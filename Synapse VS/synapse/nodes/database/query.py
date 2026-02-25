from synapse.nodes.registry import NodeRegistry
from synapse.core.types import DataType
from synapse.nodes.database.base import BaseSQLNode

@NodeRegistry.register("SQL Query", "Database")
class SQLQueryNode(BaseSQLNode):
    """
    Executes a custom SQL query and returns the results as a list of dictionaries.
    
    Inputs:
    - Flow: Execution trigger.
    - Query: The SQL SELECT statement to execute.
    
    Outputs:
    - Flow: Triggered after the query is complete.
    - Rows: List of records returned by the query.
    - Count: The number of rows returned.
    """
    version = "2.1.0"

    def define_schema(self):
        self.input_schema = {
            "Flow": DataType.FLOW,
            "Query": DataType.STRING
        }
        self.output_schema = {
            "Flow": DataType.FLOW,
            "Rows": DataType.LIST,
            "Count": DataType.INT
        }

    def register_handlers(self):
        self.register_handler("Flow", self.handle_query)

    def handle_query(self, Query=None, **kwargs):
        sql = Query if Query is not None else kwargs.get("Query") or self.properties.get("Query", "SELECT * FROM users")
        
        if not sql:
            self.logger.warning("No SQL Query provided.")
            self.bridge.set(f"{self.node_id}_ActivePorts", ["Flow"], self.name)
            return True
        
        try:
            conn = self.get_connection(None) # Auto-resolves from provider
            cursor = conn.cursor()
            cursor.execute(sql)
            
            results = []
            if cursor.description:
                columns = [column[0] for column in cursor.description]
                for row in cursor.fetchall():
                    results.append(dict(zip(columns, row)))
            
            self.bridge.set(f"{self.node_id}_Rows", results, self.name)
            self.bridge.set(f"{self.node_id}_Count", len(results), self.name)
            self.logger.info(f"Query returned {len(results)} rows.")
            
            self.bridge.set(f"{self.node_id}_ActivePorts", ["Flow"], self.name)
            return
        except Exception as e:
            self.logger.error(f"Query Error: {e}")
            self.bridge.set(f"{self.node_id}_ActivePorts", ["Flow"], self.name)
        return True

    def __init__(self, node_id, name, bridge):
        super().__init__(node_id, name, bridge)
        self.properties["Query"] = "SELECT * FROM users"
