from synapse.core.types import DataType
from synapse.nodes.lib.provider_node import ProviderNode
from synapse.nodes.registry import NodeRegistry
from synapse.core.dependencies import DependencyManager

# Lazy import
lancedb = None
def ensure_lancedb():
    global lancedb
    if lancedb: return True
    if DependencyManager.ensure("lancedb"):
        import lancedb as _l; lancedb = _l; return True
    return False

class LanceDBVectorDatabase:
    def __init__(self, path):
        if ensure_lancedb():
            self.db = lancedb.connect(path)
        else:
            self.db = None
    
    def get_table(self, name):
        if self.db:
            return self.db.open_table(name)
        return None

@NodeRegistry.register("LanceDB", "AI/Vector")
class LanceDBNode(ProviderNode):
    """
    Service provider for LanceDB, a serverless, persistent vector database.
    Stores and retrieves embedded vectors directly from local disk.
    
    Inputs:
    - Flow: Start the LanceDB service and enter the vector scope.
    - Provider End: Close the database connection and exit the scope.
    - Storage Path: Directory path where the database files are stored.
    - Table Name: The specific collection/table to interact with.
    
    Outputs:
    - Provider Flow: Active while the database connection is open.
    - Provider ID: Unique ID for this specific provider instance.
    - Flow: Triggered when the service is stopped.
    """
    version = "2.1.0"

    def __init__(self, node_id, name, bridge):
        super().__init__(node_id, name, bridge)
        self.provider_type = "VECTOR"
        self.properties["Storage Path"] = "./data/vectors"
        self.properties["Table Name"] = "knowledge_base"
        self.define_schema()
        self.register_handlers()

    def define_schema(self):
        super().define_schema()
        self.input_schema["Storage Path"] = DataType.STRING
        self.input_schema["Table Name"] = DataType.STRING

    def start_scope(self, **kwargs):
        # Fallback with legacy support
        path = kwargs.get("Storage Path") or self.properties.get("StoragePath", self.properties.get("StoragePath"))
        table = kwargs.get("Table Name") or self.properties.get("TableName", self.properties.get("TableName"))
        
        if not ensure_lancedb():
            self.logger.error("LanceDB dependencies missing.")
            return super().start_scope(**kwargs)

        try:
            db = LanceDBVectorDatabase(path=path)
            self.bridge.set(f"{self.node_id}_Database", {"db": db, "table": table}, self.name)
            self.logger.info(f"Connected to LanceDB at {path} (Table: {table})")
            return super().start_scope(**kwargs)
        except Exception as e:
            self.logger.error(f"Failed to connect to LanceDB: {e}")
            return super().start_scope(**kwargs)

