from synapse.core.super_node import SuperNode
from synapse.nodes.registry import NodeRegistry
from synapse.core.types import DataType

@NodeRegistry.register("Number", "Data")
class NumberNode(SuperNode):
    """
    Manages a numerical value. Supports automatic conversion from strings and dynamic updates.
    
    Inputs:
    - Flow: Trigger the number retrieval/update.
    - Value: Optional numerical value to set.
    
    Outputs:
    - Flow: Triggered after the value is processed.
    - Result: The current numerical value.
    """
    version = "2.1.0"

    def __init__(self, node_id, name, bridge):
        super().__init__(node_id, name, bridge)
        self.is_native = True
        self.properties["Value"] = 0
        self.define_schema()
        self.register_handlers()

    def register_handlers(self):
        self.register_handler("Flow", self.process_number)

    def define_schema(self):
        self.input_schema = {
            "Flow": DataType.FLOW,
            "Value": DataType.NUMBER
        }
        self.output_schema = {
            "Flow": DataType.FLOW,
            "Result": DataType.NUMBER
        }

    def process_number(self, Value=None, **kwargs):
        # 1. Resolve raw value
        is_val_provided = Value is not None or "Value" in kwargs
        raw_val = Value if Value is not None else kwargs.get("Value") or self.properties.get("Value", 0)
        
        # 2. Auto-convert/Sanitize
        try:
            val = float(raw_val)
            if val.is_integer():
                val = int(val)
        except (ValueError, TypeError):
            val = 0 # Fallback
            
        # 3. Update internal property if set via Flow
        if is_val_provided:
             self.properties["Value"] = val

        self.bridge.set(f"{self.node_id}_Result", val, self.name)
        self.bridge.set(f"{self.node_id}_ActivePorts", ["Flow"], self.name)
        return True
