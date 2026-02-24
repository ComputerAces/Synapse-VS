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
        registry = getattr(self.bridge, '_port_registry', None)
        
        for out in outputs:
            if out in ["Flow", "Error Flow"]: continue
            
            # 1. Try UUID Key (Direct injection from PortRegistry-aware SubGraphNode)
            val = None
            if registry:
                uuid_key = registry.get_uuid(self.node_id, out, "output")
                if uuid_key:
                    val = self.bridge.get(uuid_key)
            
            # 2. Try Name Key (Standard injection from SubGraphNode)
            if val is None:
                val = self.bridge.get(out)
            
            # 3. Try Legacy Node-Prefixed Key (Injected as {node_id}_{port_name})
            if val is None:
                val = self.bridge.get(f"{self.node_id}_{out}")
                
            # 4. Property Fallback
            if val is None:
                val = self.properties.get(out)
                
            if val is not None:
                # Prime the output for downstream nodes in this graph pass
                self.set_output(out, val)

