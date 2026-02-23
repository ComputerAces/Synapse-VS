from synapse.core.node import BaseNode
from synapse.nodes.registry import NodeRegistry
from synapse.core.vector import DependencyManager, MilvusVectorDatabase
from synapse.nodes.lib.provider_node import ProviderNode
from synapse.core.types import DataType

@NodeRegistry.register("Milvus", "AI/Vector")
class MilvusNode(ProviderNode):
    """
    Service provider for Milvus, a high-performance, cloud-native vector database.
    Manages connections to standalone Milvus instances or Milvus Lite.
    
    Inputs:
    - Flow: Start the Milvus service and enter the vector scope.
    - Provider End: Close the database connection and exit the scope.
    - URI: The Milvus server address (e.g., 'http://localhost:19530').
    - Token: Authentication token/password (if required).
    - Collection Name: The target collection for search/add operations.
    
    Outputs:
    - Provider Flow: Active while the database connection is open.
    - Provider ID: Unique ID for this specific provider instance.
    - Flow: Triggered when the service is stopped.
    """
    version = "2.1.0"

    def __init__(self, node_id, name, bridge):
        super().__init__(node_id, name, bridge)
        self.provider_type = "VECTOR"
        self.properties["URI"] = "http://localhost:19530"
        self.properties["Token"] = ""
        self.properties["CollectionName"] = "synapse_knowledge"
        self.define_schema()
        self.register_handlers()

    def define_schema(self):
        super().define_schema()
        self.input_schema["URI"] = DataType.STRING
        self.input_schema["Token"] = DataType.STRING
        self.input_schema["Collection Name"] = DataType.STRING

    def start_scope(self, **kwargs):
        # Fallback with legacy support
        uri = kwargs.get("URI") or self.properties.get("URI", self.properties.get("URI"))
        token = kwargs.get("Token") or self.properties.get("Token", self.properties.get("Token"))
        collection = kwargs.get("Collection Name") or self.properties.get("CollectionName", self.properties.get("CollectionName"))

        try:
            db = MilvusVectorDatabase(uri=uri, token=token)
            self.bridge.set(f"{self.node_id}_Database", {"db": db, "table": collection}, self.name)
            self.logger.info(f"Connected to Milvus at {uri} (Collection: {collection})")
            return super().start_scope(**kwargs)
        except Exception as e:
            self.logger.error(f"Failed to connect to Milvus: {e}")
            return super().start_scope(**kwargs)

