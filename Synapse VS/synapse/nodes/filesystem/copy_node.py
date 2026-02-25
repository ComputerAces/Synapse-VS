import os
import shutil
from synapse.core.super_node import SuperNode
from synapse.nodes.registry import NodeRegistry
from synapse.core.types import DataType
from synapse.utils.path_utils import resolve_project_path

@NodeRegistry.register("Copy File", "File System")
class CopyNode(SuperNode):
    """
    Copies a file or directory from a source path to a destination path.
    Supports recursive directory copying and automatic parent directory creation.
    
    Inputs:
    - Flow: Trigger the copy operation.
    - Source: The path to the file or folder to copy.
    - Destination: The target path where the item should be copied.
    
    Outputs:
    - Flow: Triggered if the copy operation completes successfully.
    - Error Flow: Triggered if the source is missing or an I/O error occurs.
    """
    version = "2.1.0"

    def __init__(self, node_id, name, bridge):
        super().__init__(node_id, name, bridge)
        self.is_native = True
        self.properties["Source"] = ""
        self.properties["Destination"] = ""
        self.define_schema()
        self.register_handlers()

    def define_schema(self):
        self.input_schema = {
            "Flow": DataType.FLOW,
            "Source": DataType.STRING,
            "Destination": DataType.STRING
        }
        self.output_schema = {
            "Flow": DataType.FLOW,
            "Error Flow": DataType.FLOW
        }

    def register_handlers(self):
        self.register_handler("Flow", self.copy_item)

    def copy_item(self, Source=None, Destination=None, **kwargs):
        source = Source if Source is not None else kwargs.get("Source") or self.properties.get("Source", "")
        destination = Destination if Destination is not None else kwargs.get("Destination") or self.properties.get("Destination", "")
        
        if not source or not destination:
            self.logger.error("Error: Source and destination required.")
            self.bridge.set(f"{self.node_id}_ActivePorts", ["Error Flow"], self.name)
            return True

        # [PROJECT VARS] Resolve paths against project variables
        source = resolve_project_path(source, self.bridge)
        destination = resolve_project_path(destination, self.bridge)
        
        try:
            if not os.path.exists(source):
                self.logger.error(f"Error: Source not found: {source}")
                self.bridge.set(f"{self.node_id}_ActivePorts", ["Error Flow"], self.name)
                return True
            
            # Create parent directories for destination
            dest_dir = os.path.dirname(destination)
            if dest_dir:
                os.makedirs(dest_dir, exist_ok=True)
            
            if os.path.isdir(source):
                # Copy directory recursively
                shutil.copytree(source, destination, dirs_exist_ok=True)
                self.logger.info(f"Copied directory: {source} -> {destination}")
            else:
                # Copy file
                shutil.copy2(source, destination)
                self.logger.info(f"Copied file: {source} -> {destination}")
            
            self.bridge.set(f"{self.node_id}_ActivePorts", ["Flow"], self.name)
            return True
        except Exception as e:
            self.logger.error(f"Error executing copy: {e}")
            self.bridge.set(f"{self.node_id}_ActivePorts", ["Error Flow"], self.name)
            return True
