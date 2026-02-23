from synapse.nodes.registry import NodeRegistry
from synapse.core.types import DataType
from .base import BaseSecurityActionNode

@NodeRegistry.register("Assign User to Group", "Security/Actions")
class AssignUserGroupNode(BaseSecurityActionNode):
    """
    Adds an individual user to a security group.
    The user will inherit all roles and permissions associated with that group.
    
    Inputs:
    - Flow: Trigger the group assignment.
    - Username: The target user's name.
    - Group Name: The name of the group to join.
    
    Outputs:
    - Flow: Triggered after the operation is attempted.
    - Success: True if the user was successfully added to the group.
    """
    version = "2.1.0"

    def __init__(self, node_id, name, bridge):
        super().__init__(node_id, name, bridge)
        self.define_schema()
        self.register_handlers()

    def register_handlers(self):
        self.register_handler("Flow", self.assign_group)

    def define_schema(self):
        self.input_schema = {
            "Flow": DataType.FLOW,
            "Username": DataType.STRING,
            "Group Name": DataType.STRING
        }
        self.output_schema = {
            "Flow": DataType.FLOW,
            "Success": DataType.BOOLEAN
        }

    def assign_group(self, Username=None, Group_Name=None, **kwargs):
        # Fallback with legacy support
        Username = Username or kwargs.get("Username") or self.properties.get("Username", self.properties.get("Username"))
        Group_Name = Group_Name or kwargs.get("Group Name") or self.properties.get("Group Name", self.properties.get("GroupName"))
        pid = self.get_security_pid()
        if not pid:
            self.logger.error("No Security Provider found.")
            self.bridge.set(f"{self.node_id}_ActivePorts", ["Flow"], self.name)
            return True
            
        Connection = self.bridge.get(f"{pid}_Connection")
        table = self.bridge.get(f"{pid}_Table Name") or "UserGroups"

        if not Username or not Group_Name:
            self.bridge.set(f"{self.node_id}_ActivePorts", ["Flow"], self.name)
            return True
        try:
            conn = self.get_connection(Connection)
            cursor = conn.cursor()
            cursor.execute(f"INSERT INTO {table} (Username, GroupName) VALUES (?, ?)", [Username, Group_Name])
            conn.commit()
            conn.close()
            self.bridge.set(f"{self.node_id}_Success", True, self.name)
        except Exception as e:
            self.logger.error(f"Error: {e}")
            self.bridge.set(f"{self.node_id}_Success", False, self.name)
        return True
