
import sys
import json
import os
import time
from synapse.core.super_node import SuperNode
from synapse.nodes.registry import NodeRegistry
from synapse.core.types import DataType

# Check GUI availability
try:
    from PyQt6.QtWidgets import QApplication
    HAS_GUI = True
except ImportError:
    HAS_GUI = False

# Lazy Import CLI renderer
try:
    from synapse.core.cli_forms import render_form_cli
except ImportError:
    render_form_cli = None

@NodeRegistry.register("Custom Form", "UI")
class CustomFormNode(SuperNode):
    """
    Renders a dynamic user interface form based on a matching schema.
    Supports both GUI (via Bridge) and CLI rendering modes.
    
    Inputs:
    - Flow: Trigger the form display.
    - Title: The window or header title for the form.
    - Blocking: If True, execution waits until the user submits the form.
    - Schema: A list of field definitions (label, type, default).
    
    Outputs:
    - Flow: Triggered after form submission (or immediately if non-blocking).
    - Form Data: A dictionary containing the user's input values.
    """
    version = "2.1.0"

    def __init__(self, node_id, name, bridge):
        super().__init__(node_id, name, bridge)
        self.properties["Title"] = "Data Input"
        self.properties["Blocking"] = True
        self.properties["Schema"] = [
            {"label": "Name", "type": "text", "default": ""},
            {"label": "Agree", "type": "boolean", "default": False}
        ]
        self.define_schema()
        self.register_handlers()

    def define_schema(self):
        self.input_schema = {
            "Flow": DataType.FLOW,
            "Title": DataType.STRING,
            "Blocking": DataType.BOOLEAN,
            "Schema": DataType.LIST
        }
        self.output_schema = {
            "Flow": DataType.FLOW,
            "Form Data": DataType.DICT
        }

    def register_handlers(self):
        self.register_handler("Flow", self.do_work)

    def do_work(self, Title=None, Blocking=None, Schema=None, **kwargs):
        title = Title if Title is not None else kwargs.get("Title") or self.properties.get("Title", "Data Input")
        schema = Schema if Schema is not None else kwargs.get("Schema") or self.properties.get("Schema", [])
        blocking = Blocking if Blocking is not None else kwargs.get("Blocking") if kwargs.get("Blocking") is not None else self.properties.get("Blocking", True)
        
        is_headless = False
        if HAS_GUI:
            app = QApplication.instance()
            if not app:
                is_headless = True
        else:
            is_headless = True

        data = {}

        # 1. Automation Mode check
        safe_name = title.lower().replace(" ", "_") + ".syf"
        if os.path.exists(safe_name):
            self.logger.info(f"Automation: Found {safe_name}. Loading answers.")
            try:
                with open(safe_name, 'r') as f:
                    data = json.load(f)
                self.bridge.set(f"{self.node_id}_Form Data", data, self.name)
                self.bridge.set(f"{self.node_id}_ActivePorts", ["Flow"], self.name)
                return True
            except Exception as e:
                self.logger.error(f"Error reading {safe_name}: {e}")

        # 2. Interactive Mode
        if is_headless:
            if render_form_cli:
                self.logger.info("Rendering CLI Form...")
                data = render_form_cli(title, schema)
            else:
                self.logger.error("CLI Forms module missing. Using defaults.")
                data = {f["label"]: f.get("default") for f in schema}
        else:
            # GUI Mode via Bridge Request
            self.logger.info("Requesting GUI Form via Bridge...")
            req_id = f"FORM_{self.node_id}_{time.time_ns()}"
            
            payload = {
                "id": req_id,
                "title": title,
                "schema": schema
            }
            
            self.bridge.set("SHOW_FORM", payload, self.name)
            
            if not blocking:
                self.bridge.set(f"{self.node_id}_Form Data", {}, self.name)
                self.bridge.set(f"{self.node_id}_ActivePorts", ["Flow"], self.name)
                return True

            resp_key = f"FORM_RESPONSE_{req_id}"
            max_retries = 600 # 60 seconds
            
            for _ in range(max_retries):
                resp = self.bridge.get(resp_key)
                if resp:
                    data = resp
                    self.bridge.delete(resp_key)
                    break
                time.sleep(0.1)
            
            if not data:
                self.logger.warning("Timed out waiting for GUI Form.")
                data = {}

        self.bridge.set(f"{self.node_id}_Form Data", data, self.name)
        self.bridge.set(f"{self.node_id}_ActivePorts", ["Flow"], self.name)
        return True

