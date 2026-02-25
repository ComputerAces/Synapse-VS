from synapse.core.super_node import SuperNode
from synapse.nodes.registry import NodeRegistry
from synapse.core.types import DataType

@NodeRegistry.register("Currency", "Data")
class CurrencyNode(SuperNode):
    """
    Standardizes a numerical value into a currency format (rounded to 2 decimal places).
    
    Inputs:
    - Flow: Trigger the currency formatting.
    - Value: The raw numerical value to process.
    
    Outputs:
    - Flow: Triggered after the value is formatted.
    - Result: The formatted numerical value (2-decimal float).
    """
    version = "2.1.0"

    def __init__(self, node_id, name, bridge):
        super().__init__(node_id, name, bridge)
        self.is_native = True
        self.properties["Value"] = 0.00
        self.define_schema()
        self.register_handlers()

    def register_handlers(self):
        self.register_handler("Flow", self.process_currency)

    def define_schema(self):
        self.input_schema = {
            "Flow": DataType.FLOW,
            "Value": DataType.NUMBER
        }
        self.output_schema = {
            "Flow": DataType.FLOW,
            "Result": DataType.NUMBER
        }

    def process_currency(self, Value=None, **kwargs):
        # 1. Resolve raw value
        is_val_provided = Value is not None or "Value" in kwargs
        raw = Value if Value is not None else kwargs.get("Value") or self.properties.get("Value", 0.00)
        
        # 2. Sanitize/Normalize
        try:
            val = float(raw)
        except (ValueError, TypeError):
            val = 0.00
            
        # Round to 2 decimals for currency standard
        val = round(val, 2)
        
        # 3. Update internal property if set via Flow
        if is_val_provided:
             self.properties["Value"] = val

        self.bridge.set(f"{self.node_id}_Result", val, self.name)
        self.bridge.set(f"{self.node_id}_ActivePorts", ["Flow"], self.name)
        return True
