from synapse.core.super_node import SuperNode
from synapse.nodes.registry import NodeRegistry
from synapse.core.types import DataType
from synapse.utils.datetime_utils import is_formatted_datetime, compare_datetimes

@NodeRegistry.register("Compare", "Logic")
class CompareNode(SuperNode):
    """
    Performs a comparison between two values (A and B) using a specified operator.
    Supports numbers, strings, and formatted datetime strings.
    
    Inputs:
    - Flow: Trigger the comparison.
    - Compare Type: The operator to use (==, !=, >, <, >=, <=).
    - A: The first value.
    - B: The second value.
    
    Outputs:
    - True: Triggered if the condition is met.
    - False: Triggered if the condition is not met.
    - Result: Numeric 1 (True) or 0 (False).
    - Compare Result: Boolean result.
    """
    version = "2.1.0"

    def __init__(self, node_id, name, bridge):
        super().__init__(node_id, name, bridge)
        self.is_native = True
        self.properties["Compare Type"] = "=="
        self.properties["A"] = 0
        self.properties["B"] = 0
        self.hidden_outputs = ["Flow"]
        
        self.define_schema()
        self.register_handler("Flow", self.compare_values)
        
    def define_schema(self):
        self.input_schema = {
            "Flow": DataType.FLOW,
            "Compare Type": DataType.COMPARE_TYPE,
            "A": DataType.ANY,
            "B": DataType.ANY
        }
        self.output_schema = {
            "True": DataType.FLOW,
            "False": DataType.FLOW,
            "Result": DataType.NUMBER,
            "Compare Result": DataType.BOOLEAN
        }

    def compare_values(self, A=None, B=None, **kwargs):
        # Fallback to properties
        val_a = A if A is not None else kwargs.get("A") or self.properties.get("A", 0)
        val_b = B if B is not None else kwargs.get("B") or self.properties.get("B", 0)
        
        # Helper for smart casting
        def smart_cast(val):
            if val is None: return 0
            if isinstance(val, (int, float, bool, list, dict, bytes)): return val
            
            s = str(val)
            # Try numeric
            try:
                f = float(s)
                if f.is_integer(): return int(f)
                return f
            except ValueError:
                # Try boolean strings
                low = s.lower()
                if low in ("true", "yes"): return True
                if low in ("false", "no"): return False
                return s
                
        # 1. Date/Time Comparison
        if is_formatted_datetime(str(val_a)) and is_formatted_datetime(str(val_b)):
             result = self._compare_dates(val_a, val_b)
        else:
             # 2. Standard Comparison (Handles List, Dict, Data, etc.)
             a_c = smart_cast(val_a)
             b_c = smart_cast(val_b)
             result = self._compare_standard(a_c, b_c)
        
        # Outputs
        self.bridge.set(f"{self.node_id}_Compare Result", result, self.name)
        self.bridge.set(f"{self.node_id}_Result", 1 if result else 0, self.name)
        
        # Branching
        branch = "True" if result else "False"
        self.bridge.set(f"{self.node_id}_ActivePorts", [branch], self.name)
        return True

    def _compare_dates(self, a, b):
        op = self.properties.get("Compare Type", "==")
        cmp = compare_datetimes(str(a), str(b))
        if cmp is None: return False
        
        if op == "<": return cmp < 0
        elif op == "<=": return cmp <= 0
        elif op == ">": return cmp > 0
        elif op == ">=": return cmp >= 0
        elif op == "==": return cmp == 0
        elif op == "!=": return cmp != 0
        return False

    def _compare_standard(self, a, b):
        op = self.properties.get("Compare Type", "==")
        try:
            if op == "<": return a < b
            elif op == "<=": return a <= b
            elif op == ">": return a > b
            elif op == ">=": return a >= b
            elif op == "==": return a == b
            elif op == "!=": return a != b
        except TypeError:
            self.logger.warning(f"Compare Error: Type mismatch {type(a)} vs {type(b)}")
        return False
