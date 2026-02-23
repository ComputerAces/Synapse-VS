from synapse.nodes.registry import NodeRegistry
from synapse.core.types import DataType
from synapse.core.vector import BM25VectorProvider
from synapse.nodes.lib.provider_node import ProviderNode

@NodeRegistry.register("BM25 Provider", "AI/Vector")
class BM25ProviderNode(ProviderNode):
    """
    Service provider for BM25 (Best Matching 25) rank-based keyword search.
    Operates as a local Vector Provider using lexical relevance.
    
    Inputs:
    - Flow: Start the BM25 service scope.
    - Provider End: Close the service scope.
    - Corpus: A list of text documents to index for searching.
    
    Outputs:
    - Provider Flow: Active while the provider service is running.
    - Provider ID: Unique ID for this specific provider instance.
    - Flow: Triggered when the service is stopped.
    """
    version = "2.1.0"

    def __init__(self, node_id, name, bridge):
        super().__init__(node_id, name, bridge)
        self.provider_type = "VECTOR"
        self.define_schema()
        self.register_handlers()

    def define_schema(self):
        super().define_schema()
        self.input_schema["Corpus"] = DataType.LIST

    def start_scope(self, **kwargs):
        corpus = kwargs.get("Corpus")
        
        try:
            provider = BM25VectorProvider(corpus=corpus)
            self.logger.info("BM25 Provider initialized.")
            # Register in bridge for components
            self.bridge.set(f"context_provider_{self.provider_type}", provider, self.name)
            return super().start_scope(**kwargs)
        except Exception as e:
            self.logger.error(f"Failed to init BM25: {e}")
            return super().start_scope(**kwargs)

