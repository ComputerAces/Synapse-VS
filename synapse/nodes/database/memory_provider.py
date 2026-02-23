from synapse.nodes.registry import NodeRegistry
from synapse.core.types import DataType
from synapse.nodes.lib.provider_node import ProviderNode

@NodeRegistry.register("Memory Data Provider", "Database/Providers")
class MemoryDataProviderNode(ProviderNode):
    """
    Provides a temporary in-memory SQL database connection.
    
    Inputs:
    - Flow: Execution trigger.
    
    Outputs:
    - Flow: Triggered when the provider is initialized.
    """
    version = "2.1.0"

    def __init__(self, node_id, name, bridge):
        super().__init__(node_id, name, bridge)
        self.provider_type = "DATABASE"

    def define_schema(self):
        super().define_schema()

    def start_scope(self, **kwargs):
        config = {"type": "sqlite", "path": ":memory:"}
        self.bridge.set(f"{self.node_id}_Connection", config, self.name)
        self.logger.info("Memory Data Provider initialized.")
        return super().start_scope(**kwargs)

