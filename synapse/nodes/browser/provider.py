import os
import uuid
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
        self.page = page
        self.closed = False

    def close(self):
        if self.closed: return
        try:
            self.page.close()
            self.context.close()
            self.browser.close()
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
        self._current_kwargs = {}

    def define_schema(self):
        super().define_schema()
        self.input_schema.update({
            "App ID": DataType.STRING,
            "Browser Type": DataType.STRING,
            "Headless": DataType.BOOLEAN,
            "Devtools": DataType.BOOLEAN
        })

    def start_scope(self, **kwargs):
        if not ensure_playwright(): return
        self._current_kwargs = kwargs
        self.app_id = kwargs.get("App ID")
        return super().start_scope(**kwargs)


    def register_provider_context(self):
        """
        Launches Browser and registers Handle.
        """
        super().register_provider_context()
        
        # 1. Setup Playwright
        if not hasattr(self, "_playwright_instance") or not self._playwright_instance:
             self._playwright_instance = sync_playwright().start()
        
        # 2. Configure Launch
        kwargs = self._current_kwargs
        b_type = kwargs.get("Browser Type") or self.properties.get("Browser Type", "chromium")
        if hasattr(b_type, "value"): b_type = b_type.value
        b_type = b_type.lower()
        
        headless = kwargs.get("Headless") if kwargs.get("Headless") is not None else self.properties.get("Headless", True)
        devtools = kwargs.get("Devtools") if kwargs.get("Devtools") is not None else self.properties.get("Devtools", False)
        
        args = []
        if self.app_id:
             # Basic support for app_id as user data dir suffix if needed
             pass

        # 3. Launch Browser
        browser_cls = getattr(self._playwright_instance, b_type, self._playwright_instance.chromium)
        self.browser = browser_cls.launch(headless=headless, devtools=devtools, args=args)
        
        # 4. Create Context & Page
        self.context = self.browser.new_context()
        self.page = self.context.new_page()
        
        # 5. Register Handle
        self.handle = BrowserHandle(self._playwright_instance, self.browser, self.context, self.page)
        self.bridge.set(f"{self.node_id}_Handle", self.handle, self.name)
        
    def cleanup_provider_context(self):
        """
        Closes Browser and cleans up.
        """
        if hasattr(self, "handle") and self.handle:
            self.handle.close()
            self.handle = None
            
        super().cleanup_provider_context()
