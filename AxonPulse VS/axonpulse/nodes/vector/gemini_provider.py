import os
from axonpulse.core.node import BaseNode
from axonpulse.nodes.registry import NodeRegistry
from axonpulse.core.vector import GeminiVectorProvider
from axonpulse.core.types import DataType
from axonpulse.nodes.lib.provider_node import ProviderNode

@NodeRegistry.register("Gemini Embeddings", "AI/Vector")
class GeminiVectorNode(ProviderNode):
    """
    Service provider for Google's Gemini embedding models.
    Generates high-quality vector representations of text for semantic search.
    
    Inputs:
    - Flow: Start the embedding service and enter the EMBED scope.
    - Provider End: Close the service and exit the scope.
    - API Key: Your Google Gemini API Key.
    
    Outputs:
    - Provider Flow: Active while the embedding service is running.
    - Provider ID: Unique ID for this specific provider instance.
    - Flow: Triggered when the service is stopped.
    """
    version = "2.3.0"

    def __init__(self, node_id, name, bridge):
        super().__init__(node_id, name, bridge)
        self.provider_type = "EMBED"
        self.properties["Model Name"] = "models/embedding-001"
        self.properties["API Key"] = ""
        self.define_schema()
        self.register_handlers()

    def define_schema(self):
        super().define_schema()
        self.input_schema["API Key"] = DataType.STRING
        
    def start_scope(self, **kwargs):
        # Fallback
        api_key = kwargs.get("API Key") or self.properties.get("API Key") or os.environ.get("GEMINI_API_KEY")
        model = self.properties.get("Model Name", "models/embedding-001")
        
        if not api_key:
            self.logger.warning("Gemini API Key is missing.")
            return super().start_scope(**kwargs)

        try:
            provider = GeminiVectorProvider(api_key, model)
            self.logger.info(f"Gemini Embeddings initialized with model: {model}")
            # Register in bridge for components
            self.bridge.set(f"context_provider_{self.provider_type}", provider, self.name)
            return super().start_scope(**kwargs)
        except Exception as e:
            self.logger.error(f"Failed to init Gemini Embed: {e}")
            return super().start_scope(**kwargs)

