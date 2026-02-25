from synapse.nodes.database.base import BaseSQLNode
from synapse.nodes.registry import NodeRegistry

class BaseSecurityActionNode(BaseSQLNode):
    """
    Base class for security operations like Login, User Management, etc.
    Strictly requires a 'Security Provider' context to execute.
    """
    def __init__(self, node_id, name, bridge):
        super().__init__(node_id, name, bridge)
        self.required_providers = ["Security Provider"]

    def get_security_pid(self):
        return self.get_provider_id("Security Provider")
