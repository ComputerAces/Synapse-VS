from synapse.nodes.registry import NodeRegistry
from synapse.core.types import DataType
from synapse.nodes.database.base import BaseSQLNode

@NodeRegistry.register("SQL Select", "Database")
class SQLSelectNode(BaseSQLNode):
    """
    Executes a SELECT query on a database table and returns matching rows.
    
    Inputs:
    - Flow: Execution trigger.
    - Table: Name of the table to select from.
    - Filters: Dictionary of column values to filter by (e.g., {"id": 1}).
    
    Outputs:
    - Flow: Triggered after data is retrieved.
    - Rows: List of matching records as dictionaries.
    - Count: The number of rows returned.
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
            "Rows": DataType.LIST,
            "Count": DataType.INT
        }

    def register_handlers(self):
        self.register_handler("Flow", self.handle_select)

    def handle_select(self, Table=None, Filters=None, **kwargs):
        table = Table if Table is not None else kwargs.get("Table") or self.properties.get("Table", "")
        
        if not table:
            self.logger.error("Table required for SQL Select.")
            self.bridge.set(f"{self.node_id}_ActivePorts", ["Flow"], self.name)
            return True

        query = f"SELECT * FROM [{table}]"
        params = []
        if Filters:
            where_clauses = []
            for k, v in Filters.items():
                where_clauses.append(f"[{k}] = ?")
                params.append(v)
            query += " WHERE " + " AND ".join(where_clauses)

        try:
            conn = self.get_connection(None) # Auto-resolves from provider
            cursor = conn.cursor()
            cursor.execute(query, params)
            
            columns = [column[0] for column in cursor.description]
            results = [dict(zip(columns, row)) for row in cursor.fetchall()]
            
            self.bridge.set(f"{self.node_id}_Rows", results, self.name)
            self.bridge.set(f"{self.node_id}_Count", len(results), self.name)
            self.logger.info(f"Selected {len(results)} rows from '{table}'")
            
            self.bridge.set(f"{self.node_id}_ActivePorts", ["Flow"], self.name)
            return True
        except Exception as e:
            self.logger.error(f"Select Error: {e}")
            self.bridge.set(f"{self.node_id}_ActivePorts", ["Flow"], self.name)
        return True

    def __init__(self, node_id, name, bridge):
        super().__init__(node_id, name, bridge)
        self.properties["Table"] = ""
