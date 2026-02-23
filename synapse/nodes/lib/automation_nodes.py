from synapse.core.super_node import SuperNode
from synapse.nodes.registry import NodeRegistry
from synapse.core.types import DataType
from synapse.core.dependencies import DependencyManager
import time
import os
import platform
import psutil
from synapse.nodes.lib.provider_node import ProviderNode

# Lazy Globals
mss = None
pyautogui = None
gw = None

def ensure_mss():
    global mss
    if mss: return True
    if DependencyManager.ensure("mss"):
        import mss as _m; mss = _m; return True
    return False

def ensure_pyautogui():
    global pyautogui
    if pyautogui: return True
    if DependencyManager.ensure("pyautogui"):
        import pyautogui as _p; pyautogui = _p; return True
    return False

def ensure_gw():
    global gw
    if gw: return True
    if DependencyManager.ensure("PyGetWindow", "pygetwindow"):
        import pygetwindow as _g; gw = _g; return True
    return False
    
@NodeRegistry.register("Automation Provider", "System/Automation")
class AutomationProviderNode(ProviderNode):
    """
    Establishes an automation context for managing screens, windows, and input devices.
    Acts as a scope provider for mouse, keyboard, and screen capture operations.
    
    Inputs:
    - Flow: Trigger to enter the automation scope.
    - Target Title: Optional window title to target for automation.
    - Monitor: The numeric index of the monitor to capture (default: 1).
    
    Outputs:
    - Done: Triggered upon exiting the automation scope.
    - Provider Flow: Active while inside the automation context.
    - Provider: A handle containing target window and monitor configuration.
    """
    version = "2.1.0"

    def __init__(self, node_id, name, bridge):
        super().__init__(node_id, name, bridge)
        self.provider_type = "Automation Provider"
        self.properties["TargetTitle"] = ""
        self.properties["Monitor"] = 1
        self.define_schema()
        self.register_handlers()

    def define_schema(self):
        super().define_schema()
        self.input_schema["Target Title"] = DataType.STRING
        self.input_schema["Monitor"] = DataType.NUMBER
        # ProviderNode base handles output Flow renaming if needed, but we ensure Done is used in scope

    def start_scope(self, **kwargs):
        # Fallback with legacy support
        target_title = kwargs.get("Target Title") or self.properties.get("TargetTitle", self.properties.get("TargetTitle"))
        monitor = kwargs.get("Monitor") or self.properties.get("Monitor", self.properties.get("Monitor"))
        
        self.bridge.set(f"{self.node_id}_Target Title", target_title, self.name)
        self.bridge.set(f"{self.node_id}_Monitor", monitor, self.name)
        
        handle = {"title": target_title, "monitor": monitor}
        self.bridge.set(f"{self.node_id}_Provider", handle, self.name)
        
        return super().start_scope(**kwargs)


@NodeRegistry.register("Process Discovery", "System/Automation")
class ProcessDiscoveryNode(SuperNode):
    """
    Scans running system processes and filters them by name.
    Provides detailed information like PID, name, and owner.
    
    Inputs:
    - Flow: Trigger the discovery process.
    - Filter Name: Case-insensitive string to filter process names.
    
    Outputs:
    - Flow: Triggered after the scan is complete.
    - Processes: A list of objects containing process details (ID, Name, CPU, Memory).
    - Count: Number of matching processes found.
    """
    version = "2.1.0"

    def __init__(self, node_id, name, bridge):
        super().__init__(node_id, name, bridge)
        self.properties["Filter Name"] = ""
        self.define_schema()
        self.register_handlers()
        
    def define_schema(self):
        self.input_schema = {
            "Flow": DataType.FLOW,
            "Filter Name": DataType.STRING
        }
        self.output_schema = {
            "Flow": DataType.FLOW,
            "Process List": DataType.LIST,
            "Found": DataType.BOOLEAN
        }

    def register_handlers(self):
        self.register_handler("Flow", self.do_work)

    def do_work(self, **kwargs):
        # Fallback with legacy support
        filter_name = kwargs.get("Filter Name") or self.properties.get("Filter Name", "")
        
        if not psutil:
            self.logger.error("psutil not installed.")
            return True

        filter_term = str(filter_name or "").lower().strip()
        procs = []
        found = False
        
        try:
            for p in psutil.process_iter(['name']):
                try:
                    p_name = p.info['name']
                except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                    continue
                    
                if not p_name: continue
                
                if filter_term:
                    if filter_term in p_name.lower():
                        procs.append(p_name)
                        found = True
                else:
                    procs.append(p_name)
            
            procs = sorted(list(set(procs)))
            self.bridge.set(f"{self.node_id}_Process List", procs, self.name)
            self.bridge.set(f"{self.node_id}_Found", found, self.name)
            
            self.bridge.set(f"{self.node_id}_ActivePorts", ["Flow"], self.name)
        except Exception as e:
            self.logger.error(f"Error scanning processes: {e}")
        
        return True