@NodeRegistry.register("Message Box", "UI")
class MessageBoxNode(SuperNode):
    """
    Displays a modal message box to the user.
    
    Supports various types (Infor, Warning, Error) and button configurations 
    (OK, Yes/No, OK/Cancel). Can block execution until the user interacts 
    with the dialog.
    
    Inputs:
    - Flow: Trigger the display.
    - Title: The title of the message box window.
    - Message: The text content to display.
    - Type: The style of the box ('info', 'warning', 'error').
    - Buttons: The button layout ('ok', 'yes_no', 'ok_cancel').
    - Blocking: Whether to wait for user input (default True).
    
    Outputs:
    - Flow: Pulse triggered after closure (or immediately if non-blocking).
    - Result: The button clicked by the user (e.g., 'ok', 'yes', 'no').
    """
    version = "2.1.0"

    def __init__(self, node_id, name, bridge):
        super().__init__(node_id, name, bridge)
        self.properties["Title"] = "Message"
        self.properties["Message"] = "Hello World"
        self.properties["Type"] = "info"
        self.properties["Buttons"] = "ok"
        self.properties["Blocking"] = True
        self.define_schema()
        self.register_handlers()

    def define_schema(self):
        self.input_schema = {
            "Flow": DataType.FLOW,
            "Title": DataType.STRING,
            "Message": DataType.STRING,
            "Type": DataType.MSGTYPE,
            "Buttons": DataType.STRING,
            "Blocking": DataType.BOOLEAN
        }
        self.output_schema = {
            "Flow": DataType.FLOW,
            "Result": DataType.STRING
        }

    def register_handlers(self):
        self.register_handler("Flow", self.do_work)

    def do_work(self, Message=None, Title=None, Type=None, Buttons=None, Blocking=None, **kwargs):
        msg = Message if Message is not None else self.properties.get("Message", "Hello World")
        title = Title if Title is not None else self.properties.get("Title", "Message")
        msg_type = (Type if Type is not None else self.properties.get("Type", "info")).lower()
        buttons = (Buttons if Buttons is not None else self.properties.get("Buttons", "ok")).lower()
        blocking = Blocking if Blocking is not None else self.properties.get("Blocking", True)
        
        is_headless = not HAS_GUI
        if HAS_GUI:
            app = QApplication.instance()
            if not app: is_headless = True
            
        if is_headless:
            prefix = f"[{msg_type.upper()}]"
            print(f"\n{prefix} {title}: {msg}")
            
            res = "ok"
            if buttons in ["yes_no", "ok_cancel"]:
                if buttons == "yes_no":
                    ans = input(" (y/n): ").strip().lower()
                    res = "yes" if ans.startswith("y") else "no"
                else:
                    ans = input(" Press Enter to Continue (or type 'c' to cancel): ").strip().lower()
                    res = "cancel" if ans == 'c' else "ok"
            
            self.bridge.set(f"{self.node_id}_Result", res, self.name)
            self.bridge.set(f"{self.node_id}_ActivePorts", ["Flow"], self.name)
            return True
        
        req_id = f"MSG_{self.node_id}_{time.time_ns()}"
        payload = {
            "id": req_id,
            "title": title,
            "text": str(msg),
            "type": msg_type,
            "buttons": buttons
        }
        
        self.bridge.set("SHOW_MESSAGE", payload, self.name)
        
        if not blocking:
            self.bridge.set(f"{self.node_id}_Result", "triggered", self.name)
            self.bridge.set(f"{self.node_id}_ActivePorts", ["Flow"], self.name)
            return True

        resp_key = f"MESSAGE_RESPONSE_{req_id}"
        max_retries = 6000 
        
        res = "ok"
        for _ in range(max_retries):
            val = self.bridge.get(resp_key)
            if val:
                res = val
                self.bridge.delete(resp_key)
                break
            time.sleep(0.1)
            
        self.bridge.set(f"{self.node_id}_Result", res, self.name)
        self.bridge.set(f"{self.node_id}_ActivePorts", ["Flow"], self.name)
        return True

@NodeRegistry.register("Text Display", "UI")
class TextDisplayNode(SuperNode):
    """
    Displays text content to the user in a dedicated window or console block.
    Commonly used for showing long reports, logs, or multi-line data summaries.
    
    Inputs:
    - Flow: Trigger the display.
    - Text: The string content to show.
    
    Outputs:
    - Flow: Pulse triggered after the window is closed or processed.
    """
    version = "2.1.0"

    def __init__(self, node_id, name, bridge):
        super().__init__(node_id, name, bridge)
        self.properties["Title"] = "Text Output"
        self.properties["Blocking"] = True
        self.properties["Text"] = ""
        self.define_schema()
        self.register_handlers()

    def define_schema(self):
        self.input_schema = {
            "Flow": DataType.FLOW,
            "Title": DataType.STRING,
            "Blocking": DataType.BOOLEAN,
            "Text": DataType.STRING
        }
        self.output_schema = {
            "Flow": DataType.FLOW
        }

    def register_handlers(self):
        self.register_handler("Flow", self.do_work)

    def do_work(self, Text=None, Title=None, Blocking=None, **kwargs):
        text_val = Text if Text is not None else kwargs.get("Text") or self.properties.get("Text", "")
        title = Title if Title is not None else kwargs.get("Title") or self.properties.get("Title", "Text Output")
        blocking = Blocking if Blocking is not None else kwargs.get("Blocking") if kwargs.get("Blocking") is not None else self.properties.get("Blocking", True)
        
        is_headless = not HAS_GUI
        if HAS_GUI and not QApplication.instance():
            is_headless = True
            
        if is_headless:
            print(f"\n--- {title} ---")
            print(text_val)
            print("-------------------")
            self.bridge.set(f"{self.node_id}_ActivePorts", ["Flow"], self.name)
            return True
            
        req_id = f"TXT_{self.node_id}_{time.time_ns()}"
        payload = {
            "id": req_id,
            "title": title,
            "text": str(text_val)
        }
        
        self.bridge.set("SHOW_TEXT_DIALOG", payload, self.name)
        
        if not blocking:
            self.bridge.set(f"{self.node_id}_ActivePorts", ["Flow"], self.name)
            return True

        resp_key = f"TEXT_RESPONSE_{req_id}"
        max_retries = 6000 
        
        for _ in range(max_retries):
            if self.bridge.get(resp_key):
                self.bridge.delete(resp_key)
                break
            time.sleep(0.1)
            
        self.bridge.set(f"{self.node_id}_ActivePorts", ["Flow"], self.name)
        return True
