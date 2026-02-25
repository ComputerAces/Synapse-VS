from synapse.nodes.lib.provider_node import ProviderNode

class SecurityProviderNode(ProviderNode):
    """
    Base class for all security-related provider nodes.
    Defines the standard 'Security Provider' type and handling.
    """
    def __init__(self, node_id, name, bridge):
        super().__init__(node_id, name, bridge)
        self.provider_type = "Security Provider"
        self.hidden_ports = []