@NodeRegistry.register("Window Manager", "System/Automation")
class WindowManagerNode(SuperNode):
    """
    Provides tools for finding and interacting with window handles.
    Allows focusing, checking existence, or retrieving handles from titles.
    
    Inputs:
    - Flow: Trigger the window search.
    - Target Title: The window title to search for (supports exact or partial match).
    
    Outputs:
    - Flow: Triggered after the search attempt.
    - Window Handle: The numeric HWND handle of the found window.
    - Process Id: The numeric ID of the process owning the window.
    - Bounds: List defining [Left, Top, Width, Height].
    - Title: The actual title of the found window.
    - Found: True if a matching window was located.
    """
    version = "2.1.0"

    def __init__(self, node_id, name, bridge):
        super().__init__(node_id, name, bridge)
        self.properties["Target Title"] = ""
        self.define_schema()
        self.register_handlers()

    def define_schema(self):
        self.input_schema = {
            "Flow": DataType.FLOW,
            "Target Title": DataType.STRING
        }
        self.output_schema = {
            "Flow": DataType.FLOW,
            "Window Handle": DataType.INTEGER,
            "Process Id": DataType.INTEGER,
            "Bounds": DataType.LIST,
            "Title": DataType.STRING,
            "Found": DataType.BOOLEAN
        }

    def register_handlers(self):
        self.register_handler("Flow", self.do_work)

    def do_work(self, **kwargs):
        target_title = kwargs.get("Target Title") or self.properties.get("Target Title", "")

        if not ensure_gw():
            self.logger.error("pygetwindow not installed.")
            return True

        window = None
        
        try:
            if not target_title:
                window = gw.getActiveWindow()
            else:
                matches = gw.getWindowsWithTitle(target_title)
                if matches:
                    window = matches[0]

            if window:
                bounds = [window.left, window.top, window.width, window.height]
                self.bridge.set(f"{self.node_id}_Window Handle", window._hWnd, self.name)
                
                # Try to get PID if on Windows
                pid = 0
                if platform.system() == "Windows":
                    try:
                        import ctypes
                        lpdw_process_id = ctypes.c_ulong()
                        ctypes.windll.user32.GetWindowThreadProcessId(window._hWnd, ctypes.byref(lpdw_process_id))
                        pid = lpdw_process_id.value
                    except: pass
                
                self.bridge.set(f"{self.node_id}_Process Id", pid, self.name)
                self.bridge.set(f"{self.node_id}_Bounds", bounds, self.name)
                self.bridge.set(f"{self.node_id}_Title", window.title, self.name)
                self.bridge.set(f"{self.node_id}_Found", True, self.name)
            else:
                self.bridge.set(f"{self.node_id}_Found", False, self.name)
                self.bridge.set(f"{self.node_id}_Window Handle", 0, self.name)
                self.bridge.set(f"{self.node_id}_Process Id", 0, self.name)
                self.bridge.set(f"{self.node_id}_Bounds", [0,0,0,0], self.name)
                
            self.bridge.set(f"{self.node_id}_ActivePorts", ["Flow"], self.name)

        except Exception as e:
            self.logger.error(f"Error getting window: {e}")
        
        return True


