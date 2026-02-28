from synapse.core.super_node import SuperNode
from synapse.nodes.registry import NodeRegistry
from synapse.core.types import DataType

@NodeRegistry.register("Add", "Math/Arithmetic")
class AddNode(SuperNode):
    """
    Combines two values using addition, string concatenation, or list merging.
    Automatically detects data types and applies the appropriate combination logic.
    
    Inputs:
    - Flow: Trigger the addition process.
    - A: The first value (Number, String, or List).
    - B: The second value (Number, String, or List).
    
    Outputs:
    - Flow: Triggered after combination.
    - Result: The sum, merged list, or concatenated string.
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
        self.register_handler("Flow", self.add_values)

    def add_values(self, A=None, B=None, **kwargs):
        # Fallback to properties
        val_a = A if A is not None else kwargs.get("A")
        if val_a is None: val_a = self.properties.get("A", 0)
        
        val_b = B if B is not None else kwargs.get("B")
        if val_b is None: val_b = self.properties.get("B", 0)
        
        result = None
        
        # 1. Resolve Case: Lists (Merge)
        if isinstance(val_a, list) or isinstance(val_b, list):
            list_a = val_a if isinstance(val_a, list) else [val_a]
            list_b = val_b if isinstance(val_b, list) else [val_b]
            result = list_a + list_b
            
        # 2. Case: Numbers (Math) / Strings
        else:
            try:
                # Try as numbers first
                f_a = float(val_a)
                f_b = float(val_b)
                result = f_a + f_b
                if result.is_integer(): result = int(result)
            except:
                # Fallback to string concat
                result = str(val_a) + str(val_b)

        self.bridge.set(f"{self.node_id}_Result", result, self.name)
        self.bridge.set(f"{self.node_id}_ActivePorts", ["Flow"], self.name)
        return True
