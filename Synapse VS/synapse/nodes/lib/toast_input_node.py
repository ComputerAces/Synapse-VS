from synapse.core.super_node import SuperNode
from synapse.nodes.registry import NodeRegistry
from synapse.core.constants import IS_WINDOWS
from synapse.core.types import DataType
from synapse.core.dependencies import DependencyManager

# Lazy Global
toast = None

def ensure_toast():
    global toast
    if toast: return True
    if IS_WINDOWS and DependencyManager.ensure("win11toast"):
        from win11toast import toast as _t; toast = _t; return True
    return False

@NodeRegistry.register("Toast Input", "UI/Toasts")
class ToastInputNode(SuperNode):
    """
    Displays a toast notification with a text input field (Windows only).
    Falls back to a standard PyQt input dialog on non-Windows platforms.
    
    Inputs:
    - Flow: Trigger the interactive notification.
    - Title: The title of the input request.
    - Message: Instructions or prompt text for the user.
    - Value: Default text to populate the input field.
    
    Outputs:
    - Flow: Pulse triggered after the user submits or closes the dialog.
    - Text: The string content entered by the user.
    - OnClick: Pulse triggered upon successful submission.
    """
    version = "2.1.0"

    def __init__(self, node_id, name, bridge):
        super().__init__(node_id, name, bridge)
        self.is_native = True  # Must run in main process for reliable Windows Toast integration
        self.properties["Title"] = "Synapse Input"
        self.properties["Message"] = "Please enter data:"
        self.properties["Value"] = "Type here..."
        self.define_schema()
        self.register_handlers()

    def define_schema(self):
        self.input_schema = {
            "Flow": DataType.FLOW,
            "Title": DataType.STRING,
            "Message": DataType.STRING,
            "Value": DataType.STRING
        }
        self.output_schema = {
            "Flow": DataType.FLOW,
            "Text": DataType.STRING,
            "OnClick": DataType.FLOW
        }

    def register_handlers(self):
        self.register_handler("Flow", self.do_work)

    def do_work(self, Title=None, Message=None, Value=None, **kwargs):
        # Fallback to properties if inputs aren't provided
        title_val = Title if Title is not None else self.properties.get("Title", self.properties.get("Title", ""))
        message_val = Message if Message is not None else self.properties.get("Message", self.properties.get("Message", ""))
        value_val = Value if Value is not None else self.properties.get("Value", self.properties.get("Value", ""))
        
        # Trim message to prevent Windows display failure (max 200 chars)
        if message_val and len(str(message_val)) > 200:
            message_val = str(message_val)[:197] + "..."
            
        if IS_WINDOWS and ensure_toast():
            return self._execute_windows(title_val, message_val, value_val)
        else:
            # Fallback for Linux, Mac, or Windows without win11toast
            return self._execute_fallback_gui(title_val, message_val, value_val)

    def _execute_windows(self, Title, Message, DefaultValue):
        try:
            self.logger.info("Showing Toast Input...")
            result = toast(
                Title, 
                Message,
                input=DefaultValue,
                button='Submit',
                app_id="Synapse OS",
                tag=self.node_id
            )
            
            if result:
                val = None
                if 'user_input' in result:
                    val = result['user_input']
                    if isinstance(val, dict): val = next(iter(val.values()), "")
                elif len(result) > 0:
                    val = next(iter(result.values()), None)
                
                if val is not None:
                    self.logger.info(f"Win Toast Received: {val}")
                    self.bridge.set(f"{self.node_id}_Text", str(val), self.name)
                    self.bridge.set(f"{self.node_id}_ActivePorts", ["Flow", "OnClick"], self.name)
                    return True
        except Exception as e:
            self.logger.error(f"Windows Toast Input Error: {e}")
            
        self.bridge.set(f"{self.node_id}_ActivePorts", ["Flow"], self.name)
        return True

    def _execute_fallback_gui(self, Title, Message, DefaultValue):
        """Native PyQt Fallback for non-windows or missing libs."""
        self.logger.info("Using PyQt Fallback for Input...")
        
        try:
            from PyQt6.QtWidgets import QApplication, QInputDialog, QLineEdit
            
            app = QApplication.instance()
            if not app:
                app = QApplication([])
                
            text, ok = QInputDialog.getText(None, Title, Message, QLineEdit.EchoMode.Normal, DefaultValue)
            
            if ok:
                self.logger.info(f"Input Received: {text}")
                self.bridge.set(f"{self.node_id}_Text", text, self.name)
                self.bridge.set(f"{self.node_id}_ActivePorts", ["Flow", "OnClick"], self.name)
                return True
            else:
                self.logger.info("Input Cancelled.")
                self.bridge.set(f"{self.node_id}_ActivePorts", ["Flow"], self.name)
                return True
                
        except Exception as e:
            self.logger.error(f"GUI Fallback Error: {e}")
            self.bridge.set(f"{self.node_id}_ActivePorts", [], self.name)
            return False
