from synapse.core.super_node import SuperNode
from synapse.nodes.registry import NodeRegistry
from synapse.core.types import DataType

@NodeRegistry.register("Vector Search", "AI/Vector")
class VectorSearchNode(SuperNode):
    """
    Performs a semantic similarity search against a connected Vector Database Provider.
    Automatically leverages an Embedding Provider to vectorize the query before searching.
    Assumes a Provider Flow connection for both VECTOR and EMBED capabilities.
    
    Inputs:
    - Flow: Trigger the search operation.
    - Query: The text string to search for.
    - Limit: The maximum number of results to return (default: 5).
    
    Outputs:
    - Flow: Triggered after search is complete.
    - Results: List of matching document text.
    - Scores: List of similarity scores (0.0 to 1.0).
    - Metadata: List of metadata dictionaries for each result.
    """
    version = "2.1.0"

    def __init__(self, node_id, name, bridge):
        super().__init__(node_id, name, bridge)
        self.required_providers = ["VECTOR", "EMBED"]
        self.properties["Limit"] = 5
        self.define_schema()
        self.register_handlers()

    def register_handlers(self):
        self.register_handler("Flow", self.do_work)

    def define_schema(self):
        self.input_schema = {
            "Flow": DataType.FLOW,
            "Query": DataType.STRING,
            "Limit": DataType.INTEGER
        }
        self.output_schema = {
            "Flow": DataType.FLOW,
            "Results": DataType.LIST,
            "Scores": DataType.LIST,
            "Metadata": DataType.LIST
        }

    def do_work(self, **kwargs):
        query = kwargs.get("Query") or self.properties.get("Query")
        limit = kwargs.get("Limit") or self.properties.get("Limit", 5)

        # Provider Flow Resolution
        db_provider_id = self.get_provider_id("Vector Database Provider")
        database = self.bridge.get(f"{db_provider_id}_Database") if db_provider_id else None
        
        emb_provider_id = self.get_provider_id("Embedding Provider")
        embedding_provider = self.bridge.get(f"{emb_provider_id}_Provider") if emb_provider_id else None

        if not database or not embedding_provider or not query:
            missing = []
            if not database: missing.append("Vector Database")
            if not embedding_provider: missing.append("Embedding Provider")
            if not query: missing.append("Query")
            self.logger.error(f"Missing inputs: {', '.join(missing)}")
            self.bridge.set(f"{self.node_id}_ActivePorts", ["Flow"], self.name)
            return True
            
        db = database.get("db")
        table_name = database.get("table")
        
        try:
            query_vec = embedding_provider.embed_query(str(query))
            docs, scores, metas = db.search(table_name, query_vec, limit=int(limit))
            
            self.bridge.set(f"{self.node_id}_Results", docs, self.name)
            self.bridge.set(f"{self.node_id}_Scores", scores, self.name)
            self.bridge.set(f"{self.node_id}_Metadata", metas, self.name)
            self.logger.info(f"Vector search returned {len(docs)} results.")
        except Exception as e:
            self.logger.error(f"Search Failed: {e}")
        
        self.bridge.set(f"{self.node_id}_ActivePorts", ["Flow"], self.name)
        return True

