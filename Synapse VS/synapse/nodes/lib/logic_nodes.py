from synapse.core.super_node import SuperNode
from synapse.nodes.registry import NodeRegistry
from synapse.core.types import DataType, TypeCaster

@NodeRegistry.register("Boolean Flip", "Math/Logic")
class BooleanFlipNode(SuperNode):
    """
    Inverts the provided boolean value (True becomes False, and vice-versa).
    
    Inputs:
    - Flow: Trigger the inversion.
    - Value: The boolean value to flip.
    
    Outputs:
    - Flow: Triggered after the flip.
    - Result: The inverted boolean result.
    """
    version = "2.1.0"
    allow_dynamic_inputs = False

    def __init__(self, node_id, name, bridge):
        super().__init__(node_id, name, bridge)
        self.properties["Value"] = False
        self.define_schema()
        self.register_handlers()
        
    def define_schema(self):
        self.input_schema = {
            "Flow": DataType.FLOW,
            "Value": DataType.BOOLEAN
        }
        self.output_schema = {
            "Flow": DataType.FLOW,
            "Result": DataType.BOOLEAN
        }
    
    def register_handlers(self):
        self.register_handler("Flow", self.flip_bool)

    def flip_bool(self, Value=None, **kwargs):
        val = Value if Value is not None else self.properties.get("Value", False)
        result = not TypeCaster.to_bool(val)
        self.bridge.set(f"{self.node_id}_Result", result, self.name)
        self.bridge.set(f"{self.node_id}_ActivePorts", ["Flow"], self.name)
        return True

@NodeRegistry.register("AND", "Math/Logic")
class AndNode(SuperNode):
    """
    Performs a logical AND operation on a set of boolean inputs.
    Returns True only if all provided inputs are True.
    
    Inputs:
    - Flow: Trigger the logical check.
    - Item 0, Item 1...: Boolean values to evaluate (supports dynamic expansion).
    
    Outputs:
    - Flow: Triggered after evaluation.
    - Result: True if all inputs are True, False otherwise.
    """
    version = "2.1.0"
    allow_dynamic_inputs = True

    def __init__(self, node_id, name, bridge):
        super().__init__(node_id, name, bridge)
        if "AdditionalInputs" not in self.properties and "additional_inputs" not in self.properties:
            self.properties["AdditionalInputs"] = ["Item 0", "Item 1"]
        elif "additional_inputs" in self.properties:
            self.properties["AdditionalInputs"] = self.properties.pop("additional_inputs")
            
        self.define_schema()
        self.register_handlers()

    def define_schema(self):
        self.input_schema = {"Flow": DataType.FLOW}
        self.output_schema = {
            "Flow": DataType.FLOW,
            "Result": DataType.BOOLEAN
        }
        for item in self.properties.get("AdditionalInputs", []):
            self.input_schema[item] = DataType.BOOLEAN

    def register_handlers(self):
        self.register_handler("Flow", self.check_logic)

    def check_logic(self, **kwargs):
        candidates = {k: v for k, v in kwargs.items() if k.startswith("Item")}
        for k, v in self.properties.items():
            if k.startswith("Item") and k not in candidates:
                candidates[k] = v
                
        inputs = [TypeCaster.to_bool(v) for v in candidates.values()]
        result = all(inputs) if inputs else False
        self.bridge.set(f"{self.node_id}_Result", result, self.name)
        self.bridge.set(f"{self.node_id}_ActivePorts", ["Flow"], self.name)
        return True

