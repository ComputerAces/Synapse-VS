import platform
import time
from synapse.core.super_node import SuperNode
from synapse.nodes.registry import NodeRegistry
from synapse.core.types import DataType
from synapse.core.dependencies import DependencyManager

# Lazy Globals
win32service = None
win32serviceutil = None
win32evtlog = None
win32evtlogutil = None

def ensure_pywin32():
    global win32service, win32serviceutil, win32evtlog, win32evtlogutil
    if win32service: return True
    if DependencyManager.ensure("pywin32", "win32service"):
        import win32service as _s
        import win32serviceutil as _su
        import win32evtlog as _el
        import win32evtlogutil as _elu
        win32service = _s; win32serviceutil = _su
        win32evtlog = _el; win32evtlogutil = _elu
        return True
    return False

def is_windows():
    return platform.system().lower() == "windows"

@NodeRegistry.register("Service Controller", "Automation/Windows")
class ServiceControllerNode(SuperNode):
    """
    Manages Windows Services (Start, Stop, Restart).
    Requires administrative privileges for most operations.
    
    Inputs:
    - Flow: Trigger execution.
    - Service Name: The technical name of the service (e.g., 'Spooler').
    - Action: The operation to perform ('Start', 'Stop', or 'Restart').
    
    Outputs:
    - Flow: Standard follow-up trigger.
    - Success: Triggered if the service operation completed successfully.
    - Failure: Triggered if the operation failed (e.g., service not found, access denied).
    - Previous Status: The status of the service before the action was taken.
    """
    version = "2.1.0"

    def __init__(self, node_id, name, bridge):
        super().__init__(node_id, name, bridge)
        self.is_native = True
        self.properties["Action"] = "Start" # Start, Stop, Restart
        self.properties["Service Name"] = ""
        self.define_schema()
        self.register_handlers()

    def define_schema(self):
        self.input_schema = {
            "Flow": DataType.FLOW,
            "Service Name": DataType.STRING,
            "Action": DataType.STRING
        }
        self.output_schema = {
            "Flow": DataType.FLOW,
            "Success": DataType.FLOW,
            "Failure": DataType.FLOW,
            "Previous Status": DataType.STRING
        }

    def register_handlers(self):
        self.register_handler("Flow", self.control_service)

    def control_service(self, Service_Name=None, Action=None, **kwargs):
        if not is_windows() or not ensure_pywin32():
            self.logger.error("Windows only or pywin32 missing.")
            self.bridge.set(f"{self.node_id}_ActivePorts", ["Failure", "Flow"], self.name)
            return True

        # Fallback to properties
        svc_name = Service_Name if Service_Name is not None else self.properties.get("Service Name", "")
        action = Action if Action is not None else self.properties.get("Action", "Start")
        
        if not svc_name:
            self.logger.error("Missing Service Name.")
            self.bridge.set(f"{self.node_id}_ActivePorts", ["Failure", "Flow"], self.name)
            return True

        try:
            # Check status
            status_code = win32serviceutil.QueryServiceStatus(svc_name)[1]
            status_map = {
                win32service.SERVICE_STOPPED: "Stopped",
                win32service.SERVICE_START_PENDING: "Start Pending",
                win32service.SERVICE_STOP_PENDING: "Stop Pending",
                win32service.SERVICE_RUNNING: "Running",
                win32service.SERVICE_CONTINUE_PENDING: "Continue Pending",
                win32service.SERVICE_PAUSE_PENDING: "Pause Pending",
                win32service.SERVICE_PAUSED: "Paused"
            }
            prev_status = status_map.get(status_code, str(status_code))
            self.bridge.set(f"{self.node_id}_Previous Status", prev_status, self.name)

            action_lower = str(action).lower()
            if action_lower == "start":
                if status_code == win32service.SERVICE_RUNNING:
                    self.logger.info(f"Service {svc_name} already running.")
                else:
                    self.logger.info(f"Starting {svc_name}...")
                    win32serviceutil.StartService(svc_name)
                    
            elif action_lower == "stop":
                if status_code == win32service.SERVICE_STOPPED:
                    self.logger.info(f"Service {svc_name} already stopped.")
                else:
                    self.logger.info(f"Stopping {svc_name}...")
                    win32serviceutil.StopService(svc_name)
            
            elif action_lower == "restart":
                self.logger.info(f"Restarting {svc_name}...")
                win32serviceutil.RestartService(svc_name)

            self.bridge.set(f"{self.node_id}_ActivePorts", ["Success", "Flow"], self.name)
            return True

        except Exception as e:
            self.logger.error(f"Service Controller Error: {e}")
            self.bridge.set(f"{self.node_id}_ActivePorts", ["Failure", "Flow"], self.name)
            return True

