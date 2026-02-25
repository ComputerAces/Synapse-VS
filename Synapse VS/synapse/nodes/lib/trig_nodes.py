from synapse.core.super_node import SuperNode
from synapse.nodes.registry import NodeRegistry
from synapse.core.types import DataType
import math

@NodeRegistry.register("Sin", "Math/Trigonometry")
class SinNode(SuperNode):
    """
    Calculates the sine of a given angle.
    
    Processes the input 'Angle'. If 'Degrees' is True, the angle is 
    treated as degrees and converted to radians before calculation. 
    Otherwise, it is treated as radians.
    
    Inputs:
    - Flow: Trigger the calculation.
    - Angle: The input angle to process.
    - Degrees: Whether the angle is in degrees (True) or radians (False).
    
    Outputs:
    - Flow: Triggered after calculation.
    - Result: The sine of the angle.
    """
    version = "2.1.0"

    def __init__(self, node_id, name, bridge):
        super().__init__(node_id, name, bridge)
        self.is_native = True
        self.properties["Degrees"] = False
        self.properties["Angle"] = 0.0
        self.define_schema()
        self.register_handlers()

    def define_schema(self):
        self.input_schema = {
            "Flow": DataType.FLOW,
            "Angle": DataType.FLOAT,
            "Degrees": DataType.BOOLEAN
        }
        self.output_schema = {
            "Flow": DataType.FLOW,
            "Result": DataType.FLOAT
        }

    def register_handlers(self):
        self.register_handler("Flow", self.calculate_sin)

    def calculate_sin(self, Angle=None, Degrees=None, **kwargs):
        val = Angle if Angle is not None else self.properties.get("Angle", 0.0)
        angle = float(val)
        
        use_degrees = Degrees if Degrees is not None else self.properties.get("Degrees", False)
        if use_degrees:
            angle = math.radians(angle)
        self.bridge.set(f"{self.node_id}_Result", math.sin(angle), self.name)
        self.bridge.set(f"{self.node_id}_ActivePorts", ["Flow"], self.name)
        return True

@NodeRegistry.register("Cos", "Math/Trigonometry")
class CosNode(SuperNode):
    """
    Calculates the cosine of a given angle.
    Supports both Degrees and Radians based on the Degrees property.
    
    Inputs:
    - Flow: Trigger the calculation.
    - Angle: The input angle to process.
    
    Outputs:
    - Flow: Triggered after calculation.
    - Result: The cosine of the angle.
    """
    version = "2.1.0"

    def __init__(self, node_id, name, bridge):
        super().__init__(node_id, name, bridge)
        self.is_native = True
        self.properties["Degrees"] = False
        self.properties["Angle"] = 0.0
        self.define_schema()
        self.register_handlers()

    def define_schema(self):
        self.input_schema = {
            "Flow": DataType.FLOW,
            "Angle": DataType.FLOAT,
            "Degrees": DataType.BOOLEAN
        }
        self.output_schema = {
            "Flow": DataType.FLOW,
            "Result": DataType.FLOAT
        }

    def register_handlers(self):
        self.register_handler("Flow", self.calculate_cos)

    def calculate_cos(self, Angle=None, Degrees=None, **kwargs):
        val = Angle if Angle is not None else self.properties.get("Angle", 0.0)
        angle = float(val)
        
        use_degrees = Degrees if Degrees is not None else self.properties.get("Degrees", False)
        if use_degrees:
            angle = math.radians(angle)
        self.bridge.set(f"{self.node_id}_Result", math.cos(angle), self.name)
        self.bridge.set(f"{self.node_id}_ActivePorts", ["Flow"], self.name)
        return True

