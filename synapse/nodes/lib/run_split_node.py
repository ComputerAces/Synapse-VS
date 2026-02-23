from synapse.core.super_node import SuperNode
from synapse.nodes.registry import NodeRegistry
from synapse.core.types import DataType

@NodeRegistry.register("Run Split", "Logic")
class RunSplitNode(SuperNode):
    """
    Splits flow based on whether a value is populated or 'Null'.
    
    Checks the 'Value' input. If it is non-empty and valid, the 'Valid' 
    port is pulsed. If it is None, empty, or "none", the 'Null' 
    port is pulsed.
    
    Inputs:
    - Flow: Trigger the check.
    - Value: The data to validate.
    
    Outputs:
    - Valid: Pulse triggered if value is valid.
    - Null: Pulse triggered if value is empty/null.
    """
    version = "2.1.0"

    def __init__(self, node_id, name, bridge):
        super().__init__(node_id, name, bridge)
        self.is_native = True
        self.define_schema()
        self.register_handler("Flow", self.check_split)

    def define_schema(self):
        self.input_schema = {
            "Flow": DataType.FLOW,
            "Value": DataType.ANY
        }
        self.output_schema = {
            "Valid": DataType.FLOW,
            "Null": DataType.FLOW
        }

    def check_split(self, Value=None, **kwargs):
        # Fallback to properties
        val = Value if Value is not None else self.properties.get("Value", "")
        # Standardize check logic
        # Empty string "" is considered Null? Original logic:
        # is_valid = Value is not None and str(Value).strip() != "" and str(Value).lower() != "none"
        
        is_valid = val is not None and str(val).strip() != "" and str(val).lower() != "none"
        
        result_port = "Valid" if is_valid else "Null"
        
        print(f"[{self.name}] RunSplit: {val} -> {result_port}")
        self.bridge.set(f"{self.node_id}_ActivePorts", [result_port], self.name)
