from synapse.nodes.registry import NodeRegistry
from synapse.core.types import DataType
from .base import BaseSecurityActionNode

@NodeRegistry.register("Assign Group to Role", "Security/Actions")
class AssignGroupRoleNode(BaseSecurityActionNode):
    """
    Links a security group to a specific role, granting all group members the role's permissions.
    This is the primary method for bulk authorization management.
    
    Inputs:
    - Flow: Trigger the assignment.
    - Group Name: The target group name.
    - Role Name: The role to be assigned to the group.
    
    Outputs:
    - Flow: Triggered after the assignment is attempted.
    - Success: True if the relationship was successfully recorded.
    """
    version = "2.1.0"

    def __init__(self, node_id, name, bridge):
        super().__init__(node_id, name, bridge)
        self.define_schema()
        self.register_handlers()

    def register_handlers(self):
        self.register_handler("Flow", self.assign_role)

    def define_schema(self):
        self.input_schema = {
            "Flow": DataType.FLOW,
            "Group Name": DataType.STRING,
            "Role Name": DataType.STRING
        }
        self.output_schema = {
            "Flow": DataType.FLOW,
            "Success": DataType.BOOLEAN
        }

    def assign_role(self, Group_Name=None, Role_Name=None, **kwargs):
        # Fallback with legacy support
        Group_Name = Group_Name or kwargs.get("Group Name") or self.properties.get("Group Name", self.properties.get("GroupName"))
        Role_Name = Role_Name or kwargs.get("Role Name") or self.properties.get("Role Name", self.properties.get("RoleName"))
        pid = self.get_security_pid()
        if not pid:
            self.logger.error("No Security Provider found.")
            self.bridge.set(f"{self.node_id}_ActivePorts", ["Flow"], self.name)
            return True
            
        Connection = self.bridge.get(f"{pid}_Connection")
        table = self.bridge.get(f"{pid}_Table Name") or "GroupRoles"

        if not Group_Name or not Role_Name:
            self.bridge.set(f"{self.node_id}_ActivePorts", ["Flow"], self.name)
            return True
        try:
            conn = self.get_connection(Connection)
            cursor = conn.cursor()
            cursor.execute(f"INSERT INTO {table} (GroupName, RoleName) VALUES (?, ?)", [Group_Name, Role_Name])
            conn.commit()
            conn.close()
            self.bridge.set(f"{self.node_id}_Success", True, self.name)
        except Exception as e:
            self.logger.error(f"Error: {e}")
            self.bridge.set(f"{self.node_id}_Success", False, self.name)
        return True
