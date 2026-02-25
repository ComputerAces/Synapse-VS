from synapse.nodes.registry import NodeRegistry
from synapse.core.types import DataType
from .base import BaseSecurityActionNode

@NodeRegistry.register("Remove User", "Security/Actions")
class RemoveUserNode(BaseSecurityActionNode):
    """
    Permanently deletes a user account from the connected Security Provider's database.
    
    Inputs:
    - Flow: Trigger the deletion.
    - Username: The name of the user account to remove.
    
    Outputs:
    - Flow: Triggered after the deletion is attempted.
    - Success: True if the user was successfully removed.
    """
    version = "2.1.0"

    def __init__(self, node_id, name, bridge):
        super().__init__(node_id, name, bridge)
        self.define_schema()
        self.register_handlers()

    def register_handlers(self):
        self.register_handler("Flow", self.remove_user)

    def define_schema(self):
        self.input_schema = {
            "Flow": DataType.FLOW,
            "Username": DataType.STRING
        }
        self.output_schema = {
            "Flow": DataType.FLOW,
            "Error Flow": DataType.FLOW
        }

    def remove_user(self, Username=None, **kwargs):
        # Fallback with legacy support
        Username = Username or kwargs.get("Username") or self.properties.get("Username", self.properties.get("Username"))
        pid = self.get_security_pid()
        if not pid:
            self.logger.error("No Security Provider found.")
            self.bridge.set(f"{self.node_id}_ActivePorts", ["Flow"], self.name)
            return True
            
        Connection = self.bridge.get(f"{pid}_Connection")
        table = self.bridge.get(f"{pid}_Table Name") or "Users"

        if not Username:
            self.bridge.set(f"{self.node_id}_ActivePorts", ["Flow"], self.name)
            return True
        
        try:
            conn = self.get_connection(Connection)
            cursor = conn.cursor()
            cursor.execute(f"DELETE FROM [{table}] WHERE Username = ?", [Username])
            conn.commit()
            conn.close()
        except Exception as e:
            self.logger.error(f"Error: {e}")
            self.bridge.set(f"{self.node_id}_ActivePorts", ["Error Flow", "Flow"], self.name)
            return True

        self.bridge.set(f"{self.node_id}_ActivePorts", ["Flow"], self.name)
        return True
