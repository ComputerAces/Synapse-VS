from synapse.core.super_node import SuperNode
from synapse.nodes.registry import NodeRegistry
from synapse.core.types import DataType

@NodeRegistry.register("Switch", "Flow/Control")
class SwitchNode(SuperNode):
    """
    Directs execution flow based on a match between an input value and one of several named output ports.
    
    This node functions like if-elif-else or switch-case statements in programming. 
    It compares the 'Value' against the names of all custom output ports (cases). 
    Matching is string-based and case-insensitive. If no match is found, the 'Default' port is triggered.
    
    Inputs:
    - Flow: Execution trigger.
    - Value: The data item to evaluate.
    
    Outputs:
    - Default: Pulse triggered if no matching case is found.
    - [Dynamic Cases]: Custom ports where the port name defines the matching value.
    """
    version = "2.1.0"
    allow_dynamic_outputs = True

    def __init__(self, node_id, name, bridge):
        super().__init__(node_id, name, bridge)
        self.is_native = True
        
        self.properties["Value"] = "" 
            
        self.define_schema()
        self.register_handler("Flow", self.process_switch)
    
    def define_schema(self):
        self.input_schema = {
            "Flow": DataType.FLOW,
            "Value": DataType.ANY
        }
        
        self.output_schema = {
            "Default": DataType.FLOW
        }

    def process_switch(self, Value=None, **kwargs):
        val_str = str(Value) if Value is not None else str(self.properties.get("Value", ""))
        val_str = val_str.strip()
        val_lower = val_str.lower()
        
        chosen_port = "Default"
        
        # Iterate over all output ports except Default and Flow
        for port_name in self.output_schema.keys():
            if port_name in ["Default", "Flow"]:
                continue
            
            # Match strictly against port name
            if val_str == port_name or val_lower == port_name.lower():
                chosen_port = port_name
                break
            
            # Try numeric match
            try:
                if float(val_str) == float(port_name):
                    chosen_port = port_name
                    break
            except (ValueError, TypeError):
                pass
                    
        self.logger.info(f"Switching on '{val_str}' -> {chosen_port}")
        self.bridge.set(f"{self.node_id}_ActivePorts", [chosen_port], self.name)
        return True
