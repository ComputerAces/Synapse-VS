from synapse.nodes.registry import NodeRegistry
from synapse.core.types import DataType
from .base import BaseSecurityActionNode

@NodeRegistry.register("Add Role", "Security/Actions")
class AddRoleNode(BaseSecurityActionNode):
    """
    Defines a new security role with specific permissions in the Security Provider's database.
    Roles represent sets of capabilities that can be assigned to users or groups.
    
    Inputs:
    - Flow: Trigger the creation of the role.
    - Role Name: The unique identifier for the role.
    - Permissions: A list of permission strings (e.g., ["read", "write"]) to associate with this role.
    
    Outputs:
    - Flow: Triggered after the operation is attempted.
    - Success: True if the role was successfully created.
    """
    version = "2.1.0"

    def __init__(self, node_id, name, bridge):
        super().__init__(node_id, name, bridge)
        self.define_schema()
        self.register_handlers()

    def register_handlers(self):
        self.register_handler("Flow", self.add_role)

    def define_schema(self):
        self.input_schema = {
            "Flow": DataType.FLOW,
            "Role Name": DataType.STRING,
            "Permissions": DataType.LIST
        }
        self.output_schema = {
            "Flow": DataType.FLOW,
            "Success": DataType.BOOLEAN
        }

    def add_role(self, Role_Name=None, Permissions=None, **kwargs):
        # Fallback with legacy support
        Role_Name = Role_Name or kwargs.get("Role Name") or self.properties.get("Role Name", self.properties.get("RoleName"))
        Permissions = Permissions or kwargs.get("Permissions") or self.properties.get("Permissions", self.properties.get("Permissions", []))
        pid = self.get_security_pid()
        if not pid:
            self.logger.error("No Security Provider found.")
            self.bridge.set(f"{self.node_id}_ActivePorts", ["Flow"], self.name)
            return True
            
        Connection = self.bridge.get(f"{pid}_Connection")
        table = self.bridge.get(f"{pid}_Table Name") or "Roles"

        if not Role_Name:
            self.bridge.set(f"{self.node_id}_ActivePorts", ["Flow"], self.name)
            return True
        data = {"RoleName": Role_Name, "Permissions": str(Permissions or [])}
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
