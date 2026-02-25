from synapse.nodes.registry import NodeRegistry
from synapse.core.types import DataType
from .base import BaseSecurityActionNode

@NodeRegistry.register("Register", "Security/Actions")
class RegisterNode(BaseSecurityActionNode):
    """
    Handles self-service user registration with password confirmation.
    Checks for existing usernames before creating a new record.
    
    Inputs:
    - Flow: Trigger the registration workflow.
    - Username: The desired login name.
    - Password: The primary password entry.
    - Confirm Password: Must match the Password input to succeed.
    
    Outputs:
    - Flow: Triggered after the registration attempt.
    - Success: True if the account was created successfully.
    """
    version = "2.1.0"

    def __init__(self, node_id, name, bridge):
        super().__init__(node_id, name, bridge)
        self.define_schema()
        self.register_handlers()

    def register_handlers(self):
        self.register_handler("Flow", self.register_user)

    def define_schema(self):
        self.input_schema = {
            "Flow": DataType.FLOW,
            "Username": DataType.STRING,
            "Password": DataType.PASSWORD,
            "Confirm Password": DataType.PASSWORD
        }
        self.output_schema = {
            "Flow": DataType.FLOW,
            "Success": DataType.BOOLEAN
        }

    def register_user(self, Username=None, Password=None, Confirm_Password=None, **kwargs):
        # Fallback with legacy support
        Username = Username or kwargs.get("Username") or self.properties.get("Username", self.properties.get("Username"))
        Password = Password or kwargs.get("Password") or self.properties.get("Password", self.properties.get("Password"))
        
        if not Username or not Password:
            self.bridge.set(f"{self.node_id}_ActivePorts", ["Flow"], self.name)
            return True
        if Password != Confirm_Password:
            self.bridge.set(f"{self.node_id}_Success", False, self.name)
            self.bridge.set(f"{self.node_id}_ActivePorts", ["Flow"], self.name)
            return True
        pid = self.get_security_pid()
        if not pid:
            self.bridge.set(f"{self.node_id}_ActivePorts", ["Flow"], self.name)
            return True

        Connection = self.bridge.get(f"{pid}_Connection")
        table = self.bridge.get(f"{pid}_Table Name") or "Users"

        try:
            conn = self.get_connection(Connection)
            cursor = conn.cursor()
            
            cursor.execute(f"SELECT Username FROM {table} WHERE Username = ?", [Username])
            if cursor.fetchone():
                self.bridge.set(f"{self.node_id}_Success", False, self.name)
            else:
                cursor.execute(f"INSERT INTO {table} (Username, Password, Groups) VALUES (?, ?, ?)", 
                               [Username, Password, "['Default']"])
                conn.commit()
                self.bridge.set(f"{self.node_id}_Success", True, self.name)
            
            self.bridge.set(f"{self.node_id}_ActivePorts", ["Flow"], self.name)
        except Exception as e:
            self.logger.error(f"Error: {e}")
            self.bridge.set(f"{self.node_id}_Success", False, self.name)
            self.bridge.set(f"{self.node_id}_ActivePorts", ["Flow"], self.name)
        return True
