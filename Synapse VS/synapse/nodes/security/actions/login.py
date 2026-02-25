import time
from synapse.nodes.registry import NodeRegistry
from synapse.core.types import DataType
from .base import BaseSecurityActionNode

@NodeRegistry.register("Log In", "Security/Actions")
class LoginNode(BaseSecurityActionNode):
    """
    Authenticates a user against the Security Provider's database.
    If successful, it establishes a user session and updates the active User Provider.
    
    Inputs:
    - Flow: Trigger the authentication process.
    - Username: The user's login name.
    - Password: The secret password to verify.
    
    Outputs:
    - Flow: Standard execution trigger (executed ONLY upon successful authentication).
    - Error Flow: Pulse triggered if authentication fails or an error occurs.
    - Authenticated: Boolean status of the login attempt.
    """
    version = "2.1.0"

    def __init__(self, node_id, name, bridge):
        super().__init__(node_id, name, bridge)
        self.define_schema()
        self.register_handlers()

    def register_handlers(self):
        self.register_handler("Flow", self.login)

    def define_schema(self):
        self.input_schema = {
            "Flow": DataType.FLOW,
            "Username": DataType.STRING,
            "Password": DataType.PASSWORD
        }
        self.output_schema = {
            "Flow": DataType.FLOW,
            "Error Flow": DataType.FLOW,
            "Authenticated": DataType.BOOLEAN
        }

    def login(self, Username=None, Password=None, **kwargs):
        # Fallback with legacy support
        Username = Username or kwargs.get("Username") or self.properties.get("Username", self.properties.get("Username"))
        # Password usually not stored in properties for security, but can be
        Password = Password or kwargs.get("Password") or self.properties.get("Password", self.properties.get("Password"))

        pid = self.get_security_pid()
        if not pid:
            self.logger.error("No Security Provider found.")
            return

        if not Username:
            self.logger.warning("Login attempt with empty username.")
            self.bridge.set(f"{self.node_id}_ActivePorts", ["Error Flow"], self.name)
            return True

        Connection = self.bridge.get(f"{pid}_Connection")
        table = self.bridge.get(f"{pid}_Table Name") or "Users"
        
        try:
            conn = self.get_connection(Connection)
            cursor = conn.cursor()
            
            # Basic SQL injection check? Parameterized query handles it.
            query = f"SELECT * FROM {table} WHERE Username = ? AND Password = ?"
            cursor.execute(query, [Username, Password])
            user_record = cursor.fetchone()
            
            if user_record:
                use_verify = self.bridge.get(f"{pid}_Use Verify")
                
                if use_verify:
                    self.bridge.set(f"{pid}_Authenticated", False, self.name)
                    self.bridge.set(f"{pid}_Pending_Verify", Username, self.name)
                    self.bridge.set(f"{self.node_id}_Authenticated", True, self.name)
                    self.bridge.set(f"{self.node_id}_ActivePorts", ["Flow"], self.name)
                else:
                    token = f"TOKEN_{pid}_{int(time.time())}"
                    self.bridge.set(f"{pid}_Token", token, self.name)
                    self.bridge.set(f"{pid}_Authenticated", True, self.name)
                    
                    # Update User Provider
                    up_id = self.get_provider_id("User Provider")
                    if up_id:
                        up_node = self.bridge.get(up_id)
                        if up_node and hasattr(up_node, "set_user"):
                            groups = ["Default"]
                            try:
                                if "Groups" in user_record.keys():
                                    groups = eval(user_record["Groups"])
                            except: pass
                            up_node.set_user(Username, roles=["User"], groups=groups)

                    self.bridge.set(f"{self.node_id}_Authenticated", True, self.name)
                    self.bridge.set(f"{self.node_id}_ActivePorts", ["Flow"], self.name)
                    return True
            else:
                self.bridge.set(f"{pid}_Authenticated", False, self.name)
                self.bridge.set(f"{self.node_id}_Authenticated", False, self.name)
                self.bridge.set(f"{self.node_id}_ActivePorts", ["Error Flow"], self.name)
                return True
                
        except Exception as e:
            self.logger.error(f"Error: {e}")
            self.bridge.set(f"{self.node_id}_ActivePorts", ["Error Flow"], self.name)
        return True