@NodeRegistry.register("Event Log Watcher", "Automation/Windows")
class EventLogWatcherNode(SuperNode):
    """
    Reads recent entries from Windows Event Logs (System, Application, Security).
    Allows monitoring system events and security logs for specific patterns.
    
    Inputs:
    - Flow: Trigger the log reading operation.
    - Log Type: The log category to read ('System', 'Application', or 'Security').
    - Limit: The maximum number of recent events to retrieve.
    
    Outputs:
    - Flow: Triggered after logs are retrieved.
    - Logs: A list of event dictionaries containing time, source, ID, and message.
    """
    version = "2.1.0"

    def __init__(self, node_id, name, bridge):
        super().__init__(node_id, name, bridge)
        self.is_native = True
        self.properties["Log Type"] = "System" # System, Application, Security
        self.properties["Limit"] = 10
        self.define_schema()
        self.register_handlers()

    def define_schema(self):
        self.input_schema = {
            "Flow": DataType.FLOW,
            "Log Type": DataType.STRING,
            "Limit": DataType.INTEGER
        }
        self.output_schema = {
            "Flow": DataType.FLOW,
            "Logs": DataType.LIST
        }

    def register_handlers(self):
        self.register_handler("Flow", self.read_logs)

    def read_logs(self, Log_Type=None, Limit=None, **kwargs):
        if not is_windows() or not ensure_pywin32():
            self.logger.error("Windows only or pywin32 missing.")
            return False

        # Fallback to properties
        log_type = Log_Type if Log_Type is not None else self.properties.get("Log Type", "System")
        limit = int(Limit) if Limit is not None else int(self.properties.get("Limit", 10))

        logs = []
        hand = None
        try:
            server = "localhost" 
            hand = win32evtlog.OpenEventLog(server, log_type)
            flags = win32evtlog.EVENTLOG_BACKWARDS_READ | win32evtlog.EVENTLOG_SEQUENTIAL_READ
            total = 0
            
            while total < limit:
                events = win32evtlog.ReadEventLog(hand, flags, 0)
                if not events: break
                
                for event in events:
                    if total >= limit: break
                    
                    data = {
                        "Time": str(event.TimeGenerated),
                        "Source": event.SourceName,
                        "Event ID": event.EventID,
                        "Type": event.EventType,
                        "Category": event.EventCategory,
                    }
                    try:
                        msg = win32evtlogutil.SafeFormatMessage(event, log_type)
                        data["Message"] = msg
                    except Exception:
                        data["Message"] = "(Format Error)"
                        
                    logs.append(data)
                    total += 1

            self.bridge.set(f"{self.node_id}_Logs", logs, self.name)
            self.logger.info(f"Read {len(logs)} events from {log_type}")
            
        except Exception as e:
            self.logger.error(f"Event Log Error: {e}")
        finally:
            if hand: win32evtlog.CloseEventLog(hand)

        return True

@NodeRegistry.register("Window List", "Automation/Windows")
class WindowListNode(SuperNode):
    """
    Retrieves a list of all visible window titles and handles for a specific process.
    Useful for identifying target windows for automation.
    
    Inputs:
    - Flow: Trigger the window enumeration.
    - Process ID: The numeric ID of the process to inspect.
    
    Outputs:
    - Flow: Triggered after listing is complete.
    - Titles: List of window titles found.
    - Handles: List of numeric window handles (HWND) found.
    """
    version = "2.1.0"

    def __init__(self, node_id, name, bridge):
        super().__init__(node_id, name, bridge)
        self.is_native = True
        self.properties["Process ID"] = 0
        self.define_schema()
        self.register_handlers()

    def define_schema(self):
        self.input_schema = {
            "Flow": DataType.FLOW,
            "Process ID": DataType.INTEGER
        }
        self.output_schema = {
            "Flow": DataType.FLOW,
            "Titles": DataType.LIST,
            "Handles": DataType.LIST
        }

    def register_handlers(self):
        self.register_handler("Flow", self.list_windows)

    def list_windows(self, Process_ID=None, **kwargs):
        if not is_windows():
            self.logger.error("Windows only.")
            return False

        import ctypes
        from ctypes import wintypes

        # Fallback to properties
        pid = int(Process_ID) if Process_ID is not None else int(self.properties.get("Process ID", 0))
        if not pid:
            self.logger.warning("No Process ID provided.")
            return False

        user32 = ctypes.windll.user32
        EnumWindowsProc = ctypes.WINFUNCTYPE(wintypes.BOOL, wintypes.HWND, wintypes.LPARAM)
        
        titles = []
        handles = []
        
        def enum_callback(hwnd, lparam):
            window_pid = wintypes.DWORD()
            user32.GetWindowThreadProcessId(hwnd, ctypes.byref(window_pid))
            
            if window_pid.value == pid:
                length = user32.GetWindowTextLengthW(hwnd)
                if length > 0:
                    buf = ctypes.create_unicode_buffer(length + 1)
                    user32.GetWindowTextW(hwnd, buf, length + 1)
                    titles.append(buf.value)
                else:
                    titles.append("")
                handles.append(int(hwnd))
            return True

        user32.EnumWindows(EnumWindowsProc(enum_callback), 0)

        self.bridge.set(f"{self.node_id}_Titles", titles, self.name)
        self.bridge.set(f"{self.node_id}_Handles", handles, self.name)
        self.logger.info(f"Found {len(handles)} window(s) for PID {pid}")
        return True

