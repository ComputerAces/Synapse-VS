from synapse.nodes.registry import NodeRegistry
from synapse.core.types import DataType
from .base import BaseSecurityActionNode

@NodeRegistry.register("Add User", "Security/Actions")
class AddUserNode(BaseSecurityActionNode):
    """
    Registers a new user account in the connected Security Provider's database.
    This creates the primary identity record used for authentication and authorization.
    
    Inputs:
    - Flow: Trigger the user creation process.
    - Username: The unique login name for the user.
    - Password: The user's secret password (should be hashed before storage if possible).
    - Groups: An optional list of groups to immediately assign the user to.
    
    Outputs:
    - Flow: Triggered after the account creation attempt.
    - Success: True if the user was successfully registered.
    """
    version = "2.1.0"
    
    def __init__(self, node_id, name, bridge):
        super().__init__(node_id, name, bridge)
        self.define_schema()
        self.register_handlers()

    def register_handlers(self):
        self.register_handler("Flow", self.add_user)

    def define_schema(self):
        self.input_schema = {
            "Flow": DataType.FLOW,
            "Username": DataType.STRING,
            "Password": DataType.PASSWORD,
            "Groups": DataType.LIST
        }
        self.output_schema = {
            "Flow": DataType.FLOW,
            "Success": DataType.BOOLEAN
        }

    def add_user(self, Username=None, Password=None, Groups=None, **kwargs):
        # Fallback with legacy support
        Username = Username or kwargs.get("Username") or self.properties.get("Username", self.properties.get("Username"))
        Password = Password or kwargs.get("Password") or self.properties.get("Password", self.properties.get("Password"))
        Groups = Groups or kwargs.get("Groups") or self.properties.get("Groups", self.properties.get("Groups", []))

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
        data = {"Username": Username, "Password": Password, "Groups": str(Groups)}
        
        try:
            conn = self.get_connection(Connection)
            cursor = conn.cursor()
            cols = ", ".join([f"[{k}]" for k in data.keys()])
            placeholders = ", ".join(["?"] * len(data))
            cursor.execute(f"INSERT INTO {table} ({cols}) VALUES ({placeholders})", list(data.values()))
            conn.commit()
            conn.close()
            self.bridge.set(f"{self.node_id}_Success", True, self.name)
        except Exception as e:
            self.logger.error(f"Error: {e}")
            self.bridge.set(f"{self.node_id}_Success", False, self.name)
        return True
