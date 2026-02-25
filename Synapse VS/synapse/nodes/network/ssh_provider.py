from synapse.nodes.registry import NodeRegistry
from synapse.nodes.lib.provider_node import ProviderNode
from synapse.core.types import DataType

@NodeRegistry.register("SSH Provider", "Network/SSH")
class SSHProviderNode(ProviderNode):
    """
    Service provider for SSH (Secure Shell) connections.
    Registers connection parameters in a scope for child nodes like 
    SSH Command and SFTP Transfer to discover and use.
    
    Inputs:
    - Flow: Start the SSH provider service and enter the connection scope.
    - Host: The remote hostname or IP address (default: 127.0.0.1).
    - Port: The SSH port (default: 22).
    - User: The username for authentication.
    - Password: The password for authentication.
    - Key Path: Path to a private key file for key-based authentication.
    
    Outputs:
    - Provider Flow: Active while the connection scope is open.
    - Flow: Triggered when the service is stopped.
    """
    version = "2.1.0"

    def __init__(self, node_id, name, bridge):
        super().__init__(node_id, name, bridge)
        self.provider_type = "SSH Provider"
        self.hidden_ports = []
        self.properties["Host"] = "127.0.0.1"
        self.properties["Port"] = 22
        self.properties["User"] = "root"
        self.properties["Password"] = ""
        self.properties["Key Path"] = ""

    def define_schema(self):
        super().define_schema()
        # Add SSH Specific Inputs
        self.input_schema["Host"] = DataType.STRING
        self.input_schema["Port"] = DataType.NUMBER
        self.input_schema["User"] = DataType.STRING
        self.input_schema["Password"] = DataType.PASSWORD
        self.input_schema["Key Path"] = DataType.STRING

    def register_provider_context(self):
        self.bridge.set(f"{self.node_id}_Host", self.properties.get("Host"), self.name)
        self.bridge.set(f"{self.node_id}_Port", self.properties.get("Port", 22), self.name)
        self.bridge.set(f"{self.node_id}_User", self.properties.get("User"), self.name)
        self.bridge.set(f"{self.node_id}_Password", self.properties.get("Password"), self.name)
        self.bridge.set(f"{self.node_id}_Key Path", self.properties.get("Key Path"), self.name)

    def execute(self, **kwargs):
        return super().execute(**kwargs)
