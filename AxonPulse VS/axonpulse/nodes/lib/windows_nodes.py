import platform

import time

from axonpulse.core.super_node import SuperNode

from axonpulse.nodes.registry import NodeRegistry

from axonpulse.core.types import DataType

from axonpulse.core.dependencies import DependencyManager

from typing import Any, List, Dict, Optional

from axonpulse.core.types import DataType, TypeCaster

from axonpulse.nodes.decorators import axon_node

win32service = None

win32serviceutil = None

win32evtlog = None

win32evtlogutil = None

def ensure_pywin32():
    global win32service, win32serviceutil, win32evtlog, win32evtlogutil
    if win32service:
        return True
    if DependencyManager.ensure('pywin32', 'win32service'):
        import win32service as _s
        import win32serviceutil as _su
        import win32evtlog as _el
        import win32evtlogutil as _elu
        win32service = _s
        win32serviceutil = _su
        win32evtlog = _el
        win32evtlogutil = _elu
        return True
    return False

def is_windows():
    return platform.system().lower() == 'windows'

@axon_node(category="Automation/Windows", version="2.3.0", node_label="Service Controller", outputs=['Success', 'Failure', 'Previous Status'])
def ServiceControllerNode(Service_Name: str = '', Action: str = 'Start', _bridge: Any = None, _node: Any = None, _node_id: str = None, **kwargs) -> Any:
    """Manages Windows Services (Start, Stop, Restart).
Requires administrative privileges for most operations.

Inputs:
- Flow: Trigger execution.
- Service Name: The technical name of the service (e.g., 'Spooler').
- Action: The operation to perform ('Start', 'Stop', or 'Restart').

Outputs:
- Flow: Standard follow-up trigger.
- Success: Triggered if the service operation completed successfully.
- Failure: Triggered if the operation failed (e.g., service not found, access denied).
- Previous Status: The status of the service before the action was taken."""
    if not is_windows() or not ensure_pywin32():
        _node.logger.error('Windows only or pywin32 missing.')
        _bridge.set(f'{_node_id}_ActivePorts', ['Failure', 'Flow'], _node.name)
    else:
        pass
    svc_name = Service_Name if Service_Name is not None else _node.properties.get('Service Name', '')
    action = Action if Action is not None else _node.properties.get('Action', 'Start')
    if not svc_name:
        _node.logger.error('Missing Service Name.')
        _bridge.set(f'{_node_id}_ActivePorts', ['Failure', 'Flow'], _node.name)
    else:
        pass
    try:
        status_code = win32serviceutil.QueryServiceStatus(svc_name)[1]
        status_map = {win32service.SERVICE_STOPPED: 'Stopped', win32service.SERVICE_START_PENDING: 'Start Pending', win32service.SERVICE_STOP_PENDING: 'Stop Pending', win32service.SERVICE_RUNNING: 'Running', win32service.SERVICE_CONTINUE_PENDING: 'Continue Pending', win32service.SERVICE_PAUSE_PENDING: 'Pause Pending', win32service.SERVICE_PAUSED: 'Paused'}
        prev_status = status_map.get(status_code, str(status_code))
        action_lower = str(action).lower()
        if action_lower == 'start':
            if status_code == win32service.SERVICE_RUNNING:
                _node.logger.info(f'Service {svc_name} already running.')
            else:
                _node.logger.info(f'Starting {svc_name}...')
                win32serviceutil.StartService(svc_name)
        elif action_lower == 'stop':
            if status_code == win32service.SERVICE_STOPPED:
                _node.logger.info(f'Service {svc_name} already stopped.')
            else:
                _node.logger.info(f'Stopping {svc_name}...')
                win32serviceutil.StopService(svc_name)
        elif action_lower == 'restart':
            _node.logger.info(f'Restarting {svc_name}...')
            win32serviceutil.RestartService(svc_name)
        else:
            pass
        _bridge.set(f'{_node_id}_ActivePorts', ['Success', 'Flow'], _node.name)
    except Exception as e:
        _node.logger.error(f'Service Controller Error: {e}')
        _bridge.set(f'{_node_id}_ActivePorts', ['Failure', 'Flow'], _node.name)
    finally:
        pass
    return {'Previous Status': prev_status}


