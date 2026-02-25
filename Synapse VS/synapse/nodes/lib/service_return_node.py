from synapse.core.super_node import SuperNode
from synapse.nodes.registry import NodeRegistry
from synapse.core.types import DataType

@NodeRegistry.register("Service Return", "Logic")
class ServiceReturnNode(SuperNode):
    """
    Signals the end of a service or subgraph execution phase.
    
    Used within service graphs to return control and data back to 
    the parent graph. It packages all non-flow inputs into a 
    return payload.
    
    Inputs:
    - Flow: Trigger the return.
    
    Outputs:
    - None (Terminator node).
    """
    version = "2.1.0"

    def __init__(self, node_id, name, bridge):
        super().__init__(node_id, name, bridge)
        self.is_native = True
        self.define_schema()
        self.register_handler("Flow", self.yield_service)

    def define_schema(self):
        self.input_schema = {
            "Flow": DataType.FLOW
        }
        self.output_schema = {}

    def yield_service(self, **kwargs):
        # 1. Package return data
        results = {}
        for k, v in kwargs.items():
            if k != "Flow":
                results[k] = v
        
        # 2. Set return metadata on bridge
        self.bridge.set("SUBGRAPH_RETURN", results, self.name)
        self.bridge.set("__RETURN_NODE_LABEL__", "Flow", self.name)
        
        # 3. Signal Yield to Engine
        print(f"[{self.name}] Service Yielding control to parent...")
        self.bridge.set("_SYNP_YIELD", True, self.name)
        
        # No propagation of flow (it exits the setup phase)
        # self.bridge.set(f"{self.node_id}_ActivePorts", [], self.name)
        return results