@NodeRegistry.register("Window Information", "Automation/Windows")
class WindowInformationNode(SuperNode):
    """
    Retrieves detailed properties for a specific window given its handle.
    Includes title, dimensions, position, class name, and visibility status.
    
    Inputs:
    - Flow: Trigger the information retrieval.
    - Handle: The numeric handle (HWND) of the target window.
    
    Outputs:
    - Flow: Triggered after information is gathered.
    - Title: The window's title text.
    - X, Y: Coordinates of the window's top-left corner.
    - Width, Height: Dimensions of the window.
    - Class Name: The internal Windows class name for the window.
    - Is Visible: True if the window is currently visible.
    """
    version = "2.1.0"

    def __init__(self, node_id, name, bridge):
        super().__init__(node_id, name, bridge)
        self.is_native = True
        self.properties["Handle"] = 0
        self.define_schema()
        self.register_handlers()

    def define_schema(self):
        self.input_schema = {
            "Flow": DataType.FLOW,
            "Handle": DataType.INTEGER
        }
        self.output_schema = {
            "Flow": DataType.FLOW,
            "Title": DataType.STRING,
            "X": DataType.INTEGER,
            "Y": DataType.INTEGER,
            "Width": DataType.INTEGER,
            "Height": DataType.INTEGER,
            "Class Name": DataType.STRING,
            "Is Visible": DataType.BOOLEAN
        }

    def register_handlers(self):
        self.register_handler("Flow", self.get_info)

    def get_info(self, Handle=None, **kwargs):
        if not is_windows():
            self.logger.error("Windows only.")
            return False

        import ctypes
        from ctypes import wintypes

        # Fallback to properties
        hwnd = int(Handle) if Handle is not None else int(self.properties.get("Handle", self.properties.get("Handle", 0)))
        if not hwnd:
            self.logger.warning("No Window Handle provided.")
            return False

        user32 = ctypes.windll.user32

        # Title
        length = user32.GetWindowTextLengthW(hwnd)
        buf = ctypes.create_unicode_buffer(length + 1)
        user32.GetWindowTextW(hwnd, buf, length + 1)
        title = buf.value

        # Rect
        rect = wintypes.RECT()
        user32.GetWindowRect(hwnd, ctypes.byref(rect))
        x, y = rect.left, rect.top
        w, h = rect.right - rect.left, rect.bottom - rect.top

        # Class Name
        cls_buf = ctypes.create_unicode_buffer(256)
        user32.GetClassNameW(hwnd, cls_buf, 256)
        class_name = cls_buf.value

        # Visibility
        is_visible = bool(user32.IsWindowVisible(hwnd))

        self.bridge.set(f"{self.node_id}_Title", title, self.name)
        self.bridge.set(f"{self.node_id}_X", x, self.name)
        self.bridge.set(f"{self.node_id}_Y", y, self.name)
        self.bridge.set(f"{self.node_id}_Width", w, self.name)
        self.bridge.set(f"{self.node_id}_Height", h, self.name)
        self.bridge.set(f"{self.node_id}_Class Name", class_name, self.name)
        self.bridge.set(f"{self.node_id}_Is Visible", is_visible, self.name)

        self.logger.info(f"Window '{title}' info retrieved.")
        return True