@axon_node(category="Automation/Windows", version="2.3.0", node_label="Event Log Watcher", outputs=['Logs'])
def EventLogWatcherNode(Log_Type: str = 'System', Limit: float = 10, _bridge: Any = None, _node: Any = None, _node_id: str = None, **kwargs) -> Any:
    """Reads recent entries from Windows Event Logs (System, Application, Security).
Allows monitoring system events and security logs for specific patterns.

Inputs:
- Flow: Trigger the log reading operation.
- Log Type: The log category to read ('System', 'Application', or 'Security').
- Limit: The maximum number of recent events to retrieve.

Outputs:
- Flow: Triggered after logs are retrieved.
- Logs: A list of event dictionaries containing time, source, ID, and message."""
    if not is_windows() or not ensure_pywin32():
        _node.logger.error('Windows only or pywin32 missing.')
        return False
    else:
        pass
    log_type = Log_Type if Log_Type is not None else _node.properties.get('Log Type', 'System')
    limit = int(Limit) if Limit is not None else int(_node.properties.get('Limit', 10))
    logs = []
    hand = None
    try:
        server = 'localhost'
        hand = win32evtlog.OpenEventLog(server, log_type)
        flags = win32evtlog.EVENTLOG_BACKWARDS_READ | win32evtlog.EVENTLOG_SEQUENTIAL_READ
        total = 0
        while total < limit:
            events = win32evtlog.ReadEventLog(hand, flags, 0)
            if not events:
                break
            else:
                pass
            for event in events:
                if total >= limit:
                    break
                else:
                    pass
                data = {'Time': str(event.TimeGenerated), 'Source': event.SourceName, 'Event ID': event.EventID, 'Type': event.EventType, 'Category': event.EventCategory}
                try:
                    msg = win32evtlogutil.SafeFormatMessage(event, log_type)
                    data['Message'] = msg
                except Exception:
                    data['Message'] = '(Format Error)'
                finally:
                    pass
                logs.append(data)
                total += 1
        _node.logger.info(f'Read {len(logs)} events from {log_type}')
    except Exception as e:
        _node.logger.error(f'Event Log Error: {e}')
    finally:
        if hand:
            win32evtlog.CloseEventLog(hand)
        else:
            pass
    return logs


@axon_node(category="Automation/Windows", version="2.3.0", node_label="Window List", outputs=['Titles', 'Handles'])
def WindowListNode(Process_ID: float = 0, _bridge: Any = None, _node: Any = None, _node_id: str = None, **kwargs) -> Any:
    """Retrieves a list of all visible window titles and handles for a specific process.
Useful for identifying target windows for automation.

Inputs:
- Flow: Trigger the window enumeration.
- Process ID: The numeric ID of the process to inspect.

Outputs:
- Flow: Triggered after listing is complete.
- Titles: List of window titles found.
- Handles: List of numeric window handles (HWND) found."""
    if not is_windows():
        _node.logger.error('Windows only.')
        return False
    else:
        pass
    import ctypes
    from ctypes import wintypes
    pid = int(Process_ID) if Process_ID is not None else int(_node.properties.get('Process ID', 0))
    if not pid:
        _node.logger.warning('No Process ID provided.')
        return False
    else:
        pass
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
                titles.append('')
            handles.append(int(hwnd))
        else:
            pass
    user32.EnumWindows(EnumWindowsProc(enum_callback), 0)
    _node.logger.info(f'Found {len(handles)} window(s) for PID {pid}')
    return {'Titles': titles, 'Handles': handles}


@axon_node(category="Automation/Windows", version="2.3.0", node_label="Window Information", outputs=['Title', 'X', 'Y', 'Width', 'Height', 'Class Name', 'Is Visible'])
def WindowInformationNode(Handle: float = 0, _bridge: Any = None, _node: Any = None, _node_id: str = None, **kwargs) -> Any:
    """Retrieves detailed properties for a specific window given its handle.
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
- Is Visible: True if the window is currently visible."""
    if not is_windows():
        _node.logger.error('Windows only.')
        return False
    else:
        pass
    import ctypes
    from ctypes import wintypes
    hwnd = int(Handle) if Handle is not None else int(_node.properties.get('Handle', _node.properties.get('Handle', 0)))
    if not hwnd:
        _node.logger.warning('No Window Handle provided.')
        return False
    else:
        pass
    user32 = ctypes.windll.user32
    length = user32.GetWindowTextLengthW(hwnd)
    buf = ctypes.create_unicode_buffer(length + 1)
    user32.GetWindowTextW(hwnd, buf, length + 1)
    title = buf.value
    rect = wintypes.RECT()
    user32.GetWindowRect(hwnd, ctypes.byref(rect))
    (x, y) = (rect.left, rect.top)
    (w, h) = (rect.right - rect.left, rect.bottom - rect.top)
    cls_buf = ctypes.create_unicode_buffer(256)
    user32.GetClassNameW(hwnd, cls_buf, 256)
    class_name = cls_buf.value
    is_visible = bool(user32.IsWindowVisible(hwnd))
    _node.logger.info(f"Window '{title}' info retrieved.")
    return {'Title': title, 'X': x, 'Y': y, 'Width': w, 'Height': h, 'Class Name': class_name, 'Is Visible': is_visible}
