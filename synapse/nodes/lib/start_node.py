from synapse.nodes.lib.provider_node import ProviderNode
from synapse.nodes.registry import NodeRegistry
from synapse.core.types import DataType

@NodeRegistry.register("Start Node", "Logic/Control Flow")
class StartNode(ProviderNode):
    """
    The entry point for a graph or subgraph execution.
    
    Initiates the flow and optionally injects global variables or provider 
    contexts into the runtime. It acts as the primary data producer for 
    the starting branch.
    
    Inputs:
    - None (Initiator node).
    
    Outputs:
    - Flow: The primary execution pulse.
    - Error Flow: Pulse triggered if context initialization fails.
    """
    version = "2.1.0"
    allow_dynamic_outputs = True
    
    def __init__(self, node_id, name, bridge):
        super().__init__(node_id, name, bridge)
        self.is_service = True 
        self.hidden_inputs = ["Flow"]
        
        self.define_schema()
        self.register_handlers()

    def register_provider_context(self):
        return "Flow Provider"

    def define_schema(self):
        # Initiators are forbidden from having Input Flow or Input Data
        self.input_schema = {}
        
        self.output_schema = {
            "Flow": DataType.FLOW,
            "Error Flow": DataType.FLOW
        }

    def register_handlers(self):
        # Initiators fire their logic via start_scope in ProviderNode context
        super().register_handlers()

    def start_scope(self, **kwargs):
        # Initiators fire their logic via start_scope in ProviderNode context
        self._inject_outputs()
        self.bridge.set(f"{self.node_id}_ActivePorts", ["Flow"], self.name)
        return True

    def _inject_outputs(self):
        outputs = list(self.output_schema.keys())
        all_keys = self.bridge.get_all_keys()
        
        for out in outputs:
            if out in ["Flow", "Error Flow"]: continue
            val = self.bridge.get(out)
            
            if val is None:
                search_key = out.lower()
                for k in all_keys:
                    clean_k = k.split(":", 1)[1] if ":" in k else k
                    if clean_k.lower() == search_key:
                        val = self.bridge.get(k)
                        break
            
            if val is None:
                val = self.properties.get(out)
                
            if val is not None:
                self.bridge.set(f"{self.node_id}_{out}", val, self.name)

