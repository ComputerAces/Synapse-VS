from synapse.nodes.registry import NodeRegistry
from synapse.core.types import DataType
from synapse.nodes.database.base import BaseSQLNode

@NodeRegistry.register("SQL Delete", "Database")
class SQLDeleteNode(BaseSQLNode):
    """
    Deletes rows from a database table based on specified filters.
    
    Inputs:
    - Flow: Execution trigger.
    - Table: Name of the table to delete from.
    - Filters: Dictionary of column values to match for deletion.
    
    Outputs:
    - Flow: Triggered after the deletion is complete.
    - Affected Rows: The number of rows deleted.
    """
    version = "2.1.0"

    def define_schema(self):
        self.input_schema = {
            "Flow": DataType.FLOW,
            "Table": DataType.STRING,
            "Filters": DataType.DICT
        }
        self.output_schema = {
            "Flow": DataType.FLOW,
            "Affected Rows": DataType.INT
        }

    def register_handlers(self):
        self.register_handler("Flow", self.handle_delete)

    def handle_delete(self, Table=None, Filters=None, **kwargs):
        table = Table if Table is not None else kwargs.get("Table") or self.properties.get("Table", "")
        
        if not table:
            self.logger.error("Table required for SQL Delete.")
            self.bridge.set(f"{self.node_id}_ActivePorts", ["Flow"], self.name)
            return True

        query = f"DELETE FROM [{table}]"
        params = []
        if Filters:
            where_clauses = [f"[{k}] = ?" for k in Filters.keys()]
            query += " WHERE " + " AND ".join(where_clauses)
            params = list(Filters.values())

        try:
            conn = self.get_connection(None) # Auto-resolves from provider
            cursor = conn.cursor()
            cursor.execute(query, params)
            conn.commit()
            
            row_count = cursor.rowcount
            self.bridge.set(f"{self.node_id}_Affected Rows", row_count, self.name)
            self.logger.info(f"Deleted {cursor.rowcount} rows from '{table}'")
            
            self.bridge.set(f"{self.node_id}_ActivePorts", ["Flow"], self.name)
            return True
        except Exception as e:
            self.logger.error(f"Delete Error: {e}")
            self.bridge.set(f"{self.node_id}_ActivePorts", ["Flow"], self.name)
        return True

    def __init__(self, node_id, name, bridge):
        super().__init__(node_id, name, bridge)
        self.properties["Table"] = ""
