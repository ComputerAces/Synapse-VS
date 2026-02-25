from synapse.nodes.registry import NodeRegistry
from synapse.core.types import DataType
from synapse.nodes.database.base import BaseSQLNode

@NodeRegistry.register("SQL Execute", "Database")
class SQLExecuteNode(BaseSQLNode):
    """
    Executes a non-query SQL command (e.g., CREATE TABLE, DROP) on the database.
    
    Inputs:
    - Flow: Execution trigger.
    - Command: The SQL statement to execute.
    
    Outputs:
    - Flow: Triggered after the command is executed.
    - Affected Rows: The number of rows affected by the command.
    """
    version = "2.1.0"

    def define_schema(self):
        self.input_schema = {
            "Flow": DataType.FLOW,
            "Command": DataType.STRING
        }
        self.output_schema = {
            "Flow": DataType.FLOW,
            "Affected Rows": DataType.INT
        }

    def register_handlers(self):
        self.register_handler("Flow", self.handle_execute)

    def handle_execute(self, Command=None, **kwargs):
        sql = Command if Command is not None else kwargs.get("Command") or self.properties.get("Command", "")
        
        if not sql:
            self.logger.warning("No SQL Command provided.")
            self.bridge.set(f"{self.node_id}_ActivePorts", ["Flow"], self.name)
            return True
            
        try:
            conn = self.get_connection(None) # Auto-resolves from provider
            cursor = conn.cursor()
            cursor.execute(sql)
            conn.commit()
            
            row_count = cursor.rowcount
            self.bridge.set(f"{self.node_id}_Affected Rows", row_count, self.name)
            self.logger.info(f"SQL command executed. Affected rows: {row_count}")
            # Do NOT close connection, BaseSQLNode manages it or it might be shared
            
            self.bridge.set(f"{self.node_id}_ActivePorts", ["Flow"], self.name)
            return
        except Exception as e:
            self.logger.error(f"Execute Error: {e}")
            self.bridge.set(f"{self.node_id}_ActivePorts", ["Flow"], self.name)
        return True

    def __init__(self, node_id, name, bridge):
        super().__init__(node_id, name, bridge)
        self.properties["Command"] = "INSERT INTO events (name) VALUES ('pulse')"
