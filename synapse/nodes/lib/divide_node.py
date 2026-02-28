from synapse.core.super_node import SuperNode
from synapse.nodes.registry import NodeRegistry
from synapse.core.types import DataType

@NodeRegistry.register("Divide", "Math/Arithmetic")
class DivideNode(SuperNode):
    """
    Divides two numbers and provides the quotient.
    
    Inputs:
    - Flow: Execution trigger.
    - A: The dividend.
    - B: The divisor.
    - Handle Div 0: If true, returns 0 instead of triggering Error Flow on division by zero.
    
    Outputs:
    - Flow: Triggered on successful division.
    - Error Flow: Triggered if division by zero occurs and not handled.
    - Result: The quotient.
    """
    version = "2.1.0"

    def __init__(self, node_id, name, bridge):
        super().__init__(node_id, name, bridge)
        self.is_native = True
        self.properties["A"] = 1
        self.properties["B"] = 1
        self.properties["Handle Div 0"] = False
        self.define_schema()
        self.register_handlers()
    
    def define_schema(self):
        self.input_schema = {
            "Flow": DataType.FLOW,
            "A": DataType.NUMBER,
            "B": DataType.NUMBER,
            "Handle Div 0": DataType.BOOLEAN
        }
        self.output_schema = {
            "Flow": DataType.FLOW,
            "Error Flow": DataType.FLOW,
            "Result": DataType.NUMBER
        }

    def register_handlers(self):
        self.register_handler("Flow", self.divide)
        
    def divide(self, A=None, B=None, **kwargs):
        val_a = A if A is not None else kwargs.get("A")
        if val_a is None: val_a = self.properties.get("A", 1)
        
        val_b = B if B is not None else kwargs.get("B")
        if val_b is None: val_b = self.properties.get("B", 1)
        
        handle_zero = kwargs.get("Handle Div 0") if kwargs.get("Handle Div 0") is not None else self.properties.get("Handle Div 0", False)
        
        try:
            divisor = float(val_b)
            if divisor == 0:
                if handle_zero:
                    self.bridge.set(f"{self.node_id}_Result", 0, self.name)
                    self.bridge.set(f"{self.node_id}_ActivePorts", ["Flow"], self.name)
                    return True
                else:
                    self.logger.error("Division by zero.")
                    self.bridge.set(f"{self.node_id}_ActivePorts", ["Error Flow"], self.name)
                    return True
                
            result = float(val_a) / divisor
            if result.is_integer(): result = int(result)
            self.bridge.set(f"{self.node_id}_Result", result, self.name)
            self.bridge.set(f"{self.node_id}_ActivePorts", ["Flow"], self.name)
        except Exception as e:
            self.logger.error(f"Divide Error: {e}")
            self.bridge.set(f"{self.node_id}_ActivePorts", ["Error Flow"], self.name)
            
        return True
