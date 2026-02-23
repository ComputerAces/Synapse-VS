from synapse.core.types import DataType
from synapse.nodes.registry import NodeRegistry
from synapse.nodes.lib.provider_node import ProviderNode

@NodeRegistry.register("Network Provider", "Network/Providers")
class NetworkProviderNode(ProviderNode):
    """
    Service provider for base network configurations.
    Registers global settings like Base URL and Proxy in a scope for child 
    nodes like HTTP Request to discover and use.
    
    Inputs:
    - Flow: Start the network provider service and enter the configuration scope.
    - Base URL: The default API endpoint prefix.
    - Proxy: The proxy server URL for outgoing requests.
    - Headers: A dictionary of default HTTP headers.
    
    Outputs:
    - Provider Flow: Active while the configuration scope is open.
    - Flow: Triggered when the service is stopped.
    """
    version = "2.1.0"

    def __init__(self, node_id, name, bridge):
        super().__init__(node_id, name, bridge)
        self.provider_type = "Network Provider"
        self.properties["BaseUrl"] = ""
        self.properties["Proxy"] = ""
        self.properties["DefaultHeaders"] = {} # dict

    def define_schema(self):
        super().define_schema()
        # No extra inputs, just properties
        
    def start_scope(self, **kwargs):
        # Register values in bridge so child nodes can find them via get_provider_id
        self.bridge.set(f"{self.node_id}_Base URL", self.properties.get("BaseUrl"), self.name)
        self.bridge.set(f"{self.node_id}_Proxy", self.properties.get("Proxy"), self.name)
        self.bridge.set(f"{self.node_id}_Headers", self.properties.get("DefaultHeaders"), self.name)
        
        # We don't have a "service object" per se, but we set the provider context
        self.bridge.set(f"{self.node_id}_Provider", True, self.name)
        
        super().start_scope(**kwargs)

    def register_provider_context(self):
        # Already handled in start_scope or here? 
        # ProviderNode calls register_provider_context inside start_scope usually?
        # Let's check ProviderNode implementation.
        # ProviderNode calls register_provider_context() in its start_scope?
        # No, ProviderNode just emits flow. 
        # Base implementation used register_provider_context.
        # Let's keep it consistent.
        self.bridge.set(f"{self.node_id}_Base URL", self.properties.get("BaseUrl"), self.name)
        self.bridge.set(f"{self.node_id}_Proxy", self.properties.get("Proxy"), self.name)
        self.bridge.set(f"{self.node_id}_Headers", self.properties.get("DefaultHeaders"), self.name)
