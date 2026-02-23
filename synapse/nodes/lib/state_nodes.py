from synapse.core.super_node import SuperNode
from synapse.nodes.registry import NodeRegistry
from synapse.core.types import DataType
from synapse.core.dependencies import DependencyManager
import time
import os
import platform
import ctypes

# Lazy Global
pyautogui = None

def ensure_pyautogui():
    global pyautogui
    if pyautogui: return True
    if DependencyManager.ensure("pyautogui"):
        import pyautogui as _p; pyautogui = _p; return True
    return False

class USER_INPUT_INFO(ctypes.Structure):
    """Win32 structure for capturing input timing."""
    _fields_ = [
        ("cbSize", ctypes.c_uint),
        ("dwTime", ctypes.c_uint),
    ]

@NodeRegistry.register("User Activity", "System/State")
class UserActivityNode(SuperNode):
    """
    Monitors system-wide user activity to detect idle states.
    Uses native OS hooks (Windows) or mouse tracking fallback to distinguish 
    between active and idle sessions.
    
    Inputs:
    - Flow: Check for user activity.
    - Timeout MS: The idle duration threshold in milliseconds (default: 5000).
    
    Outputs:
    - Active Flow: Pulse triggered if activity was detected within the timeout.
    - Idle Flow: Pulse triggered if the system has been idle longer than the timeout.
    """
    version = "2.1.0"

    def __init__(self, node_id, name, bridge):
        super().__init__(node_id, name, bridge)
        self._last_mouse_pos = None
        self._last_activity_time = time.time()
        self._is_windows = platform.system() == "Windows"
        
        self.define_schema()
        self.register_handler("Flow", self.do_work)

    def define_schema(self):
        self.input_schema = {
            "Flow": DataType.FLOW,
            "Timeout MS": DataType.NUMBER
        }
        self.output_schema = {
            "Active Flow": DataType.FLOW,
            "Idle Flow": DataType.FLOW
        }

    def _get_idle_time_ms(self):
        """Returns system idle time in milliseconds."""
        if self._is_windows:
            try:
                last_input_info = USER_INPUT_INFO()
                last_input_info.cbSize = ctypes.sizeof(USER_INPUT_INFO)
                ctypes.windll.user32.GetLastInputInfo(ctypes.byref(last_input_info))
                
                millis = ctypes.windll.kernel32.GetTickCount() - last_input_info.dwTime
                return millis
            except Exception:
                pass
        
        # Fallback: Check mouse position change via pyautogui (if available)
        # Note: This only works if this node is called frequently.
        # It's less accurate than OS level hook.
        if ensure_pyautogui():
            curr_pos = pyautogui.position()
            if self._last_mouse_pos != curr_pos:
                self._last_mouse_pos = curr_pos
                self._last_activity_time = time.time()
                return 0
            else:
                return (time.time() - self._last_activity_time) * 1000
        return 0 # Assume active if we can't check

    def do_work(self, Timeout_MS=5000, **kwargs):
        idle_ms = self._get_idle_time_ms()
        
        timeout = float(Timeout_MS) if Timeout_MS is not None else 5000.0
        
        if idle_ms < timeout:
            # Active
            self.bridge.set(f"{self.node_id}_Idle Time", idle_ms, self.name)
            self.bridge.set(f"{self.node_id}_ActivePorts", ["Active Flow"], self.name)
        else:
            # Idle
            self.logger.info(f"User Idle for {idle_ms}ms (Timeout: {timeout}ms)")
            self.bridge.set(f"{self.node_id}_ActivePorts", ["Idle Flow"], self.name)
