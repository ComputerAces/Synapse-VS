from synapse.core.super_node import SuperNode
from synapse.nodes.registry import NodeRegistry
from synapse.core.types import DataType
from synapse.utils.datetime_utils import is_formatted_datetime, subtract_from_datetime

@NodeRegistry.register("Subtract", "Math/Arithmetic")
class SubtractNode(SuperNode):
    """
    Subtracts one value from another. Supports both numeric subtraction 
    and date/time offsets (subtracting seconds or days from a timestamp).
    
    Inputs:
    - Flow: Trigger the calculation.
    - A: The base value (Number or Formatted Datetime).
    - B: The value to subtract (Number).
    
    Outputs:
    - Flow: Triggered after the difference is calculated.
    - Result: The resulting difference or offset date.
    """
    version = "2.1.0"

    def __init__(self, node_id, name, bridge):
        super().__init__(node_id, name, bridge)
        self.is_native = True
        self.properties["A"] = 0
        self.properties["B"] = 0
        self.define_schema()
        self.register_handlers()
    
    def define_schema(self):
        self.input_schema = {
            "Flow": DataType.FLOW,
            "A": DataType.ANY, 
            "B": DataType.ANY
        }
        self.output_schema = {
            "Flow": DataType.FLOW,
            "Result": DataType.ANY
        }

    def register_handlers(self):
        self.register_handler("Flow", self.subtract_values)

    def subtract_values(self, A=None, B=None, **kwargs):
        # Fallback to properties
        val_a = A if A is not None else kwargs.get("A")
        if val_a is None: val_a = self.properties.get("A", 0)
        
        val_b = B if B is not None else kwargs.get("B")
        if val_b is None: val_b = self.properties.get("B", 0)
        
        result = None
        
        # 1. Case: Date/Time Math
        if is_formatted_datetime(val_a):
            try:
                # B must be numeric (seconds or days)
                b_val = float(str(val_b))
                # If B contains a dot, or is a float, treat as seconds.
                # Else treat as days (int).
                if "." in str(val_b) or isinstance(val_b, float):
                    result = subtract_from_datetime(val_a, b_val)
                else:
                    result = subtract_from_datetime(val_a, int(b_val))
            except Exception as e:
                self.logger.warning(f"Date/Time Subtraction Failed: {e}")
                result = str(val_a)
        else:
            # Normal Numeric subtraction
            try:
                result = float(val_a) - float(val_b)
                if result.is_integer(): result = int(result)
            except:
                result = 0
                
        self.bridge.set(f"{self.node_id}_Result", result, self.name)
        self.bridge.set(f"{self.node_id}_ActivePorts", ["Flow"], self.name)
        return True

