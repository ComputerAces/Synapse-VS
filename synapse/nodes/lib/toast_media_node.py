from synapse.core.super_node import SuperNode
from synapse.nodes.registry import NodeRegistry
from synapse.core.constants import IS_WINDOWS
from synapse.core.types import DataType
from synapse.core.dependencies import DependencyManager
import threading
import os

# Lazy Globals
toast = None
DesktopNotifier = None

def ensure_toast():
    global toast, DesktopNotifier
    if IS_WINDOWS:
        if toast: return True
        if DependencyManager.ensure("win11toast"):
            from win11toast import toast as _t; toast = _t; return True
    else:
        if DesktopNotifier: return True
        if DependencyManager.ensure("desktop-notifier", "desktop_notifier"):
            from desktop_notifier import DesktopNotifier as _D; DesktopNotifier = _D; return True
    return False

@NodeRegistry.register("Toast Media", "UI/Toasts")
class ToastMediaNode(SuperNode):
    """
    Displays a system-native toast notification with an attached image.
    Ideal for alerts that require visual context, such as security 
    camera triggers or status updates with icons.
    
    Inputs:
    - Flow: Trigger the notification.
    - Title: The bold header text of the toast.
    - Message: The main body text of the notification.
    - Path: The absolute or relative path to the image file to display.
    
    Outputs:
    - Flow: Pulse triggered after the toast is sent.
    - OnClick: Pulse triggered if the user clicks on the notification.
    """
    version = "2.1.0"

    def __init__(self, node_id, name, bridge):
        super().__init__(node_id, name, bridge)
        self.properties["Title"] = "Synapse Media"
        self.properties["Message"] = "Check this out!"
        self.properties["Path"] = ""
        self.define_schema()
        self.register_handlers()

    def define_schema(self):
        self.input_schema = {
            "Flow": DataType.FLOW,
            "Title": DataType.STRING,
            "Message": DataType.STRING,
            "Path": DataType.STRING
        }
        self.output_schema = {
            "Flow": DataType.FLOW,
            "OnClick": DataType.FLOW
        }

    def register_handlers(self):
        self.register_handler("Flow", self.do_work)

    def do_work(self, Title=None, Message=None, Path=None, **kwargs):
        # Fallback to properties if inputs aren't provided
        title_val = Title if Title is not None else self.properties.get("Title", self.properties.get("Title", ""))
        message_val = Message if Message is not None else self.properties.get("Message", self.properties.get("Message", ""))
        path_val = Path if Path is not None else self.properties.get("Path", self.properties.get("Path", ""))
        
        # Trim message to prevent Windows display failure (max 200 chars)
        if message_val and len(str(message_val)) > 200:
            message_val = str(message_val)[:197] + "..."

        # Resolve Path
        abs_path = path_val
        if path_val and not os.path.isabs(path_val):
            abs_path = os.path.abspath(path_val)

        ensure_toast()
        if IS_WINDOWS:
            return self._execute_windows(title_val, message_val, abs_path)
        else:
            return self._execute_cross_platform(title_val, message_val, abs_path)

    def _execute_windows(self, Title, Message, Path):
        if not toast:
            self.logger.error("win11toast not installed.")
            return False
            
        clicked_event = threading.Event()
        def on_click(args):
            clicked_event.set()

        try:
            params = {
                'title': Title,
                'body': Message,
                'on_click': on_click,
                'app_id': "Synapse OS",
                'tag': self.node_id
            }
            if Path and os.path.exists(Path):
                params['image'] = Path
                
            toast(**params)
            
            if clicked_event.wait(timeout=15.0):
                self.bridge.set(f"{self.node_id}_ActivePorts", ["Flow", "OnClick"], self.name)
                return True
        except Exception as e:
            self.logger.error(f"Windows Toast Media Error: {e}")
            
        self.bridge.set(f"{self.node_id}_ActivePorts", ["Flow"], self.name)
        return True

    def _execute_cross_platform(self, Title, Message, Path):
        if not DesktopNotifier:
            self.logger.error("desktop-notifier not installed.")
            return False
            
        clicked_event = threading.Event()
        
        async def notify():
            notifier = DesktopNotifier(app_name="Synapse OS")
            await notifier.send(
                title=Title,
                message=Message,
                on_clicked=lambda: clicked_event.set()
            )

        try:
            import asyncio
            loop = asyncio.new_event_loop()
            threading.Thread(target=loop.run_forever, daemon=True).start()
            asyncio.run_coroutine_threadsafe(notify(), loop)
            
            if clicked_event.wait(timeout=15.0):
                self.bridge.set(f"{self.node_id}_ActivePorts", ["Flow", "OnClick"], self.name)
                return True
        except Exception as e:
            self.logger.error(f"Cross-platform Notification Media Error: {e}")

        self.bridge.set(f"{self.node_id}_ActivePorts", ["Flow"], self.name)
        return True
