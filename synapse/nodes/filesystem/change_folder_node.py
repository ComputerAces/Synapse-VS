import os
from synapse.core.super_node import SuperNode
from synapse.nodes.registry import NodeRegistry
from synapse.core.types import DataType

@NodeRegistry.register("Change Folder", "File System")
class ChangeFolderNode(SuperNode):
    """
    Changes the current working directory or global path reference for file operations.
    Validates that the target path exists and is a directory before applying the change.
    
    Inputs:
    - Flow: Trigger the path change.
    - Path: The absolute or relative path to switch to.
    
    Outputs:
    - Flow: Triggered if the path was successfully changed.
    - Error Flow: Triggered if the path is invalid or inaccessible.
    """
    version = "2.1.0"

    def __init__(self, node_id, name, bridge):
        super().__init__(node_id, name, bridge)
        self.is_native = True
        self.properties["Path"] = ""
        self.define_schema()
        self.register_handlers()

    def define_schema(self):
        self.input_schema = {
            "Flow": DataType.FLOW,
            "Path": DataType.STRING
        }
        self.output_schema = {
            "Flow": DataType.FLOW,
            "Error Flow": DataType.FLOW
        }

    def register_handlers(self):
        self.register_handler("Flow", self.change_folder)

    def change_folder(self, Path=None, **kwargs):
        val = Path if Path is not None else kwargs.get("Path") or self.properties.get("Path", "")
        
        success = False
        if val:
             if os.path.exists(val) and os.path.isdir(val):
                 abs_path = os.path.abspath(val)
                 self.logger.info(f"Changing Global Path -> {abs_path}")
                 self.bridge.set("path", abs_path, self.name)
                 success = True
             else:
                 self.logger.error(f"Path not found or not dir: {val}")
        
        target = "Flow" if success else "Error Flow"
        self.bridge.set(f"{self.node_id}_ActivePorts", [target], self.name)
        return True
