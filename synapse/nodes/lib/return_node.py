from synapse.core.super_node import SuperNode
from synapse.nodes.registry import NodeRegistry
from synapse.core.types import DataType

@NodeRegistry.register("Return Node", "Logic/Control Flow")
class ReturnNode(SuperNode):
    """
    The exit point for a graph or subgraph execution.
    
    Sends results back to the caller (e.g., a 'Run Graph' or 'SubGraph' node). 
    It consumes all incoming data and bundles it into the return payload.
    
    Inputs:
    - Flow: Trigger the return.
    
    Outputs:
    - None (Terminator node).
    """
    version = "2.1.0"
    allow_dynamic_inputs = True

    def __init__(self, node_id, name, bridge):
        super().__init__(node_id, name, bridge)
        self.is_native = True
        self.hidden_outputs = ["Flow"]
        
        self.define_schema()
        self.register_handlers()

    def define_schema(self):
        # Base schema
        self.input_schema = {"Flow": DataType.FLOW}
        # Terminators are forbidden from having Output Flow or Output Data
        self.output_schema = {}

    def register_handlers(self):
        self.register_handler("Flow", self.do_work)

    def do_work(self, **kwargs):
        # Capture return values
        return_values = {}
        
        # Collect all incoming data ports
        for k, v in kwargs.items():
            if k in ["Flow", "_trigger", "Exec", "In"]:
                continue
            return_values[k] = v

        if "Data" in return_values and "data" in return_values:
            del return_values["data"]
                
        self.bridge.set("SUBGRAPH_RETURN", return_values, self.name)
        
        # Determine label (engine usually looks for specific node name or default Flow)
        label = self.name if self.name != "Return Node" else "Flow"
        self.bridge.set("__RETURN_NODE_LABEL__", label, self.name)
        
        # No active ports - flow terminates here
        self.bridge.set(f"{self.node_id}_ActivePorts", [], self.name)
        return True

