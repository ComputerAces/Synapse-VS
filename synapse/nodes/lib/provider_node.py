from synapse.core.super_node import SuperNode
from synapse.core.types import DataType
from synapse.nodes.registry import NodeRegistry

class ProviderNode(SuperNode):
    """
    Base class for service providers that establish a context or scope.
    Manages resource initialization, scope entry/exit, and emergency shutdown.
    
    Inputs:
    - Flow: Start the provider and enter its scope.
    - Provider End: Pulse to close the scope and trigger final cleanup.
    - Exit: Emergency pulse to terminate the provider and shut down the system.
    
    Outputs:
    - Flow: Pulse triggered after the provider successfully closes.
    - Provider Flow: Active pulse while the scope is open.
    - Error Flow: Pulse triggered if initialization fails.
    - Provider ID: The unique node ID of the active provider.
    """
    version = "2.1.0"

    def __init__(self, node_id, name, bridge):
        super().__init__(node_id, name, bridge)
        self.is_service = True 
        self.provider_type = getattr(self, "provider_type", "Base Provider")
        self._is_initialized = False
        self.define_schema()
        self.register_handlers()

    def register_handlers(self):
        # Event Handlers
        self.register_handler("Flow", self.start_scope)
        self.register_handler("Provider End", self.end_scope)
        self.register_handler("Exit", self.emergency_exit)

    def define_schema(self):
        self.input_schema = {
            "Flow": DataType.FLOW,
            "Provider End": DataType.PROVIDER_FLOW,
            "Exit": DataType.FLOW
        }
        self.output_schema = {
            "Flow": DataType.FLOW,
            "Provider Flow": DataType.PROVIDER_FLOW,
            "Error Flow": DataType.FLOW,
            "Provider ID": DataType.STRING
        }

    def start_scope(self, **kwargs):
        # 1. Register Identity & Super-Functions
        if not self._is_initialized:
            self.register_provider_context()
            self._is_initialized = True
        
        # 2. Output Provider ID & Type
        self.bridge.set(f"{self.node_id}_Provider ID", self.node_id, self.name)
        self.bridge.set(f"{self.node_id}_Provider Type", self.provider_type, self.name)
        
        # Register in Current Scope
        current_scope = self.context_stack[-1] if self.context_stack else self.bridge.default_scope
        self.bridge.set(f"{current_scope}_Provider_{self.provider_type}", self.node_id, self.name)
        
        # 3. Trigger Provider Flow
        self.bridge.set(f"{self.node_id}_ActivePorts", ["Provider Flow"], self.name)
        return True

    def end_scope(self, **kwargs):
        # 1. Cleanup
        self.cleanup_provider_context()
        self._is_initialized = False
        
        # 2. Trigger Final Flow
        self.bridge.set(f"{self.node_id}_ActivePorts", ["Flow"], self.name)
        return True

    def emergency_exit(self, **kwargs):
        self.cleanup_provider_context()
        self._is_initialized = False
        self.bridge.set("_SYSTEM_SHUTDOWN", True, self.name)
        return False

    def register_provider_context(self):
        """Override to register specific super-functions."""
        pass

    def cleanup_provider_context(self):
        """Cleanup logic before final flow out."""
        self.bridge.unregister_super_functions(self.node_id)

    def terminate(self):
        self.cleanup_provider_context()
        super().terminate()