@NodeRegistry.register("Screen Capture", "System/Automation")
class ScreenCaptureNode(SuperNode):
    """
    Captures a screenshot of a specific window or a region of a monitor.
    Uses the active Automation Provider context if available.
    
    Inputs:
    - Flow: Trigger the capture.
    - Region: List/String defining the area [Left, Top, Width, Height].
    - Window Handle: Optional numeric HWND of a window to capture.
    
    Outputs:
    - Flow: Triggered after the capture is complete.
    - Image: The resulting image data (PIL Image or path).
    """
    version = "2.1.0"

    def __init__(self, node_id, name, bridge):
        super().__init__(node_id, name, bridge)
        self.properties["Monitor"] = 1
        self.define_schema()
        self.register_handlers()

    def define_schema(self):
        self.input_schema = {
            "Flow": DataType.FLOW,
            "Bounds": DataType.LIST,
            "Monitor": DataType.INTEGER
        }
        self.output_schema = {
            "Flow": DataType.FLOW,
            "Image": DataType.IMAGE
        }

    def register_handlers(self):
        self.register_handler("Flow", self.do_work)

    def do_work(self, **kwargs):
        bounds = kwargs.get("Bounds")
        monitor_input = kwargs.get("Monitor")
        
        if not ensure_mss():
            self.logger.error("mss not installed.")
            return True

        try:
            with mss.mss() as sct:
                # Fallback with legacy support
                monitor_idx = int(monitor_input or self.properties.get("Monitor", self.properties.get("Monitor", 1)))
                if monitor_idx >= len(sct.monitors):
                    monitor_idx = 1
                monitor_region = sct.monitors[monitor_idx]
                region = monitor_region
                
                if isinstance(bounds, list) and len(bounds) == 4:
                    x, y, w, h = bounds
                    if w > 0 and h > 0:
                        region = {"top": int(y), "left": int(x), "width": int(w), "height": int(h)}

                sct_img = sct.grab(region)
                from PIL import Image
                img = Image.frombytes("RGB", sct_img.size, sct_img.bgra, "raw", "BGRX")
                self.bridge.set(f"{self.node_id}_Image", img, self.name)
                
                self.bridge.set(f"{self.node_id}_ActivePorts", ["Flow"], self.name)

        except Exception as e:
            self.logger.error(f"Capture Error: {e}")
            
        return True


@NodeRegistry.register("Mouse Action", "System/Automation")
class MouseActionNode(SuperNode):
    """
    Simulates mouse movements, clicks, and scrolls.
    
    Supports absolute coordinates or relative offsets. Can target specific 
    buttons and perform double-clicks.
    
    Inputs:
    - Flow: Trigger the mouse action.
    - Action: The operation to perform ('Move', 'Click', 'Scroll', etc.).
    - X, Y: Target coordinates for the action.
    - Button: Which mouse button to use ('left', 'right', 'middle').
    - Double Click: Whether to perform a double-click (default False).
    
    Outputs:
    - Flow: Pulse triggered after the mouse action is performed.
    """
    version = "2.1.0"

    def __init__(self, node_id, name, bridge):
        super().__init__(node_id, name, bridge)
        self.properties["Action"] = "Click"
        self.properties["Button"] = "left"
        self.define_schema()
        self.register_handlers()

    def define_schema(self):
        self.input_schema = {
            "Flow": DataType.FLOW,
            "Action": DataType.MOUSEACTION,
            "X": DataType.NUMBER,
            "Y": DataType.NUMBER,
            "Button": DataType.STRING,
            "Double Click": DataType.BOOLEAN
        }
        self.output_schema = {
            "Flow": DataType.FLOW
        }

    def register_handlers(self):
        self.register_handler("Flow", self.do_work)

    def do_work(self, Action=None, Button=None, X=None, Y=None, **kwargs):
        x = X if X is not None else kwargs.get("X")
        y = Y if Y is not None else kwargs.get("Y")
        button_arg = Button if Button is not None else kwargs.get("Button")
        double_click = kwargs.get("Double Click", False)

        if not ensure_pyautogui():
            self.logger.error("pyautogui not installed.")
            return True

        pause_file = self.bridge.get("_SYSTEM_PAUSE_FILE")
        if pause_file and os.path.exists(pause_file):
            self.logger.warning("SECURITY: Action BLOCKED (System Paused).")
            return True

        # Fallback with legacy support
        action = (Action if Action is not None else self.properties.get("Action", "Click")).title()
        button = (button_arg or self.properties.get("Button", "left")).lower()
        if button not in ["left", "right", "middle"]: button = "left"
        
        try:
            if x is None or y is None:
                curr_x, curr_y = pyautogui.position()
                target_x = float(x) if x is not None else curr_x
                target_y = float(y) if y is not None else curr_y
            else:
                target_x, target_y = int(x), int(y)

            if action == "Move":
                pyautogui.moveTo(target_x, target_y, duration=0.1)
                self.logger.info(f"Moved to ({target_x}, {target_y})")
            elif action == "Click":
                clicks = 2 if double_click else 1
                pyautogui.click(target_x, target_y, clicks=clicks, interval=0.1, button=button)
                self.logger.info(f"Clicked ({target_x}, {target_y}) Btn:{button} x{clicks}")

            self.bridge.set(f"{self.node_id}_ActivePorts", ["Flow"], self.name)
        except Exception as e:
            self.logger.error(f"Mouse Error: {e}")
            
        return True


