from synapse.nodes.registry import NodeRegistry
from synapse.core.types import DataType
from synapse.nodes.lib.provider_node import ProviderNode

@NodeRegistry.register("SQLite Provider", "Database/Providers")
class SQLiteProviderNode(ProviderNode):
    """
    Provides a connection to a local SQLite database file.
    
    Inputs:
    - Flow: Execution trigger.
    - Filename: The path to the SQLite database file.
    
    Outputs:
    - Flow: Triggered when the provider is initialized.
    """
    version = "2.1.0"

    def __init__(self, node_id, name, bridge):
        super().__init__(node_id, name, bridge)
        self.provider_type = "DATABASE"
        self.properties["Filename"] = "data.db"

    def define_schema(self):
        super().define_schema()
        self.input_schema["Filename"] = DataType.STRING

    def start_scope(self, **kwargs):
        # Fallback with legacy support
        path = kwargs.get("Filename") or self.properties.get("Filename", self.properties.get("Filename"))
        
        config = {"type": "sqlite", "path": path}
        self.bridge.set(f"{self.node_id}_Connection", config, self.name)
        self.logger.info(f"SQLite connection configured: {path}")
        return super().start_scope(**kwargs)
