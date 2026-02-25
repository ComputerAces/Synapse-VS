from synapse.nodes.registry import NodeRegistry
from synapse.core.types import DataType
from .base import BaseSecurityActionNode

@NodeRegistry.register("Update User", "Security/Actions")
class UpdateUserNode(BaseSecurityActionNode):
    """
    Modifies existing user data in the Security Provider's database using a dictionary of updates.
    
    Inputs:
    - Flow: Trigger the update process.
    - Username: The target user account to update.
    - Data: A dictionary containing the fields and new values (e.g., {"Password": "new_hash"}).
    
    Outputs:
    - Flow: Triggered after the update attempt.
    """
    version = "2.1.0"

    def __init__(self, node_id, name, bridge):
        super().__init__(node_id, name, bridge)
        self.define_schema()
        self.register_handlers()

    def register_handlers(self):
        self.register_handler("Flow", self.update_user)

    def define_schema(self):
        self.input_schema = {
            "Flow": DataType.FLOW,
            "Username": DataType.STRING,
            "Password": DataType.PASSWORD,
            "Email": DataType.STRING,
            "Roles": DataType.LIST,
            "Groups": DataType.LIST
        }
        self.output_schema = {
            "Flow": DataType.FLOW
        }

    def update_user(self, Username=None, **kwargs):
        # Fallback with legacy support
        Username = Username or kwargs.get("Username") or self.properties.get("Username")
        pid = self.get_security_pid()
        if not pid:
            self.logger.error("No Security Provider found.")
            self.bridge.set(f"{self.node_id}_ActivePorts", ["Flow"], self.name)
            return True
            
        Connection = self.bridge.get(f"{pid}_Connection")
        table = self.bridge.get(f"{pid}_Table Name") or "Users"

        updates = {}
        if kwargs.get("Password"): updates["Password"] = kwargs["Password"]
        if kwargs.get("Email"): updates["Email"] = kwargs["Email"]
        if kwargs.get("Roles"): updates["Roles"] = kwargs["Roles"]
        if kwargs.get("Groups"): updates["Groups"] = kwargs["Groups"]
        
        if not Username or not updates:
            self.logger.warning("No Username or updates provided.")
            self.bridge.set(f"{self.node_id}_ActivePorts", ["Flow"], self.name)
            return True
        
        try:
            conn = self.get_connection(Connection)
            cursor = conn.cursor()
            set_clauses = [f"[{k}] = ?" for k in updates.keys()]
            query = f"UPDATE [{table}] SET {', '.join(set_clauses)} WHERE Username = ?"
            params = list(updates.values()) + [Username]
            cursor.execute(query, params)
            conn.commit()
            conn.close()
            self.bridge.set(f"{self.node_id}_ActivePorts", ["Flow"], self.name)
        except Exception as e:
            self.logger.error(f"Error: {e}")
            self.bridge.set(f"{self.node_id}_ActivePorts", ["Flow"], self.name)
        return True