@NodeRegistry.register("Send Keys", "System/Automation")
class SendKeysNode(SuperNode):
    """
    Simulates keyboard input, supporting text blocks and special key combinations.
    Works relative to the currently focused window or the active provider target.
    
    Inputs:
    - Flow: Trigger the keyboard input.
    - Text: The string of characters to type.
    - Keys: Special keys to press (e.g., 'ENTER', 'TAB', 'CTRL+V').
    - Delay: The delay (in ms) between individual keystrokes.
    
    Outputs:
    - Flow: Triggered after the keys are sent.
    """
    version = "2.1.0"

    def __init__(self, node_id, name, bridge):
        super().__init__(node_id, name, bridge)
        self.properties["Mode"] = "Text"
        self.properties["Interval"] = 0.05
        self.properties["Text"] = ""
        self.properties["Key"] = ""
        self.define_schema()
        self.register_handlers()

    def define_schema(self):
        self.input_schema = {
            "Flow": DataType.FLOW,
            "Text": DataType.STRING,
            "Key": DataType.STRING,
            "Interval": DataType.NUMBER,
            "Mode": DataType.SENDKEYMODE
        }
        self.output_schema = {
            "Flow": DataType.FLOW
        }

    def register_handlers(self):
        self.register_handler("Flow", self.do_work)

    def do_work(self, **kwargs):
        text_arg = kwargs.get("Text")
        key_arg = kwargs.get("Key")

        text = text_arg if text_arg is not None else self.properties.get("Text", "")
        key = key_arg if key_arg is not None else self.properties.get("Key", "")

        if not ensure_pyautogui():
            self.logger.error("pyautogui not installed.")
            return True

        pause_file = self.bridge.get("_SYSTEM_PAUSE_FILE")
        if pause_file and os.path.exists(pause_file):
            self.logger.warning("SECURITY: Action BLOCKED (System Paused).")
            return True
            
        # Fallback with legacy support
        mode = kwargs.get("Mode") or self.properties.get("Mode", "Text")
        interval = float(kwargs.get("Interval") or self.properties.get("Interval", 0.05))

        try:
            if mode == "Text" or (text and not key):
                txt = text or ""
                if txt:
                    pyautogui.write(txt, interval=interval)
                    self.logger.info(f"Typed: '{txt}'")
            elif mode == "Key Press" or key:
                k = key or ""
                if k:
                    if "," in k or "+" in k:
                        keys = k.replace("+", ",").split(",")
                        keys = [x.strip() for x in keys]
                        pyautogui.hotkey(*keys)
                        self.logger.info(f"Hotkey: {keys}")
                    else:
                        pyautogui.press(k)
                        self.logger.info(f"Pressed: '{k}'")
            
            self.bridge.set(f"{self.node_id}_ActivePorts", ["Flow"], self.name)
        except Exception as e:
            self.logger.error(f"Send Keys Error: {e}")
            
        return True


