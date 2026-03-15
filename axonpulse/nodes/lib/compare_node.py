from axonpulse.core.super_node import SuperNode
from axonpulse.nodes.registry import NodeRegistry
from axonpulse.core.types import DataType
from axonpulse.utils.datetime_utils import is_formatted_datetime, compare_datetimes

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
    version = "2.3.0"

    def __init__(self, node_id, name, bridge):
        super().__init__(node_id, name, bridge)
        self.is_native = True
        self.properties["Compare Type"] = "=="
        self.properties["A"] = ""
        self.properties["B"] = ""
        self.hidden_outputs = ["Flow"]
        
        self.define_schema()
        self.register_handler("Flow", self.compare_values)
        # [FIX] Defensive Triggering: Allow 'A' and 'B' as triggers if wired incorrectly
        self.register_handler("A", self.compare_values)
        self.register_handler("B", self.compare_values)
        
    def define_schema(self):
        self.input_schema = {
            'Flow': DataType.FLOW,
            'A': DataType.ANY,
            'B': DataType.ANY,
            'Compare Type': DataType.COMPARE_TYPE
        }
        self.output_schema = {
            'Flow': DataType.FLOW,
            'True': DataType.FLOW,
            'False': DataType.FLOW,
            'Result': DataType.BOOLEAN
        }

    def compare_values(self, A=None, B=None, **kwargs):
        # Resolve inputs
        val_a = A if A is not None else kwargs.get("A") or self.properties.get("A", 0)
        val_b = B if B is not None else kwargs.get("B") or self.properties.get("B", 0)
        op = kwargs.get("Compare Type") or self.properties.get("Compare Type", "==")
        
        # 1. Date/Time Comparison
        if is_formatted_datetime(str(val_a)) and is_formatted_datetime(str(val_b)):
             result = self._compare_dates(val_a, val_b, op)
        else:
             # 2. Universal Comparison
             result = self._compare_universal(val_a, val_b, op)
        
        # Outputs
        self.bridge.set(f"{self.node_id}_Compare Result", result, self.name)
        self.bridge.set(f"{self.node_id}_Result", 1 if result else 0, self.name)
        
        # Branching
        branch = "True" if result else "False"
        self.bridge.set(f"{self.node_id}_ActivePorts", [branch], self.name)
        return True

    def _compare_dates(self, a, b, op):
        cmp = compare_datetimes(str(a), str(b))
        if cmp is None: return False
        
        if op == "<": return cmp < 0
        elif op == "<=": return cmp <= 0
        elif op == ">": return cmp > 0
        elif op == ">=": return cmp >= 0
        elif op == "==": return cmp == 0
        elif op == "!=": return cmp != 0
        return False

    def _get_hash(self, val):
        """Generates a stable hash for comparison of complex types."""
        import hashlib
        import json
        
        if val is None: return "None"
        if isinstance(val, (int, float, bool)): return str(val)
        
        try:
            if isinstance(val, bytes):
                # Fastest for raw image data
                return hashlib.md5(val).hexdigest()
            elif isinstance(val, (dict, list)):
                # Stable JSON for data structures
                encoded = json.dumps(val, sort_keys=True).encode()
                return hashlib.md5(encoded).hexdigest()
        except:
            pass
            
        return str(val)

    def _compare_universal(self, a, b, op):
        # Helper for smart casting (numeric/bool)
        def try_numeric(val):
            if isinstance(val, (int, float, bool)): return val
            try:
                f = float(str(val))
                return int(f) if f.is_integer() else f
            except:
                return None

        # 1. Numeric Comparison (Priority)
        num_a = try_numeric(a)
        num_b = try_numeric(b)
        if num_a is not None and num_b is not None:
            try:
                if op == "<": return num_a < num_b
                elif op == "<=": return num_a <= num_b
                elif op == ">": return num_a > num_b
                elif op == ">=": return num_a >= num_b
                elif op == "==": return num_a == num_b
                elif op == "!=": return num_a != num_b
            except: pass

        # 2. String/Complex Comparison
        # For strings, we allow equality and inequality.
        # For large data (bytes, dict, list), we use hashing.
        
        is_complex = isinstance(a, (bytes, dict, list)) or isinstance(b, (bytes, dict, list))
        
        if is_complex:
            hash_a = self._get_hash(a)
            hash_b = self._get_hash(b)
            if op == "==": return hash_a == hash_b
            elif op == "!=": return hash_a != hash_b
            # Other ops don't make sense for complex data, default to False per user preference
            return False
            
        # Standard strings/other
        str_a = str(a)
        str_b = str(b)
        
        if op == "==": return str_a == str_b
        elif op == "!=": return str_a != str_b
        elif op == "<": return str_a < str_b
        elif op == "<=": return str_a <= str_b
        elif op == ">": return str_a > str_b
        elif op == ">=": return str_a >= str_b
        
        return False
