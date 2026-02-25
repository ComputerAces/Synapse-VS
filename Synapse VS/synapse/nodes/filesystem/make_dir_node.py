import os
from synapse.core.super_node import SuperNode
from synapse.nodes.registry import NodeRegistry
from synapse.core.types import DataType
from synapse.utils.path_utils import resolve_project_path

@NodeRegistry.register("Make Directory", "File System")
class MakeDirNode(SuperNode):
    """
    Creates a new directory at the specified path.
    
    Automatically creates all parent directories if they do not exist 
    (equivalent to 'mkdir -p'). Supports project variable resolution.
    
    Inputs:
    - Flow: Trigger the directory creation.
    - Path: The absolute path of the directory to create.
    
    Outputs:
    - Flow: Pulse triggered on successful creation.
    - Error Flow: Pulse triggered if the operation fails (e.g., permission denied).
    """
    version = "2.1.0"

    def __init__(self, node_id, name, bridge):
        super().__init__(node_id, name, bridge)
        self.is_native = True
        self.properties["Path"] = ""

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
        self.register_handler("Flow", self.make_directory)

    def make_directory(self, Path=None, **kwargs):
        path = Path if Path is not None else kwargs.get("Path") or self.properties.get("Path", self.properties.get("Path", ""))
        
        if not path:
            self.logger.error("Error: No path specified.")
            self.bridge.set(f"{self.node_id}_ActivePorts", ["Error Flow"], self.name)
            return True
            
        # [PROJECT VARS] Resolve path against project variables
        path = resolve_project_path(path, self.bridge)
        
        try:
            # makedirs creates parent directories too
            os.makedirs(path, exist_ok=True)
            self.logger.info(f"Created directory: {path}")
            self.bridge.set(f"{self.node_id}_ActivePorts", ["Flow"], self.name)
            return True
        except Exception as e:
            self.logger.error(f"Error: {e}")
            self.bridge.set(f"{self.node_id}_ActivePorts", ["Error Flow"], self.name)
        return True
