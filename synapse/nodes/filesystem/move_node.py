import os
import shutil
from synapse.core.super_node import SuperNode
from synapse.nodes.registry import NodeRegistry
from synapse.core.types import DataType
from synapse.utils.path_utils import resolve_project_path

@NodeRegistry.register("Move File", "File System")
class MoveNode(SuperNode):
    """
    Moves or renames a file or directory to a new location.
    
    Uses high-level shell operations to relocate items across the file system. 
    Supports project variable resolution for both Source and Destination.
    
    Inputs:
    - Flow: Trigger the move operation.
    - Source: The absolute current path of the item.
    - Dest: The absolute destination path (including new name if applicable).
    
    Outputs:
    - Flow: Pulse triggered on successful move.
    - Error Flow: Pulse triggered if the move fails or source is missing.
    """
    version = "2.1.0"

    def __init__(self, node_id, name, bridge):
        super().__init__(node_id, name, bridge)
        self.is_native = True
        self.properties["Source"] = ""
        self.properties["Dest"] = ""

    def define_schema(self):
        self.input_schema = {
            "Flow": DataType.FLOW,
            "Source": DataType.STRING,
            "Dest": DataType.STRING
        }
        self.output_schema = {
            "Flow": DataType.FLOW,
            "Error Flow": DataType.FLOW
        }

    def register_handlers(self):
        self.register_handler("Flow", self.move_item)

    def move_item(self, Source=None, Dest=None, **kwargs):
        src = Source if Source is not None else kwargs.get("Source") or self.properties.get("Source", self.properties.get("Source", ""))
        dst = Dest if Dest is not None else kwargs.get("Dest") or self.properties.get("Dest", self.properties.get("Dest", ""))
        
        # [PROJECT VARS] Resolve paths against project variables
        src = resolve_project_path(src, self.bridge)
        dst = resolve_project_path(dst, self.bridge)
        
        if not src or not os.path.exists(src):
            self.logger.error(f"Error: Source not found {src}")
            self.bridge.set(f"{self.node_id}_ActivePorts", ["Error Flow"], self.name)
            return True
            
        try:
            shutil.move(src, dst)
            self.logger.info(f"Moved {src} -> {dst}")
            self.bridge.set(f"{self.node_id}_ActivePorts", ["Flow"], self.name)
            return True
        except Exception as e:
            self.logger.error(f"Move Error: {e}")
            self.bridge.set(f"{self.node_id}_ActivePorts", ["Error Flow"], self.name)
        return True