@NodeRegistry.register("Tan", "Math/Trigonometry")
class TanNode(SuperNode):
    """
    Calculates the tangent of a given angle.
    
    Processes the input 'Angle'. If 'Degrees' is True, the angle is 
    treated as degrees and converted to radians before calculation. 
    Otherwise, it is treated as radians.
    
    Inputs:
    - Flow: Trigger the calculation.
    - Angle: The input angle to process.
    - Degrees: Whether the angle is in degrees (True) or radians (False).
    
    Outputs:
    - Flow: Triggered after calculation.
    - Result: The tangent of the angle.
    """
    version = "2.1.0"

    def __init__(self, node_id, name, bridge):
        super().__init__(node_id, name, bridge)
        self.is_native = True
        self.properties["Degrees"] = False
        self.properties["Angle"] = 0.0
        self.define_schema()
        self.register_handlers()

    def define_schema(self):
        self.input_schema = {
            "Flow": DataType.FLOW,
            "Angle": DataType.FLOAT,
            "Degrees": DataType.BOOLEAN
        }
        self.output_schema = {
            "Flow": DataType.FLOW,
            "Result": DataType.FLOAT
        }

    def register_handlers(self):
        self.register_handler("Flow", self.calculate_tan)

    def calculate_tan(self, Angle=None, Degrees=None, **kwargs):
        val = Angle if Angle is not None else self.properties.get("Angle", 0.0)
        angle = float(val)
        
        use_degrees = Degrees if Degrees is not None else self.properties.get("Degrees", False)
        if use_degrees:
            angle = math.radians(angle)
        self.bridge.set(f"{self.node_id}_Result", math.tan(angle), self.name)
        self.bridge.set(f"{self.node_id}_ActivePorts", ["Flow"], self.name)
        return True

@NodeRegistry.register("Asin", "Math/Trigonometry")
class AsinNode(SuperNode):
    """
    Calculates the arc sine (inverse sine) of a value.
    The input value must be between -1 and 1.
    
    Inputs:
    - Flow: Trigger the calculation.
    - Value: The numerical value to process (-1 to 1).
    
    Outputs:
    - Flow: Triggered after calculation.
    - Result: The angle in radians (or degrees if the Degrees property is set).
    """
    version = "2.1.0"

    def __init__(self, node_id, name, bridge):
        super().__init__(node_id, name, bridge)
        self.is_native = True
        self.properties["Degrees"] = False
        self.properties["Value"] = 0.0
        self.define_schema()
        self.register_handlers()

    def define_schema(self):
        self.input_schema = {
            "Flow": DataType.FLOW,
            "Value": DataType.FLOAT,
        }
        self.output_schema = {
            "Flow": DataType.FLOW,
            "Result": DataType.FLOAT
        }

    def register_handlers(self):
        self.register_handler("Flow", self.calculate_asin)

    def calculate_asin(self, Value=None, **kwargs):
        val = Value if Value is not None else self.properties.get("Value", 0.0)
        value = float(val)
        try:
            result = math.asin(max(-1, min(1, value)))
            if self.properties.get("Degrees", self.properties.get("Degrees", False)):
                result = math.degrees(result)
            self.bridge.set(f"{self.node_id}_Result", result, self.name)
        except ValueError:
             self.logger.warning(f"Asin Error: Value {value} out of range -1 to 1")
        self.bridge.set(f"{self.node_id}_ActivePorts", ["Flow"], self.name)
        return True

@NodeRegistry.register("Acos", "Math/Trigonometry")
class AcosNode(SuperNode):
    """
    Calculates the arc cosine (inverse cosine) of a value.
    The input value must be between -1 and 1.
    
    Inputs:
    - Flow: Trigger the calculation.
    - Value: The numerical value to process (-1 to 1).
    
    Outputs:
    - Flow: Triggered after calculation.
    - Result: The angle in radians (or degrees if the Degrees property is set).
    """
    version = "2.1.0"

    def __init__(self, node_id, name, bridge):
        super().__init__(node_id, name, bridge)
        self.is_native = True
        self.properties["Degrees"] = False
        self.properties["Value"] = 0.0
        self.define_schema()
        self.register_handlers()

    def define_schema(self):
        self.input_schema = {
            "Flow": DataType.FLOW,
            "Value": DataType.FLOAT,
        }
        self.output_schema = {
            "Flow": DataType.FLOW,
            "Result": DataType.FLOAT
        }

    def register_handlers(self):
        self.register_handler("Flow", self.calculate_acos)

    def calculate_acos(self, Value=None, **kwargs):
        val = Value if Value is not None else self.properties.get("Value", 0.0)
        value = float(val)
        try:
            result = math.acos(max(-1, min(1, value)))
            if self.properties.get("Degrees", self.properties.get("Degrees", False)):
                result = math.degrees(result)
            self.bridge.set(f"{self.node_id}_Result", result, self.name)
        except ValueError:
             self.logger.warning(f"Acos Error: Value {value} out of range -1 to 1")
        self.bridge.set(f"{self.node_id}_ActivePorts", ["Flow"], self.name)
        return True

