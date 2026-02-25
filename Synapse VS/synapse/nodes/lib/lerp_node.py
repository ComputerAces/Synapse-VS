from synapse.core.super_node import SuperNode
from synapse.nodes.registry import NodeRegistry
from synapse.core.types import DataType

@NodeRegistry.register("Lerp", "Math/Advanced")
class LerpNode(SuperNode):
    """
    Performs Linear Interpolation (Lerp) between two values based on a weight factor.
    
    Formula: Result = A + (B - A) * T. 
    If T is 0.0, the result is A. If T is 1.0, the result is B.
    
    Inputs:
    - Flow: Trigger the calculation.
    - A: The start value (0%).
    - B: The end value (100%).
    - T: The interpolation factor (typically 0.0 to 1.0).
    
    Outputs:
    - Flow: Triggered after calculation.
    - Result: The interpolated value.
    """
    version = "2.1.0"

    def __init__(self, node_id, name, bridge):
        super().__init__(node_id, name, bridge)
        self.is_native = True
        self.properties["A"] = 0.0
        self.properties["B"] = 1.0
        self.properties["T"] = 0.5
        self.define_schema()
        self.register_handlers()

    def define_schema(self):
        self.input_schema = {
            "Flow": DataType.FLOW,
            "A": DataType.FLOAT,
            "B": DataType.FLOAT,
            "T": DataType.FLOAT
        }
        self.output_schema = {
            "Flow": DataType.FLOW,
            "Result": DataType.FLOAT
        }

    def register_handlers(self):
        self.register_handler("Flow", self.calculate_lerp)

    def calculate_lerp(self, A=None, B=None, T=None, **kwargs):
        a = A if A is not None else kwargs.get("A") or self.properties.get("A", 0.0)
        b = B if B is not None else kwargs.get("B") or self.properties.get("B", 1.0)
        t = T if T is not None else kwargs.get("T") or self.properties.get("T", 0.5)
        try:
            res = a + (b - a) * t
            self.bridge.set(f"{self.node_id}_Result", res, self.name)
        except Exception as e:
            self.logger.error(f"Lerp Error: {e}")
            self.bridge.set(f"{self.node_id}_Result", 0.0, self.name)
        self.bridge.set(f"{self.node_id}_ActivePorts", ["Flow"], self.name)
        return True

@NodeRegistry.register("Inverse Lerp", "Math/Advanced")
class InverseLerpNode(SuperNode):
    """
    Calculates the normalized interpolant (T) for a value within a specific range [A, B].
    
    This is the inverse of the Lerp operation. It determines where 'Value' sits 
    relative to A and B.
    
    Inputs:
    - Flow: Trigger the calculation.
    - A: The lower bound (maps to 0.0).
    - B: The upper bound (maps to 1.0).
    - Value: The number to normalize.
    
    Outputs:
    - Flow: Triggered after calculation.
    - T: The normalized position (0.0 to 1.0).
    """
    version = "2.1.0"

    def __init__(self, node_id, name, bridge):
        super().__init__(node_id, name, bridge)
        self.is_native = True
        self.properties["A"] = 0.0
        self.properties["B"] = 1.0
        self.properties["Value"] = 0.5
        self.define_schema()
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
        self.register_handler("Flow", self.calculate_inverse_lerp)

    def calculate_inverse_lerp(self, A=None, B=None, Value=None, **kwargs):
        a = A if A is not None else kwargs.get("A") or self.properties.get("A", 0.0)
        b = B if B is not None else kwargs.get("B") or self.properties.get("B", 1.0)
        val = Value if Value is not None else kwargs.get("Value") or self.properties.get("Value", 0.5)
        
        if b == a:
            t = 0.0
        else:
            t = (val - a) / (b - a)
            
        self.bridge.set(f"{self.node_id}_T", t, self.name)
        self.bridge.set(f"{self.node_id}_ActivePorts", ["Flow"], self.name)
        return True

@NodeRegistry.register("Remap", "Math/Advanced")
class RemapNode(SuperNode):
    """
    Maps a value from an input range [InMin, InMax] to an output range [OutMin, OutMax].
    
    This node first normalizes the input value and then applies it to the output target range.
    
    Inputs:
    - Flow: Trigger the operation.
    - Value: The number to remap.
    - In Min: The start of the input range.
    - In Max: The end of the input range.
    - Out Min: The start of the output range.
    - Out Max: The end of the output range.
    
    Outputs:
    - Flow: Triggered after transformation.
    - Result: The value mapped to the new range.
    """
    version = "2.1.0"

    def __init__(self, node_id, name, bridge):
        super().__init__(node_id, name, bridge)
        self.is_native = True
        self.properties["Value"] = 0.0
        self.properties["InMin"] = 0.0
        self.properties["InMax"] = 1.0
        self.properties["OutMin"] = 0.0
        self.properties["OutMax"] = 100.0
        self.define_schema()
        self.register_handlers()

    def define_schema(self):
        self.input_schema = {
            "Flow": DataType.FLOW,
            "Value": DataType.FLOAT,
            "In Min": DataType.FLOAT,
            "In Max": DataType.FLOAT,
            "Out Min": DataType.FLOAT,
            "Out Max": DataType.FLOAT
        }
        self.output_schema = {
            "Flow": DataType.FLOW,
            "Result": DataType.FLOAT
        }

    def register_handlers(self):
        self.register_handler("Flow", self.calculate_remap)

    def calculate_remap(self, Value=None, In_Min=None, In_Max=None, Out_Min=None, Out_Max=None, **kwargs):
        val = Value if Value is not None else kwargs.get("Value") or self.properties.get("Value", 0.0)
        in_min = In_Min if In_Min is not None else kwargs.get("In Min") or self.properties.get("InMin", 0.0)
        in_max = In_Max if In_Max is not None else kwargs.get("In Max") or self.properties.get("InMax", 1.0)
        out_min = Out_Min if Out_Min is not None else kwargs.get("Out Min") or self.properties.get("OutMin", 0.0)
        out_max = Out_Max if Out_Max is not None else kwargs.get("Out Max") or self.properties.get("OutMax", 100.0)
        
        if in_max == in_min:
            t = 0.0
        else:
            t = (val - in_min) / (in_max - in_min)
            
        result = out_min + (out_max - out_min) * t
        self.bridge.set(f"{self.node_id}_Result", result, self.name)
        self.bridge.set(f"{self.node_id}_ActivePorts", ["Flow"], self.name)
        return True
