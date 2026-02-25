from synapse.core.super_node import SuperNode
from synapse.nodes.registry import NodeRegistry
from synapse.core.types import DataType
from synapse.utils.path_utils import resolve_project_path
import os

@NodeRegistry.register("List Files", "File System")
class ListFilesNode(SuperNode):
    """
    Retrieves a list of filenames within a specified directory.
    
    Filters for files only (excluding subdirectories). Supports project 
    variable resolution and defaults to the current working directory if empty.
    
    Inputs:
    - Flow: Trigger the listing operation.
    - Path: The absolute path of the folder to scan.
    
    Outputs:
    - Flow: Pulse triggered after the operation.
    - Files List: A list of strings containing the names of files found.
    """
    version = "2.1.0"

    def define_schema(self):
        self.input_schema = {
            "Flow": DataType.FLOW,
            "Path": DataType.STRING
        }
        self.output_schema = {
            "Flow": DataType.FLOW,
            "Files List": DataType.LIST
        }

    def register_handlers(self):
        self.register_handler("Flow", self.handle_list)

    def handle_list(self, Path=None, **kwargs):
        # 1. Determine Path: Input -> Prop -> Project 'path' -> CWD
        raw_path = Path if Path is not None else kwargs.get("Path") or self.properties.get("Path", self.properties.get("Path", ""))
        
        if not raw_path:
            # Fallback to Project Variables (via utility which handles this)
            raw_path = os.getcwd()  # Start with CWD as default
           
        # [PROJECT VARS] Resolve path against project variables
        target_path = resolve_project_path(raw_path, self.bridge)
        target_path = os.path.abspath(target_path)
        
        results = []
        if os.path.exists(target_path) and os.path.isdir(target_path):
            try:
                results = [f for f in os.listdir(target_path) if os.path.isfile(os.path.join(target_path, f))]
                self.logger.info(f"Listing {target_path}: {len(results)} files")
            except Exception as e:
                self.logger.error(f"Error listing {target_path}: {e}")
        else:
            self.logger.error(f"Invalid Directory: {target_path}")
            
        # Set output
        self.bridge.set(f"{self.node_id}_Files List", results, self.name)
        self.bridge.set(f"{self.node_id}_ActivePorts", ["Flow"], self.name)
        return True

    def __init__(self, node_id, name, bridge):
        super().__init__(node_id, name, bridge)
        self.properties["Path"] = ""