@NodeRegistry.register("Atan", "Math/Trigonometry")
class AtanNode(SuperNode):
    """
    Calculates the arc tangent (inverse tangent) of a value.
    
    Inputs:
    - Flow: Trigger the calculation.
    - Value: The numerical value to process.
    
    Outputs:
    - Flow: Triggered after calculation.
    - Result: The angle in radians (or degrees if the Degrees property is set).
    """
    version = "2.1.0"

    def __init__(self, node_id, name, bridge):
        super().__init__(node_id, name, bridge)
        self.is_native = True
        self.properties["Degrees"] = False
        self.properties["Value"] = 0.0
        self.define_schema()
        self.register_handlers()

    def define_schema(self):
        self.input_schema = {
            "Flow": DataType.FLOW,
            "Value": DataType.FLOAT,
        }
        self.output_schema = {
            "Flow": DataType.FLOW,
            "Result": DataType.FLOAT
        }

    def register_handlers(self):
        self.register_handler("Flow", self.calculate_atan)

    def calculate_atan(self, Value=None, **kwargs):
        val = Value if Value is not None else self.properties.get("Value", 0.0)
        value = float(val)
        result = math.atan(value)
        if self.properties.get("Degrees", self.properties.get("Degrees", False)):
            result = math.degrees(result)
        self.bridge.set(f"{self.node_id}_Result", result, self.name)
        self.bridge.set(f"{self.node_id}_ActivePorts", ["Flow"], self.name)
        return True

@NodeRegistry.register("Atan2", "Math/Trigonometry")
class Atan2Node(SuperNode):
    """
    Calculates the arc tangent of Y/X, handling quadrant information correctly.
    Ensures a result in the full 360-degree (2*pi) range.
    
    Inputs:
    - Flow: Trigger the calculation.
    - Y: The y-coordinate value.
    - X: The x-coordinate value.
    
    Outputs:
    - Flow: Triggered after calculation.
    - Result: The angle in radians (or degrees if the Degrees property is set).
    """
    version = "2.1.0"

    def __init__(self, node_id, name, bridge):
        super().__init__(node_id, name, bridge)
        self.is_native = True
        self.properties["Degrees"] = False
        self.properties["Y"] = 0.0
        self.properties["X"] = 1.0
        self.define_schema()
        self.register_handlers()

    def define_schema(self):
        self.input_schema = {
            "Flow": DataType.FLOW,
            "Y": DataType.FLOAT,
            "X": DataType.FLOAT
        }
        self.output_schema = {
            "Flow": DataType.FLOW,
            "Result": DataType.FLOAT
        }

    def register_handlers(self):
        self.register_handler("Flow", self.calculate_atan2)

    def calculate_atan2(self, X=None, Y=None, **kwargs):
        y = float(Y) if Y is not None else float(self.properties.get("Y", 0.0))
        x = float(X) if X is not None else float(self.properties.get("X", 1.0))
        result = math.atan2(y, x)
        if self.properties.get("Degrees", self.properties.get("Degrees", False)):
            result = math.degrees(result)
        self.bridge.set(f"{self.node_id}_Result", result, self.name)
        self.bridge.set(f"{self.node_id}_ActivePorts", ["Flow"], self.name)
        return True

@NodeRegistry.register("Degrees To Radians", "Math/Trigonometry")
class DegreesToRadiansNode(SuperNode):
    """
    Converts an angle from degrees to radians.
    
    Inputs:
    - Flow: Trigger the conversion.
    - Degrees: The angle in degrees.
    
    Outputs:
    - Flow: Triggered after conversion.
    - Result: The angle in radians.
    """
    version = "2.1.0"

    def __init__(self, node_id, name, bridge):
        super().__init__(node_id, name, bridge)
        self.is_native = True
        self.properties["Degrees"] = 0.0
        self.define_schema()
        self.register_handlers()

    def define_schema(self):
        self.input_schema = {"Flow": DataType.FLOW, "Degrees": DataType.FLOAT}
        self.output_schema = {"Flow": DataType.FLOW, "Result": DataType.FLOAT}

    def register_handlers(self):
        self.register_handler("Flow", self.convert)

    def convert(self, Degrees=None, **kwargs):
        val = Degrees if Degrees is not None else self.properties.get("Degrees", 0.0)
        self.bridge.set(f"{self.node_id}_Result", math.radians(float(val)), self.name)
        self.bridge.set(f"{self.node_id}_ActivePorts", ["Flow"], self.name)
        return True