@NodeRegistry.register("Color Checker", "System/Automation")
class ColorCheckerNode(SuperNode):
    """
    Samples the color of a specific pixel on the screen.
    Returns the color as both a list of RGB components and a standard hex string.
    
    Inputs:
    - Flow: Trigger the color check.
    - X, Y: Coordinates of the pixel to sample.
    
    Outputs:
    - Flow: Triggered after the check.
    - Color: The actual sampled color as an RGB list [R, G, B].
    - Hex: The actual sampled color as a hex string (e.g., "#FFFFFF").
    """
    version = "2.1.0"

    def __init__(self, node_id, name, bridge):
        super().__init__(node_id, name, bridge)
        self.define_schema()
        self.register_handlers()

    def define_schema(self):
        self.input_schema = {
            "Flow": DataType.FLOW,
            "X": DataType.NUMBER,
            "Y": DataType.NUMBER
        }
        self.output_schema = {
            "Flow": DataType.FLOW,
            "Color": DataType.LIST,
            "Hex": DataType.STRING
        }

    def register_handlers(self):
        self.register_handler("Flow", self.do_work)

    def do_work(self, **kwargs):
        x = kwargs.get("X")
        y = kwargs.get("Y")

        if not ensure_pyautogui():
            self.logger.error("pyautogui not installed.")
            return

        target_x = int(x) if x is not None else pyautogui.position()[0]
        target_y = int(y) if y is not None else pyautogui.position()[1]
             
        try:
            r, g, b = pyautogui.pixel(target_x, target_y)
            color_list = [r, g, b]
            hex_val = "#{:02x}{:02x}{:02x}".format(r, g, b).upper()
            self.bridge.set(f"{self.node_id}_Color", color_list, self.name)
            self.bridge.set(f"{self.node_id}_Hex", hex_val, self.name)
            
            self.bridge.set(f"{self.node_id}_ActivePorts", ["Flow"], self.name)
        except Exception as e:
            self.logger.error(f"Pixel Check Error: {e}")
            
        return True


@NodeRegistry.register("Window State", "System/Automation")
class WindowStateNode(SuperNode):
    """
    Modifies or retrieves the state of a window (Maximize, Minimize, Restore, Hide).
    Allows direct programmatic control over window visibility and layering.
    
    Inputs:
    - Flow: Trigger the state change.
    - Window Handle: Numeric HWND handle of the target window.
    - Action: The desired window action (Bring to Front, Minimize, Maximize, etc.).
    
    Outputs:
    - Flow: Triggered after the state update is attempted.
    """
    version = "2.1.0"

    def __init__(self, node_id, name, bridge):
        super().__init__(node_id, name, bridge)
        self.properties["Action"] = "Bring to Front"
        self.properties["Window Handle"] = 0
        self.define_schema()
        self.register_handlers()

    def define_schema(self):
        self.input_schema = {
            "Flow": DataType.FLOW,
            "Window Handle": DataType.INTEGER,
            "Action": DataType.WINSTATEACTION
        }
        self.output_schema = {
            "Flow": DataType.FLOW,
            "Error": DataType.FLOW,
            "Result": DataType.STRING
        }

    def register_handlers(self):
        self.register_handler("Flow", self.do_work)

    def do_work(self, **kwargs):
        # Fallback with legacy support
        hwnd = kwargs.get("Window Handle") or self.properties.get("Window Handle", 0)
        action = (kwargs.get("Action") or self.properties.get("Action", "Bring to Front")).lower().strip()

        if not hwnd:
            msg = "No Window Handle specified."
            self.logger.error(msg)
            self.bridge.set(f"{self.node_id}_Result", msg, self.name)
            self.bridge.set(f"{self.node_id}_ActivePorts", ["Error", "Flow"], self.name)
            return True

        if ensure_gw():
            try:
                # Find window by HWND
                found_win = None
                for win in gw.getAllWindows():
                    if hasattr(win, '_hWnd') and win._hWnd == hwnd:
                        found_win = win
                        break
                
                if not found_win:
                    msg = f"No window found with handle {hwnd}"
                    self.logger.warning(msg)
                    self.bridge.set(f"{self.node_id}_Result", msg, self.name)
                    self.bridge.set(f"{self.node_id}_ActivePorts", ["Error", "Flow"], self.name)
                    return True

                if action in ("minimize", "min"):
                    found_win.minimize()
                    msg = f"Minimized '{found_win.title}'"
                elif action in ("maximize", "max"):
                    found_win.maximize()
                    msg = f"Maximized '{found_win.title}'"
                elif action in ("restore",):
                    found_win.restore()
                    msg = f"Restored '{found_win.title}'"
                elif action in ("bring to front", "focus", "activate"):
                    try: found_win.restore()
                    except: pass
                    found_win.activate()
                    msg = f"Brought to front '{found_win.title}'"
                elif action in ("hide",):
                    if platform.system() == "Windows":
                        msg = self._hide_window_win32(found_win)
                    else:
                        found_win.minimize()
                        msg = f"Minimized '{found_win.title}' (hide not supported on {platform.system()})"
                else:
                    msg = f"Unknown action: {action}"

                self.logger.info(msg)
                self.bridge.set(f"{self.node_id}_Result", msg, self.name)
                self.bridge.set(f"{self.node_id}_ActivePorts", ["Flow"], self.name)
                return True
            except Exception as e:
                msg = f"Window control error: {e}"
                self.logger.error(msg)
                self.bridge.set(f"{self.node_id}_Result", msg, self.name)
                self.bridge.set(f"{self.node_id}_ActivePorts", ["Error", "Flow"], self.name)
                return True
        else:
            msg = "pygetwindow not installed"
            self.logger.error(msg)
            self.bridge.set(f"{self.node_id}_Result", msg, self.name)
            self.bridge.set(f"{self.node_id}_ActivePorts", ["Error", "Flow"], self.name)
            return True

    def _hide_window_win32(self, win):
        try:
            import ctypes
            SW_HIDE = 0
            hwnd = win._hWnd
            ctypes.windll.user32.ShowWindow(hwnd, SW_HIDE)
            return f"Hidden '{win.title}'"
        except Exception as e:
            return f"Hide failed: {e}"


