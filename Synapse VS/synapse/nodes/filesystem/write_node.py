from synapse.core.super_node import SuperNode
from synapse.nodes.registry import NodeRegistry
from synapse.core.types import DataType
from synapse.utils.path_utils import resolve_project_path
import os

@NodeRegistry.register("Write File", "File System")
class WriteNode(SuperNode):
    """
    Writes data to a specified file path with smart type detection.
    
    Supports writing Text, Binary (bytes), JSON (as objects), and Images 
    (PIL objects). Automatically creates parent directories if they are missing.
    
    Inputs:
    - Flow: Trigger the write operation.
    - Path: The absolute destination file path.
    - Data: The content to write (String, Bytes, Dict, or Image).
    - Mode: Writing behavior ('Overwrite' or 'Append').
    - Start Position: Byte offset to start writing from (optional).
    
    Outputs:
    - Flow: Pulse triggered on successful write.
    - Error Flow: Pulse triggered if permission denied or error occurs.
    """
    version = "2.1.0"

    def define_schema(self):
        self.input_schema = {
            "Flow": DataType.FLOW,
            "Path": DataType.STRING,
            "Data": DataType.ANY,
            "Mode": DataType.WRITEMODE,
            "Start Position": DataType.NUMBER
        }
        self.output_schema = {
            "Flow": DataType.FLOW,
            "Error Flow": DataType.FLOW
        }

    def register_handlers(self):
        self.register_handler("Flow", self.handle_write)

    def handle_write(self, Path=None, Data=None, Mode=None, Start_Position=None, **kwargs):
        path = Path if Path is not None else kwargs.get("Path") or self.properties.get("Path", "output.txt")
        start_pos = int(Start_Position) if Start_Position is not None else int(self.properties.get("Start Position", 0))
        
        # [PERMISSION CHECK]
        user_provider_id = self.get_provider_id("User Provider")
        if user_provider_id:
            user_provider = self.bridge.get(user_provider_id)
            if user_provider and hasattr(user_provider, "has_permission"):
                if not user_provider.has_permission("file system"):
                    self.logger.error("Permission Denied: User lacks 'file system' access.")
                    self.bridge.set(f"{self.node_id}_ActivePorts", ["Error Flow"], self.name)
                    return True

        # [PROJECT VARS] Resolve path against project variables
        path = resolve_project_path(path, self.bridge)
        
        # Resolve Mode (Handles "Overwrite", "Append" from Enum, or legacy "w", "a")
        mode_val = Mode or kwargs.get("Mode") or self.properties.get("Mode", "Overwrite")
        is_append = mode_val in ["Append", "a"]
        
        try:
            # Ensure dir exists
            os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
            
            # --- [SMART LOGIC: Type Detection] ---
            
            # 1. Image Check (PIL Image)
            if hasattr(Data, 'save') and not isinstance(Data, (str, bytes, bytearray)):
                try:
                    Data.save(path)
                    self.logger.info(f"Smart Write: Saved Image to {os.path.basename(path)}")
                    self.bridge.set(f"{self.node_id}_ActivePorts", ["Flow"], self.name)
                    return True
                except Exception as ie:
                    self.logger.error(f"Image Save Error: {ie}")

            # 2. Binary Check
            if isinstance(Data, (bytes, bytearray)):
                open_mode = "rb+" if start_pos > 0 else ("ab" if is_append else "wb")
                with open(path, open_mode) as f:
                    if start_pos > 0: f.seek(start_pos)
                    f.write(Data)
                self.logger.info(f"Smart Write: Wrote {len(Data)} bytes (Binary)")
                self.bridge.set(f"{self.node_id}_ActivePorts", ["Flow"], self.name)
                return True

            # 3. JSON Check (Dict/List)
            if isinstance(Data, (dict, list)):
                with open(path, "w", encoding='utf-8') as f:
                    import json
                    json.dump(Data, f, indent=4)
                self.logger.info(f"Smart Write: Wrote JSON object to {os.path.basename(path)}")
                self.bridge.set(f"{self.node_id}_ActivePorts", ["Flow"], self.name)
                return True

            # 4. Text Fallback
            text_data = str(Data) if Data is not None else ""
            open_mode = "r+" if start_pos > 0 else ("a" if is_append else "w")
            
            with open(path, open_mode, encoding='utf-8') as f:
                if start_pos > 0: f.seek(start_pos)
                f.write(text_data)
                
            self.logger.info(f"Smart Write: Wrote {len(text_data)} chars (Text)")
            self.bridge.set(f"{self.node_id}_ActivePorts", ["Flow"], self.name)
            return True
            
        except Exception as e:
            self.logger.error(f"Write Error: {e}")
            self.bridge.set(f"{self.node_id}_ActivePorts", ["Error Flow"], self.name)
        return True

    def __init__(self, node_id, name, bridge):
        super().__init__(node_id, name, bridge)
        self.properties["Path"] = "output.txt"
        self.properties["Mode"] = "Overwrite"
        self.properties["Start Position"] = 0
        self.define_schema()
