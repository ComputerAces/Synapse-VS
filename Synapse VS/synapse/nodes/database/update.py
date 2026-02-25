from synapse.nodes.registry import NodeRegistry
from synapse.core.types import DataType
from synapse.nodes.database.base import BaseSQLNode

@NodeRegistry.register("SQL Update", "Database")
class SQLUpdateNode(BaseSQLNode):
    """
    Updates existing records in a database table.
    
    Inputs:
    - Flow: Execution trigger.
    - Table: Name of the table to update.
    - Data: Dictionary of column-value pairs to set.
    - Filters: Dictionary of column values to match for the update.
    
    Outputs:
    - Flow: Triggered after the update is complete.
    - Affected Rows: The number of rows updated.
    """
    version = "2.1.0"

    def define_schema(self):
        self.input_schema = {
            "Flow": DataType.FLOW,
            "Table": DataType.STRING,
            "Data": DataType.DICT,
            "Filters": DataType.DICT
        }
        self.output_schema = {
            "Flow": DataType.FLOW,
            "Affected Rows": DataType.INT
        }

    def register_handlers(self):
        self.register_handler("Flow", self.handle_update)

    def handle_update(self, Table=None, Data=None, Filters=None, **kwargs):
        table = Table if Table is not None else kwargs.get("Table") or self.properties.get("Table", "")
        
        if not table or not Data:
            self.logger.error("Table and Data required for SQL Update.")
            self.bridge.set(f"{self.node_id}_ActivePorts", ["Flow"], self.name)
            return True

        set_clauses = [f"[{k}] = ?" for k in Data.keys()]
        query = f"UPDATE [{table}] SET {', '.join(set_clauses)}"
        params = list(Data.values())

        if Filters:
            where_clauses = [f"[{k}] = ?" for k in Filters.keys()]
            query += " WHERE " + " AND ".join(where_clauses)
            params.extend(list(Filters.values()))

        try:
            conn = self.get_connection(None) # Auto-resolves from provider
            cursor = conn.cursor()
            cursor.execute(query, params)
            conn.commit()
            
            row_count = cursor.rowcount
            self.bridge.set(f"{self.node_id}_Affected Rows", row_count, self.name)
            self.logger.info(f"Updated {row_count} rows in '{table}'")
            
            self.bridge.set(f"{self.node_id}_ActivePorts", ["Flow"], self.name)
            return True
        except Exception as e:
            self.logger.error(f"Update Error: {e}")
            self.bridge.set(f"{self.node_id}_ActivePorts", ["Flow"], self.name)
        return True

    def __init__(self, node_id, name, bridge):
        super().__init__(node_id, name, bridge)
        self.properties["Table"] = ""
