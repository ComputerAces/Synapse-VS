from synapse.nodes.registry import NodeRegistry
from synapse.core.types import DataType
from synapse.nodes.lib.provider_node import ProviderNode

@NodeRegistry.register("ODBC Provider", "Database/Providers")
class ODBCProviderNode(ProviderNode):
    """
    Provides a connection to a database via ODBC connection string.
    
    Inputs:
    - Flow: Execution trigger.
    - Connection String: The standard ODBC connection string.
    
    Outputs:
    - Flow: Triggered when the provider is initialized.
    """
    version = "2.1.0"

    def __init__(self, node_id, name, bridge):
        super().__init__(node_id, name, bridge)
        self.provider_type = "DATABASE"
        self.properties["ConnectionString"] = ""

    def define_schema(self):
        super().define_schema()
        self.input_schema["Connection String"] = DataType.STRING

    def start_scope(self, **kwargs):
        # Fallback with legacy support
        conn_str = kwargs.get("Connection String") or self.properties.get("ConnectionString", self.properties.get("ConnectionString"))
        
        config = {"type": "odbc", "conn_str": conn_str}
        self.bridge.set(f"{self.node_id}_Connection", config, self.name)
        self.logger.info("ODBC connection configured.")
        return super().start_scope(**kwargs)
