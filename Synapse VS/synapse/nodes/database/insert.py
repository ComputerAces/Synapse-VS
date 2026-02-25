from synapse.nodes.registry import NodeRegistry
from synapse.core.types import DataType
from synapse.nodes.database.base import BaseSQLNode

@NodeRegistry.register("SQL Insert", "Database")
class SQLInsertNode(BaseSQLNode):
    """
    Inserts a new record into a database table using a dictionary of data.
    
    Inputs:
    - Flow: Execution trigger.
    - Table: Name of the table to insert into.
    - Data: Dictionary of column-value pairs to insert.
    
    Outputs:
    - Flow: Triggered after the insertion is complete.
    - Affected Rows: The number of rows inserted (typically 1).
    """
    version = "2.1.0"

    def define_schema(self):
        self.input_schema = {
            "Flow": DataType.FLOW,
            "Table": DataType.STRING,
            "Data": DataType.DICT
        }
        self.output_schema = {
            "Flow": DataType.FLOW,
            "Affected Rows": DataType.INT
        }

    def register_handlers(self):
        self.register_handler("Flow", self.handle_insert)

    def handle_insert(self, Table=None, Data=None, **kwargs):
        table = Table if Table is not None else kwargs.get("Table") or self.properties.get("Table", "")
        
        if not table or not Data:
            self.logger.error("Table and Data required for SQL Insert.")
            self.bridge.set(f"{self.node_id}_ActivePorts", ["Flow"], self.name)
            return True

        # Prepare Query
        # Note: Using [] for column escaping is standard across many SQL dialects in Synapse
        cols = ", ".join([f"[{k}]" for k in Data.keys()])
        placeholders = ", ".join(["?"] * len(Data))
        query = f"INSERT INTO [{table}] ({cols}) VALUES ({placeholders})"
        params = list(Data.values())

        try:
            conn = self.get_connection(None) # Auto-resolves from provider
            cursor = conn.cursor()
            cursor.execute(query, params)
            conn.commit()
            
            row_count = cursor.rowcount
            self.bridge.set(f"{self.node_id}_Affected Rows", row_count, self.name)
            self.logger.info(f"Inserted record into '{table}'")
            
            self.bridge.set(f"{self.node_id}_ActivePorts", ["Flow"], self.name)
            return True
        except Exception as e:
            self.logger.error(f"Insert Error: {e}")
            self.bridge.set(f"{self.node_id}_ActivePorts", ["Flow"], self.name)
        return True

    def __init__(self, node_id, name, bridge):
        super().__init__(node_id, name, bridge)
        self.properties["Table"] = ""