@NodeRegistry.register("OR", "Math/Logic")
class OrNode(SuperNode):
    """
    Performs a logical OR operation on a set of boolean inputs.
    
    Returns True if at least one of the provided inputs is True. 
    Supports dynamic input expansion.
    
    Inputs:
    - Flow: Trigger the logical check.
    - Item 0, Item 1...: Boolean values to evaluate.
    
    Outputs:
    - Flow: Triggered after evaluation.
    - Result: True if any input is True, False otherwise.
    """
    version = "2.1.0"
    allow_dynamic_inputs = True

    def __init__(self, node_id, name, bridge):
        super().__init__(node_id, name, bridge)
        self.define_schema()
        self.register_handlers()

    def define_schema(self):
        self.input_schema = {"Flow": DataType.FLOW}
        self.output_schema = {
            "Flow": DataType.FLOW,
            "Result": DataType.BOOLEAN
        }

    def register_handlers(self):
        self.register_handler("Flow", self.check_logic)

    def check_logic(self, **kwargs):
        candidates = {k: v for k, v in kwargs.items() if k.startswith("Item")}
        # Resolve from property fallbacks for any Item X
        for k, v in self.properties.items():
            if k.startswith("Item") and k not in candidates:
                candidates[k] = v
                
        inputs = [TypeCaster.to_bool(v) for v in candidates.values()]
        result = any(inputs) if inputs else False
        self.bridge.set(f"{self.node_id}_Result", result, self.name)
        self.bridge.set(f"{self.node_id}_ActivePorts", ["Flow"], self.name)
        return True

@NodeRegistry.register("XOR", "Math/Logic")
class XorNode(SuperNode):
    """
    Performs a logical XOR (Exclusive OR) operation.
    
    Returns True if an odd number of inputs are True. Supports 
    dynamic input expansion.
    
    Inputs:
    - Flow: Trigger the logical check.
    - Item 0, Item 1...: Boolean values to evaluate.
    
    Outputs:
    - Flow: Triggered after evaluation.
    - Result: True if the XOR condition is met.
    """
    version = "2.1.0"
    allow_dynamic_inputs = True

    def __init__(self, node_id, name, bridge):
        super().__init__(node_id, name, bridge)
        self.define_schema()
        self.register_handlers()

    def define_schema(self):
        self.input_schema = {"Flow": DataType.FLOW}
        self.output_schema = {
            "Flow": DataType.FLOW,
            "Result": DataType.BOOLEAN
        }

    def register_handlers(self):
        self.register_handler("Flow", self.check_logic)

    def check_logic(self, **kwargs):
        candidates = {k: v for k, v in kwargs.items() if k.startswith("Item")}
        for k, v in self.properties.items():
            if k.startswith("Item") and k not in candidates:
                candidates[k] = v
                
        inputs = [TypeCaster.to_bool(v) for v in candidates.values()]
        true_count = sum(1 for v in inputs if v)
        result = (true_count % 2 == 1)
        self.bridge.set(f"{self.node_id}_Result", result, self.name)
        self.bridge.set(f"{self.node_id}_ActivePorts", ["Flow"], self.name)
        return True

@NodeRegistry.register("NOT", "Math/Logic")
class NotNode(SuperNode):
    """
    Logical NOT operator. Inverts the input boolean.
    
    Inputs:
    - Flow: Trigger execution.
    - In: The input boolean value.
    
    Outputs:
    - Flow: Triggered after inversion.
    - Result: The inverted result.
    """
    version = "2.1.0"
    allow_dynamic_inputs = True

    def __init__(self, node_id, name, bridge):
        super().__init__(node_id, name, bridge)
        self.properties["In"] = False
        self.define_schema()
        self.register_handlers()

    def define_schema(self):
        self.input_schema = {
            "Flow": DataType.FLOW,
            "In": DataType.BOOLEAN
        }
        self.output_schema = {
            "Flow": DataType.FLOW,
            "Result": DataType.BOOLEAN
        }

    def register_handlers(self):
        self.register_handler("Flow", self.flip_bool)

    def flip_bool(self, In=None, **kwargs):
        val = In if In is not None else self.properties.get("In", False)
        self.bridge.set(f"{self.node_id}_Result", not TypeCaster.to_bool(val), self.name)
        self.bridge.set(f"{self.node_id}_ActivePorts", ["Flow"], self.name)
        return True

