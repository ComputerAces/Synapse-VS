import os
from axonpulse.core.node import BaseNode
from axonpulse.nodes.registry import NodeRegistry
from axonpulse.core.vector import DependencyManager, PineconeVectorDatabase
from axonpulse.nodes.lib.provider_node import ProviderNode
from axonpulse.core.types import DataType

@NodeRegistry.register("Pinecone", "AI/Vector")
class PineconeNode(ProviderNode):
    """
    Service provider for Pinecone, a managed cloud-native vector database.
    Enables high-scale similarity search and persistent storage for AI applications.
    
    Inputs:
    - Flow: Start the Pinecone service and enter the vector scope.
    - Provider End: Close the database connection and exit the scope.
    - API Key: Your Pinecone API Key.
    
    Outputs:
    - Provider Flow: Active while the database connection is open.
    - Provider ID: Unique ID for this specific provider instance.
    - Flow: Triggered when the service is stopped.
    """
    version = "2.3.0"

    def __init__(self, node_id, name, bridge):
        super().__init__(node_id, name, bridge)
        self.provider_type = "VECTOR"
        self.properties["ApiKey"] = ""
        self.properties["IndexName"] = "axonpulse-memory"
        self.properties["Namespace"] = "default"
        self.define_schema()
        self.register_handlers()

    def define_schema(self):
        super().define_schema()
        self.input_schema["API Key"] = DataType.STRING

    def start_scope(self, **kwargs):
        # Fallback with legacy support
        api_key = kwargs.get("API Key") or self.properties.get("ApiKey", self.properties.get("ApiKey", os.environ.get("PINECONE_API_KEY")))
        index_name = self.properties.get("IndexName", self.properties.get("IndexName"))
        namespace = self.properties.get("Namespace", self.properties.get("Namespace"))
        
        if not api_key:
            self.logger.warning("Pinecone API Key is missing.")
            return super().start_scope(**kwargs)

        try:
            db = PineconeVectorDatabase(api_key=api_key, index_name=index_name, namespace=namespace)
            self.bridge.set(f"{self.node_id}_Database", {"db": db, "table": namespace}, self.name)
            self.logger.info(f"Connected to Pinecone index: {index_name} (Namespace: {namespace})")
            return super().start_scope(**kwargs)
        except Exception as e:
            self.logger.error(f"Failed to connect to Pinecone: {e}")
            return super().start_scope(**kwargs)

