from synapse.core.super_node import SuperNode
from synapse.nodes.registry import NodeRegistry
from synapse.core.types import DataType

@NodeRegistry.register("Add Documents", "AI/Vector")
class AddDocumentsNode(SuperNode):
    """
    Indexes text documents into a connected Vector Database Provider.
    Requires an Embedding Provider to generate vectors for the documents.
    
    ### Inputs:
    - Flow (flow): Trigger execution.
    - Documents (list): A list of text strings (or a single string) to be indexed.
    - Metadata (list): Optional list of dictionaries containing metadata for each document.
    
    ### Outputs:
    - Flow (flow): Triggered after indexing is complete.
    - Success (boolean): True if the documents were successfully added, False otherwise.
    """
    version = "2.1.0"

    def __init__(self, node_id, name, bridge):
        super().__init__(node_id, name, bridge)
        self.required_providers = ["VECTOR", "EMBED"]
        self.is_native = True
        self.define_schema()
        self.register_handlers()

    def register_handlers(self):
        self.register_handler("Flow", self.do_work)

    def define_schema(self):
        self.input_schema = {
            "Flow": DataType.FLOW,
            "Documents": DataType.LIST,
            "Metadata": DataType.LIST
        }
        self.output_schema = {
            "Flow": DataType.FLOW,
            "Success": DataType.BOOLEAN
        }

    def do_work(self, **kwargs):
        documents = kwargs.get("Documents") or self.properties.get("Documents", [])
        metadata = kwargs.get("Metadata") or self.properties.get("Metadata", [])
        
        if isinstance(documents, str):
            documents = [documents]
            
        # Resolved via Provider Flow
        db_provider_id = self.get_provider_id("Vector Database Provider")
        database = self.bridge.get(f"{db_provider_id}_Database") if db_provider_id else None
        
        emb_provider_id = self.get_provider_id("Embedding Provider")
        embedding_provider = self.bridge.get(f"{emb_provider_id}_Provider") if emb_provider_id else None

        if not database or not embedding_provider or not documents:
            missing = []
            if not database: missing.append("Vector Database")
            if not embedding_provider: missing.append("Embedding Provider")
            if not documents: missing.append("Documents")
            raise RuntimeError(f"[{self.name}] Missing required inputs or providers: {', '.join(missing)}")

        db = database.get("db")
        table_name = database.get("table")

        try:
            embeddings = embedding_provider.embed_documents(documents)
            count = db.add(table_name, documents, embeddings, metadata=metadata)
            self.logger.info(f"Indexed {count} documents into '{table_name}'.")
            self.bridge.set(f"{self.node_id}_Success", True, self.name)
        except Exception as e:
            self.logger.error(f"Failed to add documents: {e}")
            self.bridge.set(f"{self.node_id}_Success", False, self.name)
            
        self.bridge.set(f"{self.node_id}_ActivePorts", ["Flow"], self.name)
        return True

