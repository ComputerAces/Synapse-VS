import os
import uuid
from typing import Optional, Any
from synapse.core.node import BaseNode
from synapse.nodes.lib.provider_node import ProviderNode
from synapse.nodes.registry import NodeRegistry
from synapse.core.types import DataType
from synapse.core.dependencies import DependencyManager

from enum import Enum

class BrowserType(Enum):
    CHROMIUM = "chromium"
    FIREFOX = "firefox"
    WEBKIT = "webkit"

# [NEW] Import Magic Engine
try:
    from .magic import MagicFinder
except ImportError:
    MagicFinder = None

# Lazy Globals
sync_playwright = None

def ensure_playwright():
    global sync_playwright
    if sync_playwright: return True
    if DependencyManager.ensure("playwright"):
        from playwright.sync_api import sync_playwright as _s
        sync_playwright = _s
        return True
    return False

class BrowserHandle:
    def __init__(self, playwright, browser, context, page):
        self.id = f"browser_{uuid.uuid4().hex[:8]}"
        self.playwright = playwright
        self.browser = browser
        self.context = context
        self.pages = [page]
        self.active_page_index = 0
        self.closed = False
        
        # [NEW] Magic Engine Attachment
        self._magic_engines = {} # page_id -> MagicFinder

    @property
    def page(self):
        """Returns the currently active page."""
        if not self.pages:
            return None
        # Ensure index is valid
        if self.active_page_index >= len(self.pages):
            self.active_page_index = len(self.pages) - 1
        return self.pages[self.active_page_index]

    def switch_page(self, index):
        """Switches the active page by index."""
        if 0 <= index < len(self.pages):
            self.active_page_index = index
            return True
        return False

    @property
    def magic(self) -> Optional[Any]:
        """Provides access to the Magic Finder for the active page."""
        if not self.page: return None
        page_id = id(self.page)
        if page_id not in self._magic_engines:
            if MagicFinder:
                self._magic_engines[page_id] = MagicFinder(self.page)
            else:
                return None
        return self._magic_engines[page_id]

    def magic_find(self, target: str, payload: Any = None) -> Any:
        """Helper to invoke magic_find on the active page."""
        engine = self.magic
        if engine:
            return engine.find(target, payload)
        return None

    def close(self):
        if self.closed: return
        try:
            for p in self.pages:
                try: p.close()
                except: pass
            self.context.close()
            if self.browser: self.browser.close()
            self.playwright.stop()
        except: pass
        self.closed = True

