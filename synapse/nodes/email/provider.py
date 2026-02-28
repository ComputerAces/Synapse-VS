from synapse.nodes.registry import NodeRegistry
from synapse.core.types import DataType
from synapse.nodes.lib.provider_node import ProviderNode

@NodeRegistry.register("Email Provider", "Network/Email")
class EmailProviderNode(ProviderNode):
    """
    Provides SMTP server configuration for sending emails.
    
    Inputs:
    - Flow: Execution trigger.
    - Host: SMTP server hostname (e.g., smtp.gmail.com).
    - User: Username for authentication.
    - Password: Password for authentication.
    - Port: Connection port (default 465).
    
    Outputs:
    - Flow: Triggered when the provider is initialized.
    """
    version = "2.1.0"

    def __init__(self, node_id, name, bridge):
        super().__init__(node_id, name, bridge)
        self.provider_type = "Email Provider"
        self.properties["Host"] = "smtp.gmail.com"
        self.properties["User"] = "user@example.com"
        self.properties["Password"] = ""
        self.properties["Port"] = 465
        
        self.define_schema()
        # ProviderNode handles handlers

    def define_schema(self):
        super().define_schema()
        self.input_schema.update({
            "Host": DataType.STRING,
            "User": DataType.STRING,
            "Password": DataType.STRING,
            "Port": DataType.NUMBER
        })

    def register_provider_context(self):
        host = self.properties.get("Host", "smtp.gmail.com")
        user = self.properties.get("User", "user@example.com")
        pw = self.properties.get("Password", "")
        port = self.properties.get("Port", 465)

        self.bridge.set(f"{self.node_id}_Host", host, self.name)
        self.bridge.set(f"{self.node_id}_User", user, self.name)
        self.bridge.set(f"{self.node_id}_Password", pw, self.name)
        self.bridge.set(f"{self.node_id}_Port", port, self.name)
        return self.provider_type
