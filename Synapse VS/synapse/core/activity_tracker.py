"""
ActivityTracker — Global system-wide idle time monitor.

Module-level singleton that auto-starts on first access. Uses Win32 
GetCursorPos and GetLastInputInfo (system-wide OS APIs), so every 
process independently reads the same system state. No bridge/IPC needed.

Usage from any node in any process:
    from synapse.core.activity_tracker import get_tracker
    tracker = get_tracker()
    print(tracker.mouse_idle_ms, tracker.keyboard_idle_ms)
"""
import time
import threading
import platform
import ctypes

class _LASTINPUTINFO(ctypes.Structure):
    _fields_ = [("cbSize", ctypes.c_uint), ("dwTime", ctypes.c_uint)]

class _POINT(ctypes.Structure):
    _fields_ = [("x", ctypes.c_long), ("y", ctypes.c_long)]


class ActivityTracker:
    """Tracks mouse and keyboard idle as simple counters (ms)."""

    def __init__(self):
        self._is_windows = platform.system() == "Windows"
        self._last_mouse_pos = self._get_cursor_pos()
        self._running = False
        self._thread = None
        self._poll_ms = 250
        
        # Seed counters from current OS idle state (not zero)
        initial_idle = float(self._get_system_idle_ms())
        self._mouse_idle_ms = initial_idle
        self._keyboard_idle_ms = initial_idle

    def start(self):
        if self._running:
            return
        self._running = True
        self._thread = threading.Thread(target=self._poll_loop, daemon=True, name="ActivityTracker")
        self._thread.start()

    def stop(self):
        self._running = False
        if self._thread:
            self._thread.join(timeout=1.0)
            self._thread = None

    @property
    def mouse_idle_ms(self):
        return self._mouse_idle_ms

    @property
    def keyboard_idle_ms(self):
        return self._keyboard_idle_ms

    def _get_cursor_pos(self):
        if self._is_windows:
            try:
                pt = _POINT()
                ctypes.windll.user32.GetCursorPos(ctypes.byref(pt))
                return (pt.x, pt.y)
            except Exception:
                pass
        return (0, 0)

    def _get_system_idle_ms(self):
        if self._is_windows:
            try:
                lii = _LASTINPUTINFO()
                lii.cbSize = ctypes.sizeof(_LASTINPUTINFO)
                ctypes.windll.user32.GetLastInputInfo(ctypes.byref(lii))
                return ctypes.windll.kernel32.GetTickCount() - lii.dwTime
            except Exception:
                pass
        return 0

    def _poll_loop(self):
        while self._running:
            cursor = self._get_cursor_pos()
            system_idle = self._get_system_idle_ms()

            # Mouse: reset if cursor moved, otherwise count up
            if cursor != self._last_mouse_pos:
                self._last_mouse_pos = cursor
                self._mouse_idle_ms = 0.0
            else:
                self._mouse_idle_ms += self._poll_ms

            # Keyboard: if system active but mouse didn't move → keyboard was used
            if system_idle < self._poll_ms and self._mouse_idle_ms > self._poll_ms:
                self._keyboard_idle_ms = 0.0
            else:
                self._keyboard_idle_ms += self._poll_ms

            time.sleep(self._poll_ms / 1000.0)


# ── Module-level singleton (auto-starts on first access) ──
_instance = None
_lock = threading.Lock()

def get_tracker():
    """Returns the global ActivityTracker, starting it if needed."""
    global _instance
    if _instance is None:
        with _lock:
            if _instance is None:
                _instance = ActivityTracker()
                _instance.start()
    return _instance
