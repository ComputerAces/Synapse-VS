from synapse.core.super_node import SuperNode
from synapse.nodes.registry import NodeRegistry
from synapse.core.types import DataType

@NodeRegistry.register("Inverse Lerp", "Math/Advanced")
class InverseLerpNode(SuperNode):
    """
    Calculates the linear interpolant (t) of a value relative to a range [A, B].
    
    This is the inverse of the Lerp operation. It returns a normalized value (typically 0.0 to 1.0) 
    representing where 'Value' sits between 'A' and 'B'. If Value is at A, result is 0. If at B, result is 1.
    
    Inputs:
    - Flow: Trigger the calculation.
    - A: The start of the range (maps to 0.0).
    - B: The end of the range (maps to 1.0).
    - Value: The current value to normalize.
    
    Outputs:
    - Flow: Triggered after calculation.
    - T: The calculated interpolant.
    """
    version = "2.1.0"

    def __init__(self, node_id, name, bridge):
        super().__init__(node_id, name, bridge)
        self.properties["A"] = 0.0
        self.properties["B"] = 1.0
        self.define_schema()
        self.properties["Value"] = 0.5
        self.register_handlers()
        
    def define_schema(self):
        self.input_schema = {
            "Flow": DataType.FLOW,
            "A": DataType.FLOAT,
            "B": DataType.FLOAT,
            "Value": DataType.FLOAT
        }
        self.output_schema = {
            "Flow": DataType.FLOW,
            "T": DataType.FLOAT
        }

    def register_handlers(self):
        self.register_handler("Flow", self.execute)

    @property
    def default_inputs(self):
        return [("Flow", DataType.FLOW), ("A", DataType.FLOAT), ("B", DataType.FLOAT), ("Value", DataType.FLOAT)]

    @property
    def default_outputs(self):
        return [("Flow", DataType.FLOW), ("T", DataType.FLOAT)]

    def execute(self, A=None, B=None, Value=None, **kwargs):
        # Fallback to properties
        A = A if A is not None else self.properties.get("A", 0.0)
        B = B if B is not None else self.properties.get("B", 1.0)
        Value = Value if Value is not None else self.properties.get("Value", 0.5)
        try:
            a = float(A)
            b = float(B)
            v = float(Value)
            if b == a:
                res = 0.0
            else:
                res = (v - a) / (b - a)
            self.bridge.set(f"{self.node_id}_T", res, self.name)
        except Exception as e:
            self.logger.error(f"Inverse Lerp Error: {e}")
            self.bridge.set(f"{self.node_id}_T", 0.0, self.name)
        return True
