from synapse.core.super_node import SuperNode
from synapse.nodes.registry import NodeRegistry
from synapse.core.types import DataType
from datetime import datetime
import sys

@NodeRegistry.register("Length", "Data")
class LengthNode(SuperNode):
    """
    Calculates the length of lists/strings or normalizes numeric/date values within a range.
    
    Inputs:
    - Flow: Trigger the length/normalization calculation.
    - Value: The item to process (List, String, Number, or Date).
    - Min Value: The lower bound for normalization (optional).
    - Max Value: The upper bound for normalization (optional).
    
    Outputs:
    - Flow: Triggered after the value is processed.
    - Length: The numeric length or normalized 0.0-1.0 value.
    """
    version = "2.1.0"

    def __init__(self, node_id, name, bridge):
        super().__init__(node_id, name, bridge)
        self.is_native = True
        self.define_schema()
        self.register_handlers()

    def register_handlers(self):
        self.register_handler("Flow", self.calculate_length)

    def define_schema(self):
        self.input_schema = {
            "Flow": DataType.FLOW,
            "Value": DataType.ANY,
            "Min Value": DataType.NUMBER,
            "Max Value": DataType.NUMBER
        }
        self.output_schema = {
            "Flow": DataType.FLOW,
            "Length": DataType.NUMBER
        }

    def calculate_length(self, Value=None, Min_Value=None, Max_Value=None, **kwargs):
        val = Value if Value is not None else kwargs.get("Value")
        min_in = Min_Value if Min_Value is not None else kwargs.get("Min Value")
        max_in = Max_Value if Max_Value is not None else kwargs.get("Max Value")
        
        result = 0.0
        
        # 1. List or String (Length)
        if isinstance(val, (list, str)):
            result = len(val)
            
        # 2. Number (Normalization)
        elif isinstance(val, (int, float)):
            try:
                v_float = float(val)
                
                if min_in is not None and max_in is not None:
                     mn = float(min_in)
                     mx = float(max_in)
                     if mx == mn: 
                         result = 0.0
                     else:
                         result = (v_float - mn) / (mx - mn)
                
                elif max_in is not None:
                     mx = float(max_in)
                     if mx == 0: 
                         result = 0.0
                     else:
                         result = v_float / mx
                          
                else:
                    if isinstance(val, int):
                         mx = float(sys.maxsize)
                         result = v_float / mx
                    else:
                         mx = 3.4028235e+38 
                         result = v_float / mx
                         
            except Exception as e:
                self.logger.error(f"Error: {e}")
                result = 0.0
                
        # 3. Date (Normalization within bounds)
        elif isinstance(val, datetime):
            try:
                default_min = datetime(1, 1, 1)
                default_max = datetime(2380, 12, 31)
                
                mn = min_in if isinstance(min_in, datetime) else default_min
                mx = max_in if isinstance(max_in, datetime) else default_max
                
                total_span = (mx - mn).total_seconds()
                current_span = (val - mn).total_seconds()
                
                if total_span > 0:
                    result = current_span / total_span
                else:
                    result = 0.0
            except Exception as e:
                self.logger.error(f"Date Error: {e}")
                result = 0.0
                
        # 4. Fallback
        elif val is not None:
             result = 1
        else:
            result = 0
            
        self.bridge.set(f"{self.node_id}_Length", result, self.name)
        self.bridge.set(f"{self.node_id}_ActivePorts", ["Flow"], self.name)
        return True
