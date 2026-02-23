from synapse.core.super_node import SuperNode
from synapse.nodes.registry import NodeRegistry
from synapse.core.types import DataType
from synapse.utils.path_utils import resolve_project_path
import os

@NodeRegistry.register("Read File", "File System")
class ReadNode(SuperNode):
    """
    Reads content from a file path with support for smart type detection.
    
    This node can read plain text, JSON (as objects), or Images (as ImageObjects). 
    It supports project variable resolution (e.g., %ID%) and permission checks.
    
    Inputs:
    - Flow: Trigger the read operation.
    - Path: The absolute path to the file.
    - Start: Starting character offset (for text).
    - End: Ending character offset (-1 for until EOF).
    
    Outputs:
    - Flow: Pulse triggered on successful read.
    - Error Flow: Pulse triggered if the file is missing or error occurs.
    - Data: The content retrieved (String, Dict, or ImageObject).
    """
    version = "2.1.0"

    def define_schema(self):
        self.input_schema = {
            "Flow": DataType.FLOW,
            "Path": DataType.STRING,
            "Start": DataType.INT,
            "End": DataType.INT
        }
        self.output_schema = {
            "Flow": DataType.FLOW,
            "Error Flow": DataType.FLOW,
            "Data": DataType.STRING
        }

    def register_handlers(self):
        self.register_handler("Flow", self.handle_read)

    def handle_read(self, Path=None, Start=None, End=None, **kwargs):
        path = Path if Path is not None else kwargs.get("Path") or self.properties.get("Path", self.properties.get("Path", "data.txt"))
        
        # Resolve Start: Input -> Property -> Default (0)
        start_val = Start if Start is not None else kwargs.get("Start") or self.properties.get("Start", self.properties.get("StartOffset"))
        if start_val is None or start_val == "": start_val = 0
        start = int(start_val)
        
        # Resolve End: Input -> Property -> Default (-1)
        end_val = End if End is not None else kwargs.get("End") or self.properties.get("End", self.properties.get("EndOffset"))
        if end_val is None or end_val == "": end_val = -1
        end = int(end_val)
        
        # [PROJECT VARS] Resolve path against project variables
        path = resolve_project_path(path, self.bridge)
            
        if not os.path.exists(path):
            self.logger.error(f"File not found: {path}")
            self.bridge.set(f"{self.node_id}_ActivePorts", ["Error Flow"], self.name)
            return True
            
        # [PERMISSION CHECK]
        user_provider_id = self.get_provider_id("User Provider")
        if user_provider_id:
            user_provider = self.bridge.get(user_provider_id)
            if user_provider and hasattr(user_provider, "has_permission"):
                if not user_provider.has_permission("file system"):
                    self.logger.error("Permission Denied: User lacks 'file system' access.")
                    self.bridge.set(f"{self.node_id}_ActivePorts", ["Error Flow"], self.name)
                    return True
            
        try:
            ext = os.path.splitext(path)[1].lower()
            data = None
            
            # 1. Image Check
            if ext in [".jpg", ".jpeg", ".png", ".bmp", ".gif"]:
                from PIL import Image as PILImg
                from synapse.nodes.media.camera import ImageObject
                img = PILImg.open(path)
                data = ImageObject(img)
                self.logger.info(f"Smart Read: Loaded Image from {os.path.basename(path)}")
            
            # 2. JSON Check
            elif ext == ".json":
                with open(path, 'r', encoding='utf-8') as f:
                    import json
                    data = json.load(f)
                self.logger.info(f"Smart Read: Parsed JSON from {os.path.basename(path)}")
                
            # 3. Default Text/Binary Read
            else:
                with open(path, 'r', encoding='utf-8') as f:
                    if start > 0:
                        f.seek(start)
                    
                    if end != -1:
                        length = end - start
                        data = f.read(length) if length > 0 else ""
                    else:
                        data = f.read()
                self.logger.info(f"Read {len(data)} chars from {os.path.basename(path)}")
            
            # [HIJACK HOOK]
            if self.is_hijacked:
                provider_id = kwargs.get("HijackProviderId")
                data = self.bridge.invoke_hijack(provider_id, "Read File", data)

            self.bridge.set(f"{self.node_id}_Data", data, self.name)
            self.bridge.set(f"{self.node_id}_ActivePorts", ["Flow"], self.name)
            
        except Exception as e:
            self.logger.error(f"Read Error: {e}")
            self.bridge.set(f"{self.node_id}_ActivePorts", ["Error Flow"], self.name)
        return True

    def __init__(self, node_id, name, bridge):
        super().__init__(node_id, name, bridge)
        self.properties["Path"] = "data.txt"
        self.properties["Start"] = 0
        self.properties["End"] = -1