@NodeRegistry.register("Clipboard Read", "System/Automation")
class ClipboardReadNode(SuperNode):
    """
    Retrieves the current text or image content from the system clipboard.
    
    Inputs:
    - Flow: Trigger the clipboard read.
    
    Outputs:
    - Flow: Triggered after reading.
    - Text: The text content of the clipboard (if available).
    - Image: The image content of the clipboard (if available).
    """
    version = "2.1.0"

    def __init__(self, node_id, name, bridge):
        super().__init__(node_id, name, bridge)
        self.is_native = True
        self.properties["Requested Format"] = "Text" # Text, HTML, Image Path
        self.define_schema()
        self.register_handlers()

    def define_schema(self):
        self.input_schema = {
            "Flow": DataType.FLOW,
            "Requested Format": DataType.STRING
        }
        self.output_schema = {
            "Flow": DataType.FLOW,
            "Data": DataType.ANY,
            "Detected Format": DataType.STRING
        }

    def register_handlers(self):
        self.register_handler("Flow", self.do_work)

    def do_work(self, **kwargs):
        fmt_in = kwargs.get("Requested Format") or self.properties.get("Requested Format", "Text")
        fmt = str(fmt_in).lower().strip()
        system = platform.system()
        content = ""
        try:
            if system == "Windows": content = self._pull_windows(fmt)
            elif system == "Darwin": content = self._pull_macos()
            else: content = self._pull_linux()

            detected_fmt = "Text"
            if content and content.strip().startswith("<"): detected_fmt = "HTML"
            elif content and any(content.endswith(ext) for ext in [".png", ".jpg", ".bmp", ".gif"]):
                detected_fmt = "Image Path"

            self.bridge.set(f"{self.node_id}_Data", content, self.name)
            self.bridge.set(f"{self.node_id}_Detected Format", detected_fmt, self.name)
            self.logger.info(f"Pulled from clipboard ({detected_fmt})")
            self.bridge.set(f"{self.node_id}_ActivePorts", ["Flow"], self.name)
        except Exception as e:
            self.logger.error(f"Clipboard Error: {e}")
        return True

    def _pull_windows(self, fmt):
        import ctypes
        import ctypes.wintypes
        CF_UNICODETEXT = 13
        user32 = ctypes.windll.user32
        kernel32 = ctypes.windll.kernel32
        if not user32.OpenClipboard(None): return ""
        try:
            h = user32.GetClipboardData(CF_UNICODETEXT)
            if not h: return ""
            ptr = kernel32.GlobalLock(h)
            if not ptr: return ""
            try: return ctypes.wstring_at(ptr)
            finally: kernel32.GlobalUnlock(h)
        finally: user32.CloseClipboard()

    def _pull_macos(self):
        import subprocess
        result = subprocess.run(["pbpaste"], capture_output=True, text=True, timeout=5)
        return result.stdout if result.returncode == 0 else ""

    def _pull_linux(self):
        import subprocess
        try:
            result = subprocess.run(["xclip", "-selection", "clipboard", "-o"], capture_output=True, text=True, timeout=5)
            if result.returncode == 0: return result.stdout
        except FileNotFoundError: pass
        try:
            result = subprocess.run(["xsel", "--clipboard", "--output"], capture_output=True, text=True, timeout=5)
            if result.returncode == 0: return result.stdout
        except FileNotFoundError: pass
        return ""

