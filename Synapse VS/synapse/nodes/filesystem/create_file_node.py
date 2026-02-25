import os
from synapse.core.super_node import SuperNode
from synapse.nodes.registry import NodeRegistry
from synapse.core.types import DataType
from synapse.utils.path_utils import resolve_project_path
from synapse.core.data import DataBuffer

@NodeRegistry.register("Create File", "File System")
class CreateFileNode(SuperNode):
    """
    Creates a new file at the specified path with the provided content.
    Automatically creates parent directories and supports overwriting existing files.
    
    Inputs:
    - Flow: Trigger the file creation.
    - Path: The full path where the file should be created.
    - Content: The text or binary data to write into the file.
    
    Outputs:
    - Flow: Triggered if the file is created successfully.
    - Error Flow: Triggered if the path is invalid or an I/O error occurs.
    """
    version = "2.1.0"

    def __init__(self, node_id, name, bridge):
        super().__init__(node_id, name, bridge)
        self.is_native = True
        self.properties["Path"] = ""
        self.properties["Overwrite"] = False
        self.define_schema()
        self.register_handlers()

    def define_schema(self):
        self.input_schema = {
            "Flow": DataType.FLOW,
            "Path": DataType.STRING,
            "Content": DataType.STRING
        }
        self.output_schema = {
            "Flow": DataType.FLOW,
            "Error Flow": DataType.FLOW
        }

    def register_handlers(self):
        self.register_handler("Flow", self.create_file)

    def create_file(self, Path=None, Content=None, **kwargs):
        path = Path if Path is not None else kwargs.get("Path") or self.properties.get("Path", "")
        content = Content if Content is not None else ""
        overwrite = self.properties.get("Overwrite", False)
        
        if not path:
            self.logger.error("Error: No path specified.")
            self.bridge.set(f"{self.node_id}_ActivePorts", ["Error Flow"], self.name)
            return True
            
        # [PROJECT VARS] Resolve path against project variables
        path = resolve_project_path(path, self.bridge)
        
        try:
            # Check if file exists and overwrite is disabled
            if os.path.exists(path) and not overwrite:
                self.logger.warning(f"File already exists (overwrite=False): {path}")
                self.bridge.set(f"{self.node_id}_ActivePorts", ["Error Flow"], self.name)
                return True
            
            # Create parent directories if needed
            parent_dir = os.path.dirname(path)
            if parent_dir:
                os.makedirs(parent_dir, exist_ok=True)
            
            # Create/write file
            if isinstance(content, DataBuffer):
                with open(path, 'wb') as f:
                    f.write(content.get_raw())
            else:
                with open(path, 'w', encoding='utf-8') as f:
                    f.write(str(content))
            
            self.logger.info(f"Created file: {path}")
            self.bridge.set(f"{self.node_id}_ActivePorts", ["Flow"], self.name)
            return True
        except Exception as e:
            self.logger.error(f"Error creating file: {e}")
            self.bridge.set(f"{self.node_id}_ActivePorts", ["Error Flow"], self.name)
            return True