@NodeRegistry.register("Radians To Degrees", "Math/Trigonometry")
class RadiansToDegreesNode(SuperNode):
    """
    Converts an angle from radians to degrees.
    
    Inputs:
    - Flow: Trigger the conversion.
    - Radians: The angle in radians.
    
    Outputs:
    - Flow: Triggered after conversion.
    - Result: The angle in degrees.
    """
    version = "2.1.0"

    def __init__(self, node_id, name, bridge):
        super().__init__(node_id, name, bridge)
        self.is_native = True
        self.properties["Radians"] = 0.0
        self.define_schema()
        self.register_handlers()

    def define_schema(self):
        self.input_schema = {"Flow": DataType.FLOW, "Radians": DataType.FLOAT}
        self.output_schema = {"Flow": DataType.FLOW, "Result": DataType.FLOAT}

    def register_handlers(self):
        self.register_handler("Flow", self.convert)

    def convert(self, Radians=None, **kwargs):
        val = Radians if Radians is not None else self.properties.get("Radians", 0.0)
        self.bridge.set(f"{self.node_id}_Result", math.degrees(float(val)), self.name)
        self.bridge.set(f"{self.node_id}_ActivePorts", ["Flow"], self.name)
        return True

@NodeRegistry.register("Sinh", "Math/Hyperbolic")
class SinhNode(SuperNode):
    """
    Calculates the hyperbolic sine of a given value.
    
    Inputs:
    - Flow: Trigger the calculation.
    - Value: The input value.
    
    Outputs:
    - Flow: Triggered after calculation.
    - Result: The hyperbolic sine.
    """
    version = "2.1.0"
    def __init__(self, node_id, name, bridge):
        super().__init__(node_id, name, bridge)
        self.properties["Value"] = 0.0
        self.define_schema()
        self.register_handlers()
    def define_schema(self):
        self.input_schema = {"Flow": DataType.FLOW, "Value": DataType.FLOAT}
        self.output_schema = {"Flow": DataType.FLOW, "Result": DataType.FLOAT}
    def register_handlers(self):
        self.register_handler("Flow", self.calc)
    def calc(self, Value=None, **kwargs):
        val = Value if Value is not None else self.properties.get("Value", 0.0)
        self.bridge.set(f"{self.node_id}_Result", math.sinh(float(val)), self.name)
        self.bridge.set(f"{self.node_id}_ActivePorts", ["Flow"], self.name)
        return True

@NodeRegistry.register("Cosh", "Math/Hyperbolic")
class CoshNode(SuperNode):
    """
    Calculates the hyperbolic cosine of a given value.
    
    Inputs:
    - Flow: Trigger the calculation.
    - Value: The input value.
    
    Outputs:
    - Flow: Triggered after calculation.
    - Result: The hyperbolic cosine.
    """
    version = "2.1.0"
    def __init__(self, node_id, name, bridge):
        super().__init__(node_id, name, bridge)
        self.properties["Value"] = 0.0
        self.define_schema()
        self.register_handlers()
    def define_schema(self):
        self.input_schema = {"Flow": DataType.FLOW, "Value": DataType.FLOAT}
        self.output_schema = {"Flow": DataType.FLOW, "Result": DataType.FLOAT}
    def register_handlers(self):
        self.register_handler("Flow", self.calc)
    def calc(self, Value=None, **kwargs):
        val = Value if Value is not None else self.properties.get("Value", 0.0)
        self.bridge.set(f"{self.node_id}_Result", math.cosh(float(val)), self.name)
        self.bridge.set(f"{self.node_id}_ActivePorts", ["Flow"], self.name)
        return True

@NodeRegistry.register("Tanh", "Math/Hyperbolic")
class TanhNode(SuperNode):
    """
    Calculates the hyperbolic tangent of a given value.
    
    Inputs:
    - Flow: Trigger the calculation.
    - Value: The input value.
    
    Outputs:
    - Flow: Triggered after calculation.
    - Result: The hyperbolic tangent.
    """
    version = "2.1.0"
    def __init__(self, node_id, name, bridge):
        super().__init__(node_id, name, bridge)
        self.properties["Value"] = 0.0
        self.define_schema()
        self.register_handlers()
    def define_schema(self):
        self.input_schema = {"Flow": DataType.FLOW, "Value": DataType.FLOAT}
        self.output_schema = {"Flow": DataType.FLOW, "Result": DataType.FLOAT}
    def register_handlers(self):
        self.register_handler("Flow", self.calc)
    def calc(self, Value=None, **kwargs):
        val = Value if Value is not None else self.properties.get("Value", 0.0)
        self.bridge.set(f"{self.node_id}_Result", math.tanh(float(val)), self.name)
        self.bridge.set(f"{self.node_id}_ActivePorts", ["Flow"], self.name)
        return True
