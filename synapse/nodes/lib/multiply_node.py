from synapse.core.super_node import SuperNode
from synapse.nodes.registry import NodeRegistry
from synapse.core.types import DataType

@NodeRegistry.register("Multiply", "Math/Arithmetic")
class MultiplyNode(SuperNode):
    """
    Performs multiplication of two numeric values.
    Automatically handles integer and float conversion for the result.
    
    Inputs:
    - Flow: Trigger the multiplication.
    - A: The first factor.
    - B: The second factor.
    
    Outputs:
    - Flow: Triggered after the product is calculated.
    - Result: The product of A and B.
    """
    version = "2.1.0"

    def __init__(self, node_id, name, bridge):
        super().__init__(node_id, name, bridge)
        self.is_native = True
        self.properties["A"] = 1
        self.properties["B"] = 1
        self.define_schema()
        self.register_handlers()
    
    def define_schema(self):
        self.input_schema = {
            "Flow": DataType.FLOW,
            "A": DataType.NUMBER,
            "B": DataType.NUMBER
        }
        self.output_schema = {
            "Flow": DataType.FLOW,
            "Result": DataType.NUMBER
        }

    def register_handlers(self):
        self.register_handler("Flow", self.multiply)
        
    def multiply(self, A=None, B=None, **kwargs):
        val_a = A if A is not None else self.properties.get("A", 1)
        val_b = B if B is not None else self.properties.get("B", 1)
        
        try:
            result = float(val_a) * float(val_b)
            if result.is_integer(): result = int(result)
        except:
            result = 0
            
        self.bridge.set(f"{self.node_id}_Result", result, self.name)
        self.bridge.set(f"{self.node_id}_ActivePorts", ["Flow"], self.name)
        return True
