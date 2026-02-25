from synapse.nodes.registry import NodeRegistry
from synapse.core.types import DataType
from .base import BaseSecurityActionNode

@NodeRegistry.register("Add Group", "Security/Actions")
class AddGroupNode(BaseSecurityActionNode):
    """
    Creates a new security group within the connected Security Provider's database.
    Groups are used to organize users for bulk permission management.
    
    Inputs:
    - Flow: Trigger the creation of the group.
    - Group Name: The unique name for the new group.
    
    Outputs:
    - Flow: Triggered after the operation is attempted.
    - Success: True if the group was successfully created, False if it already exists or an error occurred.
    """
    version = "2.1.0"

    def __init__(self, node_id, name, bridge):
        super().__init__(node_id, name, bridge)
        self.define_schema()
        self.register_handlers()

    def register_handlers(self):
        self.register_handler("Flow", self.add_group)

    def define_schema(self):
        self.input_schema = {
            "Flow": DataType.FLOW,
            "Group Name": DataType.STRING
        }
        self.output_schema = {
            "Flow": DataType.FLOW,
            "Success": DataType.BOOLEAN
        }

    def add_group(self, Group_Name=None, **kwargs):
        # Fallback with legacy support
        Group_Name = Group_Name or kwargs.get("Group Name") or self.properties.get("Group Name", self.properties.get("GroupName"))
        pid = self.get_security_pid()
        if not pid:
            self.logger.error("No Security Provider found.")
            self.bridge.set(f"{self.node_id}_ActivePorts", ["Flow"], self.name)
            return True
            
        Connection = self.bridge.get(f"{pid}_Connection")
        table = self.bridge.get(f"{pid}_Table Name") or "Groups"

        if not Group_Name:
            self.bridge.set(f"{self.node_id}_ActivePorts", ["Flow"], self.name)
            return True
        try:
            conn = self.get_connection(Connection)
            cursor = conn.cursor()
            cursor.execute(f"INSERT INTO {table} (GroupName) VALUES (?)", [Group_Name])
            conn.commit()
            conn.close()
            self.bridge.set(f"{self.node_id}_Success", True, self.name)
        except Exception as e:
            self.logger.error(f"Error: {e}")
            self.bridge.set(f"{self.node_id}_Success", False, self.name)
        return True