@NodeRegistry.register("NAND", "Math/Logic")
class NandNode(SuperNode):
    """
    Performs a logical NAND operation.
    
    Returns True if at least one input is False. Returns False only 
    if all provided inputs are True. Supports dynamic input expansion.
    
    Inputs:
    - Flow: Trigger the logical check.
    - Item 0, Item 1...: Boolean values to evaluate.
    
    Outputs:
    - Flow: Triggered after evaluation.
    - Result: The NAND result.
    """
    version = "2.1.0"
    allow_dynamic_inputs = True

    def __init__(self, node_id, name, bridge):
        super().__init__(node_id, name, bridge)
        self.define_schema()
        self.register_handlers()

    def define_schema(self):
        self.input_schema = {"Flow": DataType.FLOW}
        self.output_schema = {"Flow": DataType.FLOW, "Result": DataType.BOOLEAN}

    def register_handlers(self):
        self.register_handler("Flow", self.check_logic)
    
    def check_logic(self, **kwargs):
        candidates = {k: v for k, v in kwargs.items() if k.startswith("Item")}
        for k, v in self.properties.items():
            if k.startswith("Item") and k not in candidates:
                candidates[k] = v
                
        inputs = [TypeCaster.to_bool(v) for v in candidates.values()]
        result = not all(inputs) if inputs else True
        self.bridge.set(f"{self.node_id}_Result", result, self.name)
        self.bridge.set(f"{self.node_id}_ActivePorts", ["Flow"], self.name)
        return True

@NodeRegistry.register("NOR", "Math/Logic")
class NorNode(SuperNode):
    """
    Performs a logical NOR operation.
    
    Returns True only if all provided inputs are False. Returns False 
     if at least one input is True. Supports dynamic input expansion.
    
    Inputs:
    - Flow: Trigger the logical check.
    - Item 0, Item 1...: Boolean values to evaluate.
    
    Outputs:
    - Flow: Triggered after evaluation.
    - Result: The NOR result.
    """
    version = "2.1.0"
    allow_dynamic_inputs = True

    def __init__(self, node_id, name, bridge):
        super().__init__(node_id, name, bridge)
        self.define_schema()
        self.register_handlers()

    def define_schema(self):
        self.input_schema = {"Flow": DataType.FLOW}
        self.output_schema = {"Flow": DataType.FLOW, "Result": DataType.BOOLEAN}

    def register_handlers(self):
        self.register_handler("Flow", self.check_logic)

    def check_logic(self, **kwargs):
        candidates = {k: v for k, v in kwargs.items() if k.startswith("Item")}
        for k, v in self.properties.items():
            if k.startswith("Item") and k not in candidates:
                candidates[k] = v
                
        inputs = [TypeCaster.to_bool(v) for v in candidates.values()]
        result = not any(inputs) if inputs else True
        self.bridge.set(f"{self.node_id}_Result", result, self.name)
        self.bridge.set(f"{self.node_id}_ActivePorts", ["Flow"], self.name)
        return True

@NodeRegistry.register("XNOR", "Math/Logic")
class XnorNode(SuperNode):
    """
    Performs a logical XNOR operation.
    
    Returns True if an even number of inputs are True. Supports 
    dynamic input expansion.
    
    Inputs:
    - Flow: Trigger the logical check.
    - Item 0, Item 1...: Boolean values to evaluate.
    
    Outputs:
    - Flow: Triggered after evaluation.
    - Result: The XNOR result.
    """
    version = "2.1.0"
    allow_dynamic_inputs = True

    def __init__(self, node_id, name, bridge):
        super().__init__(node_id, name, bridge)
        self.define_schema()
        self.register_handlers()

    def define_schema(self):
        self.input_schema = {"Flow": DataType.FLOW}
        self.output_schema = {"Flow": DataType.FLOW, "Result": DataType.BOOLEAN}

    def register_handlers(self):
        self.register_handler("Flow", self.check_logic)

    def check_logic(self, **kwargs):
        candidates = {k: v for k, v in kwargs.items() if k.startswith("Item")}
        for k, v in self.properties.items():
            if k.startswith("Item") and k not in candidates:
                candidates[k] = v
                
        inputs = [TypeCaster.to_bool(v) for v in candidates.values()]
        true_count = sum(1 for v in inputs if v)
        result = (true_count % 2 == 0)
        self.bridge.set(f"{self.node_id}_Result", result, self.name)
        self.bridge.set(f"{self.node_id}_ActivePorts", ["Flow"], self.name)
        return True
