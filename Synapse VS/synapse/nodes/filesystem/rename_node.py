import os
from synapse.core.super_node import SuperNode
from synapse.nodes.registry import NodeRegistry
from synapse.core.types import DataType
from synapse.utils.path_utils import resolve_project_path

@NodeRegistry.register("Rename File", "File System")
class RenameNode(SuperNode):
    """
    Changes the name of a file or directory while keeping it in the same folder.
    
    This node takes a full path and a new name string, then performs an 
    in-place rename within the parent directory.
    
    Inputs:
    - Flow: Trigger the rename operation.
    - OldPath: The current absolute path of the file.
    - NewName: The new name (filename only, not a path).
    
    Outputs:
    - Flow: Pulse triggered on successful rename.
    - Error Flow: Pulse triggered if the file is missing or rename fails.
    """
    version = "2.1.0"

    def __init__(self, node_id, name, bridge):
        super().__init__(node_id, name, bridge)
        self.is_native = True
        self.properties["OldPath"] = ""
        self.properties["NewName"] = ""

    def define_schema(self):
        self.input_schema = {
            "Flow": DataType.FLOW,
            "OldPath": DataType.STRING,
            "NewName": DataType.STRING
        }
        self.output_schema = {
            "Flow": DataType.FLOW,
            "Error Flow": DataType.FLOW
        }

    def register_handlers(self):
        self.register_handler("Flow", self.rename_item)

    def rename_item(self, OldPath=None, NewName=None, **kwargs):
        old = OldPath if OldPath is not None else kwargs.get("OldPath") or self.properties.get("OldPath", self.properties.get("OldPath", ""))
        new = NewName if NewName is not None else kwargs.get("NewName") or self.properties.get("NewName", self.properties.get("NewName", ""))
        
        # [PROJECT VARS] Resolve path against project variables
        old = resolve_project_path(old, self.bridge)
            
        if not old or not os.path.exists(old):
            self.logger.error(f"Error: Source not found {old}")
            self.bridge.set(f"{self.node_id}_ActivePorts", ["Error Flow"], self.name)
            return True
            
        # If new name is just a name, keep directory
        base_dir = os.path.dirname(old)
        new_path = os.path.join(base_dir, new)
        
        try:
            os.rename(old, new_path)
            self.logger.info(f"Renamed to {new_path}")
            self.bridge.set(f"{self.node_id}_ActivePorts", ["Flow"], self.name)
            return True
        except Exception as e:
            self.logger.error(f"Rename Error: {e}")
            self.bridge.set(f"{self.node_id}_ActivePorts", ["Error Flow"], self.name)
        return True
