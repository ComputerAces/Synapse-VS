from synapse.nodes.registry import NodeRegistry
from synapse.core.types import DataType
from synapse.nodes.lib.provider_node import ProviderNode

@NodeRegistry.register("JSON Data Provider", "Database/Providers")
class JSONDataProviderNode(ProviderNode):
    """
    Provides a mock database connection backed by a local JSON file.
    
    Inputs:
    - Flow: Execution trigger.
    - File Path: Path to the JSON database file.
    
    Outputs:
    - Flow: Triggered when the provider is initialized.
    """
    version = "2.1.0"
    
    def __init__(self, node_id, name, bridge):
        super().__init__(node_id, name, bridge)
        self.provider_type = "DATABASE"
        self.properties["FilePath"] = "database.json"

    def define_schema(self):
        super().define_schema()
        self.input_schema["File Path"] = DataType.STRING

    def start_scope(self, **kwargs):
        # Fallback with legacy support
        path = kwargs.get("File Path") or self.properties.get("FilePath", self.properties.get("FilePath"))
        
        config = {"type": "json", "path": path}
        self.bridge.set(f"{self.node_id}_Connection", config, self.name)
        self.logger.info(f"JSON Data Provider initialized: {path}")
        