@NodeRegistry.register("Browser Provider", "Browser")
class BrowserProviderNode(ProviderNode):
    """
    Launches and manages a headless or windowed web browser instance (Chromium, Firefox, WebKit).
    Establishes a context for all subsequent browser-based actions.
    
    Inputs:
    - Flow: Trigger to launch the browser and enter the scope.
    - App ID: Optional unique identifier for the browser session.
    - Browser Type: The browser engine to use (Chromium, Firefox, WebKit).
    - Headless: If True, runs the browser without a visible window.
    - Devtools: If True, opens the browser with developer tools enabled.
    
    Outputs:
    - Done: Triggered upon closing the browser and exiting the scope.
    - Provider Flow: Active while the browser is running.
    """
    version = "2.1.0"

    def __init__(self, node_id, name, bridge):
        super().__init__(node_id, name, bridge)
        self.is_native = True
        self.provider_type = "Browser Provider"
        self.properties["Browser Type"] = BrowserType.CHROMIUM.value
        self.properties["Headless"] = False
        self.properties["Devtools"] = False
        self.properties["User Profile Path"] = ""
        self.properties["Executable Path"] = ""
        self._current_kwargs = {}
        self.browser = None
        self.context = None
        self.page = None
        self.handle = None
        self.app_id = None
        self._playwright_instance = None

    def define_schema(self):
        super().define_schema()
        self.input_schema.update({
            "App ID": DataType.STRING,
            "Browser Type": DataType.STRING,
            "Headless": DataType.BOOLEAN,
            "Devtools": DataType.BOOLEAN,
            "User Profile Path": DataType.STRING,
            "Executable Path": DataType.STRING
        })

    def start_scope(self, **kwargs):
        self._current_kwargs = kwargs
        self.app_id = kwargs.get("App ID")
        if not ensure_playwright(): return
        
        # [THREAD AFFINITY FIX] Launch browser in the EXECUTION thread
        # This ensures all subsequent calls from action nodes (on this thread) work.
        self._initialize_browser_resources()
        
        return super().start_scope(**kwargs)


    def register_provider_context(self):
        """
        Reports Provider Identity. Resources are handled in start_scope for thread affinity.
        """
        return self.provider_type

    def _initialize_browser_resources(self):
        """
        Launches Browser and registers Handle in the local object store.
        MUST be called from the main execution thread.
        """
        # 1. Setup Playwright
        if not hasattr(self, "_playwright_instance") or not self._playwright_instance:
             if sync_playwright is None:
                 self.logger.error("sync_playwright is None! Initialization failed.")
                 return
             self._playwright_instance = sync_playwright().start()
        
        # 2. Configure Launch
        kwargs = self._current_kwargs
        b_type = kwargs.get("Browser Type") or self.properties.get("Browser Type", "chromium")
        if hasattr(b_type, "value"): b_type = b_type.value
        b_type = b_type.lower()
        
        headless = kwargs.get("Headless") if kwargs.get("Headless") is not None else self.properties.get("Headless", True)
        devtools = kwargs.get("Devtools") if kwargs.get("Devtools") is not None else self.properties.get("Devtools", False)
        
        args = []
        if devtools:
            args.append("--auto-open-devtools-for-tabs")
            headless = False # Devtools requires a visible window
            
        # 3. Launch Strategy (Persistent vs Standard)
        user_data_path = kwargs.get("User Profile Path") or self.properties.get("User Profile Path")
        exec_path = kwargs.get("Executable Path") or self.properties.get("Executable Path")
        if not exec_path: exec_path = None # Ensure None if empty string
        
        browser_cls = getattr(self._playwright_instance, b_type, self._playwright_instance.chromium)
        
        # [SMART PROFILE RESOLUTION]
        # Detect if user pointed to a specific profile subfolder (Profile 1, Default, etc.)
        profile_directory = None
        current_user_data_dir = user_data_path
        
        if user_data_path:
            norm_path = os.path.normpath(user_data_path)
            basename = os.path.basename(norm_path)
            # Chrome/Edge profiles usually follow 'Profile \d+' or 'Default' naming
            if basename.startswith("Profile ") or basename == "Default":
                profile_directory = basename
                current_user_data_dir = os.path.dirname(norm_path)
                self.logger.info(f"Detected profile subfolder: {profile_directory}. Adjusted root to: {current_user_data_dir}")
        
        # Determine Channel
        channel = None
        if b_type == "chromium":
            # If path suggests Chrome or Edge, set channel
            if "chrome" in (user_data_path or "").lower() or "chrome" in (exec_path or "").lower():
                channel = "chrome"
            elif "edge" in (user_data_path or "").lower() or "edge" in (exec_path or "").lower():
                channel = "msedge"

        if current_user_data_dir:
            # [AUTO-CREATE] Ensure the directory exists before Playwright tries to use it.
            if not os.path.exists(current_user_data_dir):
                self.logger.info(f"Creating missing User Profile Path directory: {current_user_data_dir}")
                try:
                    os.makedirs(current_user_data_dir, exist_ok=True)
                except Exception as e:
                    self.logger.error(f"Failed to create User Profile Path: {e}")
                    raise RuntimeError(f"Cannot create profile directory '{current_user_data_dir}': {e}")

            self.logger.info(f"Launching persistent browser context from: {current_user_data_dir} (Channel: {channel})")
            
            launch_kwargs = {
                "user_data_dir": current_user_data_dir,
                "headless": headless,
                "args": args,
                "channel": channel
            }
            if exec_path: launch_kwargs["executable_path"] = exec_path
            
            # Add profile dir arg if detected
            if profile_directory:
                args.append(f"--profile-directory={profile_directory}")
            
            try:
                self.context = browser_cls.launch_persistent_context(**launch_kwargs)
            except Exception as e:
                err_str = str(e)
                if "Target page, context or browser has been closed" in err_str or "locked" in err_str.lower():
                    self.logger.error(f"Failed to launch browser with profile '{current_user_data_dir}'. Ensure no other Chrome/Edge instances are running and using this profile. ({err_str})")
                else:
                    self.logger.error(f"Failed to launch persistent context: {e}")
                raise RuntimeError(f"Browser profile locked or failed to launch: {e}")
            
            self.browser = None
        else:
            launch_kwargs = {"headless": headless, "args": args, "channel": channel}
            if exec_path: launch_kwargs["executable_path"] = exec_path
            
            self.browser = browser_cls.launch(**launch_kwargs)
            self.context = self.browser.new_context()

        # 4. Create Initial Page
        if self.context.pages:
            self.page = self.context.pages[0]
        else:
            self.page = self.context.new_page()
        
        # 5. Register Handle [LOCAL OBJECT FIX]
        self.handle = BrowserHandle(self._playwright_instance, self.browser, self.context, self.page)
        self.bridge.set_object(f"{self.node_id}_Handle", self.handle)
        
        # Report ID to bridge for discovery
        self.bridge.set(f"{self.node_id}_Handle_ID", self.handle.id, self.name)
        
    def cleanup_provider_context(self):
        """
        Closes Browser and cleans up.
        """
        if hasattr(self, "handle") and self.handle:
            self.handle.close()
            self.handle = None
            
        super().cleanup_provider_context()
