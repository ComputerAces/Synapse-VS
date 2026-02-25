import os
import shutil
from synapse.core.super_node import SuperNode
from synapse.nodes.registry import NodeRegistry
from synapse.core.types import DataType
from synapse.utils.path_utils import resolve_project_path

@NodeRegistry.register("Delete File", "File System")
class DeleteNode(SuperNode):
    """
    Deletes a file or directory from the filesystem.
    
    Inputs:
    - Flow: Execution trigger.
    - Path: The absolute or relative path to the item to delete.
    
    Outputs:
    - Flow: Triggered after the deletion attempt.
    - Error Flow: Triggered if the deletion failed.
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
        self.register_handler("Flow", self.delete_item)

    def delete_item(self, Path=None, **kwargs):
        path = Path if Path is not None else kwargs.get("Path") or self.properties.get("Path", self.properties.get("Path", ""))
        
        # [PROJECT VARS] Resolve path against project variables
        path = resolve_project_path(path, self.bridge)
        
        if not path or not os.path.exists(path):
            self.logger.warning(f"Warning: File not found {path}")
            self.bridge.set(f"{self.node_id}_ActivePorts", ["Flow"], self.name)
            return True # Continue flow anyway
            
        # [PERMISSION CHECK]
        # Assuming SuperNode has get_provider_id or similar logic from BaseNode?
        # SuperNode inherits from BaseNode usually.
        user_provider_id = self.get_provider_id("User Provider")
        if user_provider_id:
            user_provider = self.bridge.get(user_provider_id)
            if user_provider and hasattr(user_provider, "has_permission"):
                if not user_provider.has_permission("file system"):
                    self.logger.error("Permission Denied: User lacks 'file system' access.")
                    self.bridge.set(f"{self.node_id}_ActivePorts", ["Flow"], self.name)
                    return True
            
        try:
            if os.path.isdir(path):
                shutil.rmtree(path)
            else:
                os.remove(path)
            self.logger.info(f"Deleted {path}")
            self.bridge.set(f"{self.node_id}_ActivePorts", ["Flow"], self.name)
            return True
        except Exception as e:
            self.logger.error(f"Delete Error: {e}")
            self.bridge.set(f"{self.node_id}_ActivePorts", ["Error Flow"], self.name)
        return True
