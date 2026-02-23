import os
from synapse.core.super_node import SuperNode
from synapse.nodes.registry import NodeRegistry
from synapse.core.types import DataType

@NodeRegistry.register("Current Folder", "File System")
class CurrentFolderNode(SuperNode):
    """
    Retrieves the absolute path of the current working directory or the specific project path context.
    
    Inputs:
    - Flow: Trigger the path retrieval.
    
    Outputs:
    - Flow: Triggered after the path is retrieved.
    - Path: The absolute directory path.
    """
    version = "2.1.0"

    def __init__(self, node_id, name, bridge):
        super().__init__(node_id, name, bridge)
        self.is_native = True

    def define_schema(self):
        self.input_schema = {
            "Flow": DataType.FLOW
        }
        self.output_schema = {
            "Flow": DataType.FLOW,
            "Path": DataType.STRING
        }

    def register_handlers(self):
        self.register_handler("Flow", self.get_current_folder)

    def get_current_folder(self, **kwargs):
        path = self.bridge.get("path")
        if not path:
            path = os.getcwd()
            
        self.logger.info(f"Current Folder: {path}")
        self.bridge.set(f"{self.node_id}_Path", path, self.name)
        self.bridge.set(f"{self.node_id}_ActivePorts", ["Flow"], self.name)
        return True