@NodeRegistry.register("Clipboard Write", "System/Automation")
class ClipboardWriteNode(SuperNode):
    """
    Sets the system clipboard to the provided text or image data.
    
    Inputs:
    - Flow: Trigger the clipboard write.
    - Text: The text string to place on the clipboard.
    - Image Data: image data to place on the clipboard.
    
    Outputs:
    - Flow: Triggered after writing.
    """
    version = "2.1.0"

    def __init__(self, node_id, name, bridge):
        super().__init__(node_id, name, bridge)
        self.is_native = True
        self.properties["Format"] = "Text"
        self.define_schema()
        self.register_handlers()

    def define_schema(self):
        self.input_schema = {
            "Flow": DataType.FLOW,
            "Data": DataType.ANY,
            "Format": DataType.STRING
        }
        self.output_schema = {
            "Flow": DataType.FLOW
        }

    def register_handlers(self):
        self.register_handler("Flow", self.do_work)

    def do_work(self, Data=None, Format=None, **kwargs):
        data = Data if Data is not None else ""
        fmt = (Format or self.properties.get("Format", "Text")).lower().strip()
        system = platform.system()
        try:
            text = str(data)
            if system == "Windows": self._push_windows(text, fmt)
            elif system == "Darwin": self._push_macos(text)
            else: self._push_linux(text)
            self.logger.info(f"Pushed to clipboard: {text[:30]}...")
            self.bridge.set(f"{self.node_id}_ActivePorts", ["Flow"], self.name)
        except Exception as e:
            self.logger.error(f"Clipboard Error: {e}")
        return True

    def _push_windows(self, text, fmt):
        import ctypes
        import ctypes.wintypes
        CF_UNICODETEXT = 13
        user32 = ctypes.windll.user32
        kernel32 = ctypes.windll.kernel32
        if not user32.OpenClipboard(None): raise RuntimeError("Cannot open clipboard")
        try:
            user32.EmptyClipboard()
            encoded = text.encode("utf-16-le") + b"\x00\x00"
            h = kernel32.GlobalAlloc(0x0042, len(encoded))
            ptr = kernel32.GlobalLock(h)
            ctypes.memmove(ptr, encoded, len(encoded))
            kernel32.GlobalUnlock(h)
            user32.SetClipboardData(CF_UNICODETEXT, h)
        finally: user32.CloseClipboard()

    def _push_macos(self, text):
        import subprocess
        proc = subprocess.Popen(["pbcopy"], stdin=subprocess.PIPE)
        proc.communicate(text.encode("utf-8"))

    def _push_linux(self, text):
        import subprocess
        try:
            proc = subprocess.Popen(["xclip", "-selection", "clipboard"], stdin=subprocess.PIPE)
            proc.communicate(text.encode("utf-8"))
        except FileNotFoundError:
            try:
                proc = subprocess.Popen(["xsel", "--clipboard", "--input"], stdin=subprocess.PIPE)
                proc.communicate(text.encode("utf-8"))
            except FileNotFoundError:
                raise RuntimeError("Neither xclip nor xsel found.")
