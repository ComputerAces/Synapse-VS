import os
from synapse.core.super_node import SuperNode
from synapse.nodes.registry import NodeRegistry
from synapse.core.types import DataType
from synapse.utils.path_utils import resolve_project_path

@NodeRegistry.register("Path Exists", "File System")
class ExistsNode(SuperNode):
    """
    Checks if a path exists and identifies its type (File vs Directory).
    
    Provides boolean outputs for existence and classification, useful for 
    conditional branching before performing file operations.
    
    Inputs:
    - Flow: Trigger the existence check.
    - Path: The absolute path to verify.
    
    Outputs:
    - Flow: Pulse triggered after the check.
    - Exists: True if the path exists.
    - IsFile: True if the path points to a file.
    - IsDir: True if the path points to a directory.
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
            "Exists": DataType.BOOLEAN,
            "IsFile": DataType.BOOLEAN,
            "IsDir": DataType.BOOLEAN
        }

    def register_handlers(self):
        self.register_handler("Flow", self.check_exists)

    def check_exists(self, Path=None, **kwargs):
        path = Path if Path is not None else kwargs.get("Path") or self.properties.get("Path", self.properties.get("Path", ""))
        
        # [PROJECT VARS] Resolve path against project variables
        path = resolve_project_path(path, self.bridge)
        
        if path:
            path = os.path.normpath(path)
            
        exists = os.path.exists(path) if path else False
        is_file = os.path.isfile(path) if path else False
        is_dir = os.path.isdir(path) if path else False
        
        self.logger.info(f"Path '{path}': Exists={exists}, IsFile={is_file}, IsDir={is_dir}")
        
        self.bridge.set(f"{self.node_id}_Exists", exists, self.name)
        self.bridge.set(f"{self.node_id}_IsFile", is_file, self.name)
        self.bridge.set(f"{self.node_id}_IsDir", is_dir, self.name)
        
        self.bridge.set(f"{self.node_id}_ActivePorts", ["Flow"], self.name)
        return True
