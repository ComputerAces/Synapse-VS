from synapse.nodes.registry import NodeRegistry
from synapse.core.types import DataType
from .base import BaseSecurityActionNode

@NodeRegistry.register("Log Out", "Security/Actions")
class LogoutNode(BaseSecurityActionNode):
    """
    Terminates the current user session and clears authentication tokens.
    Used to securely exit an application scope.
    
    Inputs:
    - Flow: Trigger the logout process.
    
    Outputs:
    - Flow: Triggered after session data has been cleared.
    """
    version = "2.1.0"

    def __init__(self, node_id, name, bridge):
        super().__init__(node_id, name, bridge)
        self.define_schema()
        self.register_handlers()

    def register_handlers(self):
        self.register_handler("Flow", self.logout)

    def define_schema(self):
        self.input_schema = {
            "Flow": DataType.FLOW
        }
        self.output_schema = {
            "Flow": DataType.FLOW
        }

    def logout(self, **kwargs):
        pid = self.get_security_pid()
        if pid:
            self.bridge.set(f"{pid}_Token", None, self.name)
            self.bridge.set(f"{pid}_Authenticated", False, self.name)
            self.bridge.set(f"{pid}_Pending_Verify", None, self.name)
        
        self.bridge.set(f"{self.node_id}_ActivePorts", ["Flow"], self.name)
        return True
