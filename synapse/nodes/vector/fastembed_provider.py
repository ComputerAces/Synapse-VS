from synapse.core.node import BaseNode
from synapse.nodes.registry import NodeRegistry
from synapse.core.vector import DependencyManager, FastEmbedProvider
from synapse.core.types import DataType
from synapse.nodes.lib.provider_node import ProviderNode

@NodeRegistry.register("FastEmbed Provider", "AI/Vector")
class FastEmbedProviderNode(ProviderNode):
    """
    Service provider for local document embedding using the 'fastembed' library.
    Highly optimized for CPU-based vector generation.
    
    Inputs:
    - Flow: Start resizing/embedding service scope.
    - Provider End: Close the service scope.
    - Model Name: The specific embedding model to load (e.g., 'BAAI/bge-small-en-v1.5').
    
    Outputs:
    - Provider Flow: Active while the embedding service is running.
    - Provider ID: Unique ID for this specific provider instance.
    - Flow: Triggered when the service is stopped.
    """
    version = "2.1.0"

    def __init__(self, node_id, name, bridge):
        super().__init__(node_id, name, bridge)
        self.provider_type = "VECTOR"
        self.properties["ModelName"] = "BAAI/bge-small-en-v1.5"
        self.define_schema()
        self.register_handlers()
    
    def define_schema(self):
        super().define_schema()

    def start_scope(self, **kwargs):
        # Fallback with legacy support
        model_name = self.properties.get("Model Name") or self.properties.get("ModelName", "BAAI/bge-small-en-v1.5")
        if not DependencyManager.ensure("fastembed"):
            self.logger.error("FastEmbed dependencies missing.")
            return super().start_scope(**kwargs)
            
        try:
            provider = FastEmbedProvider(model_name=model_name)
            self.bridge.set(f"{self.node_id}_Provider", provider, self.name)
            self.logger.info(f"FastEmbed initialized with model: {model_name}")
            return super().start_scope(**kwargs)
        except Exception as e:
            self.logger.error(f"Failed to init FastEmbed: {e}")
            return super().start_scope(**kwargs)

