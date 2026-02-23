from synapse.nodes.registry import NodeRegistry
from synapse.core.types import DataType
from .base import BaseSecurityActionNode

@NodeRegistry.register("Set Password", "Security/Actions")
class SetPasswordNode(BaseSecurityActionNode):
    """
    Manually hashes a plaintext string into a secure SHA-256 password hash.
    Useful for preparing password data before passing it to 'Add User' or 'Update User'.
    
    Inputs:
    - Flow: Trigger the hashing process.
    - Plaintext: The raw string to be hashed.
    
    Outputs:
    - Flow: Triggered after hashing.
    - Password: The resulting hexadecimal hash string.
    """
    version = "2.1.0"

    def __init__(self, node_id, name, bridge):
        super().__init__(node_id, name, bridge)
        self.define_schema()
        self.register_handlers()

    def register_handlers(self):
        self.register_handler("Flow", self.hash_password)

    def define_schema(self):
        self.input_schema = {
            "Flow": DataType.FLOW,
            "Plaintext": DataType.STRING
        }
        self.output_schema = {
            "Flow": DataType.FLOW,
            "Password": DataType.PASSWORD
        }

    def hash_password(self, Plaintext=None, **kwargs):
        # Fallback with legacy support
        Plaintext = Plaintext or kwargs.get("Plaintext") or self.properties.get("Plaintext", self.properties.get("Plaintext"))
        import hashlib
        if not Plaintext:
            self.bridge.set(f"{self.node_id}_ActivePorts", ["Flow"], self.name)
            return True
            
        hashed = hashlib.sha256(str(Plaintext).encode()).hexdigest()
        self.bridge.set(f"{self.node_id}_Password", hashed, self.name)
        self.bridge.set(f"{self.node_id}_ActivePorts", ["Flow"], self.name)
        return True
