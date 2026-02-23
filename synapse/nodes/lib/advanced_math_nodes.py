from synapse.core.super_node import SuperNode
from synapse.nodes.registry import NodeRegistry
from synapse.core.types import DataType
import math

@NodeRegistry.register("Power", "Math/Advanced")
class PowerNode(SuperNode):
    """
    Calculates the power of a base number raised to an exponent.
    Supports negative exponents and fractional bases.
    
    Inputs:
    - Flow: Trigger the calculation.
    - Base: The number to be raised.
    - Exponent: The power to raise the base to.
    
    Outputs:
    - Flow: Triggered after calculation.
    - Result: The calculated power.
    """
    version = "2.1.0"

    def __init__(self, node_id, name, bridge):
        super().__init__(node_id, name, bridge)
        self.is_native = True
        self.properties["Base"] = 0.0
        self.properties["Exponent"] = 1.0
        self.define_schema()
        self.register_handlers()

    def define_schema(self):
        self.input_schema = {
            "Flow": DataType.FLOW,
            "Base": DataType.FLOAT,
            "Exponent": DataType.FLOAT
        }
        self.output_schema = {
            "Flow": DataType.FLOW,
            "Result": DataType.FLOAT
        }

    def register_handlers(self):
        self.register_handler("Flow", self.calculate_power)

    def calculate_power(self, Base=None, Exponent=None, **kwargs):
        base = Base if Base is not None else self.properties.get("Base", self.properties.get("Base", 0.0))
        exponent = Exponent if Exponent is not None else self.properties.get("Exponent", self.properties.get("Exponent", 1.0))
        try:
            result = math.pow(base, exponent)
            self.bridge.set(f"{self.node_id}_Result", result, self.name)
        except Exception as e:
            self.logger.warning(f"Power Error: {e}")
            self.bridge.set(f"{self.node_id}_Result", 0.0, self.name)
        self.bridge.set(f"{self.node_id}_ActivePorts", ["Flow"], self.name)
        return True

@NodeRegistry.register("Sqrt", "Math/Advanced")
class SqrtNode(SuperNode):
    """
    Calculates the square root of a given numerical value.
    Ensures the input is non-negative (clamped to 0) to avoid imaginary results.
    
    Inputs:
    - Flow: Trigger the calculation.
    - Value: The number to process.
    
    Outputs:
    - Flow: Triggered after calculation.
    - Result: The square root of the input.
    """
    version = "2.1.0"

    def __init__(self, node_id, name, bridge):
        super().__init__(node_id, name, bridge)
        self.is_native = True
        self.properties["Value"] = 0.0
        self.define_schema()
        self.register_handlers()

    def define_schema(self):
        self.input_schema = {
            "Flow": DataType.FLOW,
            "Value": DataType.FLOAT
        }
        self.output_schema = {
            "Flow": DataType.FLOW,
            "Result": DataType.FLOAT
        }

    def register_handlers(self):
        self.register_handler("Flow", self.calculate_sqrt)

    def calculate_sqrt(self, Value=None, **kwargs):
        val = Value if Value is not None else self.properties.get("Value", self.properties.get("Value", 0.0))
        try:
            result = math.sqrt(max(0, val))
            self.bridge.set(f"{self.node_id}_Result", result, self.name)
        except Exception as e:
            self.logger.warning(f"Sqrt Error: {e}")
            self.bridge.set(f"{self.node_id}_Result", 0.0, self.name)
        self.bridge.set(f"{self.node_id}_ActivePorts", ["Flow"], self.name)
        return True

@NodeRegistry.register("Logarithm", "Math/Advanced")
class LogarithmNode(SuperNode):
    """
    Calculates the logarithm of a value to a specified base.
    Handles mathematical undefined cases (non-positive values) through an Error Flow.
    
    Inputs:
    - Flow: Trigger the calculation.
    - Value: The positive number to calculate the log for.
    - Base: The logarithmic base (defaults to e).
    
    Outputs:
    - Flow: Triggered after success.
    - Result: The calculated logarithm.
    - Error Flow: Triggered if the input is non-positive or calculation fails.
    """
    version = "2.1.0"

    def __init__(self, node_id, name, bridge):
        super().__init__(node_id, name, bridge)
        self.is_native = True
        self.properties["Value"] = 1.0
        self.properties["Base"] = math.e
        self.properties["Precision"] = 8
        self.define_schema()
        self.register_handlers()
        
    def define_schema(self):
        self.input_schema = {
            "Flow": DataType.FLOW,
            "Value": DataType.FLOAT,
            "Base": DataType.FLOAT,
            "Precision": DataType.NUMBER
        }
        self.output_schema = {
            "Flow": DataType.FLOW,
            "Result": DataType.FLOAT,
            "Error Flow": DataType.FLOW
        }

    def register_handlers(self):
        self.register_handler("Flow", self.calculate_log)

    def calculate_log(self, Value=None, Base=None, Precision=None, **kwargs):
        val = Value if Value is not None else self.properties.get("Value", self.properties.get("Value", 1.0))
        base = Base if Base is not None else self.properties.get("Base", self.properties.get("Base", math.e))
        precision = int(Precision if Precision is not None else self.properties.get("Precision", 8))
        
        if val <= 0:
            self.logger.error(f"Math Error: Logarithm of non-positive number ({val}) is undefined.")
            self.bridge.set(f"{self.node_id}_ActivePorts", ["Error Flow"], self.name)
            return True
            
        try:
            result = math.log(val, base)
            if precision >= 0: result = round(result, precision)
            self.bridge.set(f"{self.node_id}_Result", result, self.name)
            self.bridge.set(f"{self.node_id}_ActivePorts", ["Flow"], self.name)
        except Exception as e:
            self.logger.error(f"Calculation Error: {e}")
            self.bridge.set(f"{self.node_id}_ActivePorts", ["Error Flow"], self.name)
        return True


@NodeRegistry.register("Log10", "Math/Advanced")
class Log10Node(SuperNode):
    """
    Calculates the base-10 logarithm of a given value.
    Input must be a positive number.
    
    Inputs:
    - Flow: Trigger the calculation.
    - Value: The positive number to process.
    
    Outputs:
    - Flow: Triggered after calculation.
    - Result: The base-10 logarithm.
    """
    version = "2.1.0"

    def __init__(self, node_id, name, bridge):
        super().__init__(node_id, name, bridge)
        self.is_native = True
        self.properties["Value"] = 1.0
        self.define_schema()
        self.register_handlers()
    
    def define_schema(self):
        self.input_schema = {
            "Flow": DataType.FLOW,
            "Value": DataType.FLOAT
        }
        self.output_schema = {
            "Flow": DataType.FLOW,
            "Result": DataType.FLOAT
        }

    def register_handlers(self):
        self.register_handler("Flow", self.calculate_log10)

    def calculate_log10(self, Value=None, **kwargs):
        val = Value if Value is not None else self.properties.get("Value", self.properties.get("Value", 1.0))
        if val <= 0:
            self.logger.error(f"Math Error: Logarithm of non-positive number ({val}) is undefined.")
            return True
        try:
            result = math.log10(val)
            self.bridge.set(f"{self.node_id}_Result", result, self.name)
        except Exception as e:
            self.logger.error(f"Calculation Error: {e}")
            self.bridge.set(f"{self.node_id}_Result", 0.0, self.name)
        self.bridge.set(f"{self.node_id}_ActivePorts", ["Flow"], self.name)
        return True

@NodeRegistry.register("Exp", "Math/Advanced")
class ExpNode(SuperNode):
    """
    Exponential Function (e^x). Calculates the result of Euler's number (e ≈ 2.71828) raised to the power of the input 'Value'.
    
    This node is the inverse of the natural logarithm (LN). It is fundamental in modeling processes that grow or decay 
    proportionally to their current value, such as population dynamics, radioactive decay, and continuously compounded interest.
    
    Inputs:
    - Flow: Trigger the calculation.
    - Value: The exponent (x) for 'e'.
    
    Outputs:
    - Flow: Triggered after calculation completion.
    - Result: The calculated value (e^Value).
    """
    version = "2.1.0"

    def __init__(self, node_id, name, bridge):
        super().__init__(node_id, name, bridge)
        self.is_native = True
        self.properties["Value"] = 0.0
        self.define_schema()
        self.register_handlers()
    
    def define_schema(self):
        self.input_schema = {
            "Flow": DataType.FLOW,
            "Value": DataType.FLOAT
        }
        self.output_schema = {
            "Flow": DataType.FLOW,
            "Result": DataType.FLOAT
        }

    def register_handlers(self):
        self.register_handler("Flow", self.calculate_exp)

    def calculate_exp(self, Value=None, **kwargs):
        val = Value if Value is not None else self.properties.get("Value", self.properties.get("Value", 0.0))
        try:
            result = math.exp(val)
            self.bridge.set(f"{self.node_id}_Result", result, self.name)
        except Exception as e:
            self.logger.warning(f"Exp Error: {e}")
            self.bridge.set(f"{self.node_id}_Result", 0.0, self.name)
        self.bridge.set(f"{self.node_id}_ActivePorts", ["Flow"], self.name)
        return True

@NodeRegistry.register("Abs", "Math/Arithmetic")
class AbsNode(SuperNode):
    """
    Calculates the absolute value (magnitude) of a numerical input.
    Ensures the result is non-negative.
    
    Inputs:
    - Flow: Trigger the calculation.
    - Value: The number to process.
    
    Outputs:
    - Flow: Triggered after calculation.
    - Result: The absolute value of the input.
    """
    version = "2.1.0"

    def __init__(self, node_id, name, bridge):
        super().__init__(node_id, name, bridge)
        self.is_native = True
        self.properties["Value"] = 0.0
        self.define_schema()
        self.register_handlers()
    
    def define_schema(self):
        self.input_schema = {
            "Flow": DataType.FLOW,
            "Value": DataType.FLOAT
        }
        self.output_schema = {
            "Flow": DataType.FLOW,
            "Result": DataType.FLOAT
        }

    def register_handlers(self):
        self.register_handler("Flow", self.calculate_abs)

    def calculate_abs(self, Value=None, **kwargs):
        val = Value if Value is not None else self.properties.get("Value", self.properties.get("Value", 0.0))
        self.bridge.set(f"{self.node_id}_Result", abs(val), self.name)
        self.bridge.set(f"{self.node_id}_ActivePorts", ["Flow"], self.name)
        return True


@NodeRegistry.register("Floor", "Math/Rounding")
class FloorNode(SuperNode):
    """
    Rounds a numerical value down to the nearest integer that is less than or equal to the input.
    
    Unlike standard rounding which may round up or down depending on the decimal part, Floor always moves 
    the value towards negative infinity. 
    Example: 3.7 -> 3.0, -3.2 -> -4.0.
    
    Inputs:
    - Flow: Trigger the floor operation.
    - Value: The number to round down.
    
    Outputs:
    - Flow: Triggered after the value is processed.
    - Result: The largest integer less than or equal to 'Value'.
    """
    version = "2.1.0"

    def __init__(self, node_id, name, bridge):
        super().__init__(node_id, name, bridge)
        self.is_native = True
        self.properties["Value"] = 0.0
        self.define_schema()
        self.register_handlers()
    
    def define_schema(self):
        self.input_schema = {
            "Flow": DataType.FLOW,
            "Value": DataType.FLOAT
        }
        self.output_schema = {
            "Flow": DataType.FLOW,
            "Result": DataType.INT
        }

    def register_handlers(self):
        self.register_handler("Flow", self.calculate_floor)

    def calculate_floor(self, Value=None, **kwargs):
        val = Value if Value is not None else self.properties.get("Value", self.properties.get("Value", 0.0))
        self.bridge.set(f"{self.node_id}_Result", math.floor(val), self.name)
        self.bridge.set(f"{self.node_id}_ActivePorts", ["Flow"], self.name)
        return True

@NodeRegistry.register("Ceil", "Math/Rounding")
class CeilNode(SuperNode):
    """
    Rounds a numerical value up to the nearest integer.
    
    Inputs:
    - Flow: Trigger the ceiling operation.
    - Value: The number to round up.
    
    Outputs:
    - Flow: Triggered after rounding.
    - Result: The resulting integer.
    """
    version = "2.1.0"

    def __init__(self, node_id, name, bridge):
        super().__init__(node_id, name, bridge)
        self.is_native = True
        self.properties["Value"] = 0.0
        self.define_schema()
        self.register_handlers()
    
    def define_schema(self):
        self.input_schema = {
            "Flow": DataType.FLOW,
            "Value": DataType.FLOAT
        }
        self.output_schema = {
            "Flow": DataType.FLOW,
            "Result": DataType.INT
        }

    def register_handlers(self):
        self.register_handler("Flow", self.calculate_ceil)

    def calculate_ceil(self, Value=None, **kwargs):
        val = Value if Value is not None else self.properties.get("Value", self.properties.get("Value", 0.0))
        self.bridge.set(f"{self.node_id}_Result", math.ceil(val), self.name)
        self.bridge.set(f"{self.node_id}_ActivePorts", ["Flow"], self.name)
        return True

@NodeRegistry.register("Round", "Math/Rounding")
class RoundNode(SuperNode):
    """
    Rounds a numerical value to a specified number of decimal places.
    
    Inputs:
    - Flow: Trigger the round operation.
    - Value: The number to round.
    - Decimals: The number of decimal places to keep.
    
    Outputs:
    - Flow: Triggered after rounding.
    - Result: The rounded number.
    """
    version = "2.1.0"

    def __init__(self, node_id, name, bridge):
        super().__init__(node_id, name, bridge)
        self.is_native = True
        self.properties["Value"] = 0.0
        self.properties["Decimals"] = 0
        self.define_schema()
        self.register_handlers()
    
    def define_schema(self):
        self.input_schema = {
            "Flow": DataType.FLOW,
            "Value": DataType.FLOAT,
            "Decimals": DataType.INT
        }
        self.output_schema = {
            "Flow": DataType.FLOW,
            "Result": DataType.FLOAT
        }

    def register_handlers(self):
        self.register_handler("Flow", self.calculate_round)

    def calculate_round(self, Value=None, Decimals=None, **kwargs):
        val = Value if Value is not None else self.properties.get("Value", self.properties.get("Value", 0.0))
        decimals = Decimals if Decimals is not None else self.properties.get("Decimals", self.properties.get("Decimals", 0))
        try:
            self.bridge.set(f"{self.node_id}_Result", round(val, int(decimals)), self.name)
        except:
             self.bridge.set(f"{self.node_id}_Result", round(val), self.name)
        self.bridge.set(f"{self.node_id}_ActivePorts", ["Flow"], self.name)
        return True


@NodeRegistry.register("Modulo", "Math/Arithmetic")
class ModuloNode(SuperNode):
    """
    Calculates the remainder of a division (modulo operation).
    
    Inputs:
    - Flow: Trigger the calculation.
    - A: The dividend.
    - B: The divisor.
    
    Outputs:
    - Flow: Triggered after calculation.
    - Result: A modulo B.
    """
    version = "2.1.0"

    def __init__(self, node_id, name, bridge):
        super().__init__(node_id, name, bridge)
        self.is_native = True
        self.properties["A"] = 0.0
        self.properties["B"] = 1.0
        self.define_schema()
        self.register_handlers()
    
    def define_schema(self):
        self.input_schema = {
            "Flow": DataType.FLOW,
            "A": DataType.FLOAT,
            "B": DataType.FLOAT
        }
        self.output_schema = {
            "Flow": DataType.FLOW,
            "Result": DataType.FLOAT
        }

    def register_handlers(self):
        self.register_handler("Flow", self.calculate_modulo)

    def calculate_modulo(self, A=None, B=None, **kwargs):
        val_a = A if A is not None else self.properties.get("A", self.properties.get("A", 0.0))
        val_b = B if B is not None else self.properties.get("B", self.properties.get("B", 1.0))
        if val_b == 0:
            result = 0
            self.logger.warning("Modulo by zero!")
        else:
            result = val_a % val_b
        self.bridge.set(f"{self.node_id}_Result", result, self.name)
        self.bridge.set(f"{self.node_id}_ActivePorts", ["Flow"], self.name)
        return True

@NodeRegistry.register("Min", "Math/Advanced")
class MinNode(SuperNode):
    """
    Returns the smaller of two numerical inputs.
    
    Inputs:
    - Flow: Trigger the comparison.
    - A: First number.
    - B: Second number.
    
    Outputs:
    - Flow: Triggered after comparison.
    - Result: The minimum of A and B.
    """
    version = "2.1.0"

    def __init__(self, node_id, name, bridge):
        super().__init__(node_id, name, bridge)
        self.is_native = True
        self.properties["A"] = 0.0
        self.properties["B"] = 0.0
        self.define_schema()
        self.register_handlers()
    
    def define_schema(self):
        self.input_schema = {
            "Flow": DataType.FLOW,
            "A": DataType.FLOAT,
            "B": DataType.FLOAT
        }
        self.output_schema = {
            "Flow": DataType.FLOW,
            "Result": DataType.FLOAT
        }

    def register_handlers(self):
        self.register_handler("Flow", self.calculate_min)

    def calculate_min(self, A=None, B=None, **kwargs):
        val_a = A if A is not None else self.properties.get("A", self.properties.get("A", 0.0))
        val_b = B if B is not None else self.properties.get("B", self.properties.get("B", 0.0))
        self.bridge.set(f"{self.node_id}_Result", min(val_a, val_b), self.name)
        self.bridge.set(f"{self.node_id}_ActivePorts", ["Flow"], self.name)
        return True


@NodeRegistry.register("Max", "Math/Advanced")
class MaxNode(SuperNode):
    """
    Returns the larger of two numerical inputs.
    
    Inputs:
    - Flow: Trigger the comparison.
    - A: First number.
    - B: Second number.
    
    Outputs:
    - Flow: Triggered after comparison.
    - Result: The maximum of A and B.
    """
    version = "2.1.0"

    def __init__(self, node_id, name, bridge):
        super().__init__(node_id, name, bridge)
        self.is_native = True
        self.properties["A"] = 0.0
        self.properties["B"] = 0.0
        self.define_schema()
        self.register_handlers()

    def define_schema(self):
        self.input_schema = {
            "Flow": DataType.FLOW,
            "A": DataType.FLOAT,
            "B": DataType.FLOAT
        }
        self.output_schema = {
            "Flow": DataType.FLOW,
            "Result": DataType.FLOAT
        }

    def register_handlers(self):
        self.register_handler("Flow", self.calculate_max)

    def calculate_max(self, A=None, B=None, **kwargs):
        val_a = A if A is not None else self.properties.get("A", self.properties.get("A", 0.0))
        val_b = B if B is not None else self.properties.get("B", self.properties.get("B", 0.0))
        self.bridge.set(f"{self.node_id}_Result", max(val_a, val_b), self.name)
        self.bridge.set(f"{self.node_id}_ActivePorts", ["Flow"], self.name)
        return True

@NodeRegistry.register("Clamp", "Math/Advanced")
class ClampNode(SuperNode):
    """
    Restricts a numerical value to a defined range [Min, Max].
    If the value is outside the range, it is set to the nearest boundary.
    
    Inputs:
    - Flow: Trigger the clamp operation.
    - Value: The number to restrict.
    - Min: The lower boundary.
    - Max: The upper boundary.
    
    Outputs:
    - Flow: Triggered after processing.
    - Result: The clamped value.
    """
    version = "2.1.0"

    def __init__(self, node_id, name, bridge):
        super().__init__(node_id, name, bridge)
        self.is_native = True
        self.properties["Value"] = 0.0
        self.properties["Min"] = 0.0
        self.properties["Max"] = 1.0
        self.define_schema()
        self.register_handlers()
    
    def define_schema(self):
        self.input_schema = {
            "Flow": DataType.FLOW,
            "Value": DataType.FLOAT,
            "Min": DataType.FLOAT,
            "Max": DataType.FLOAT
        }
        self.output_schema = {
            "Flow": DataType.FLOW,
            "Result": DataType.FLOAT
        }

    def register_handlers(self):
        self.register_handler("Flow", self.calculate_clamp)

    def calculate_clamp(self, Value=None, Min=None, Max=None, **kwargs):
        val = Value if Value is not None else self.properties.get("Value", self.properties.get("Value", 0.0))
        min_val = Min if Min is not None else self.properties.get("Min", self.properties.get("Min", 0.0))
        max_val = Max if Max is not None else self.properties.get("Max", self.properties.get("Max", 1.0))
        result = max(min_val, min(max_val, val))
        self.bridge.set(f"{self.node_id}_Result", result, self.name)
        self.bridge.set(f"{self.node_id}_ActivePorts", ["Flow"], self.name)
        return True

@NodeRegistry.register("Pi", "Math/Constants")
class PiNode(SuperNode):
    """
    Outputs the mathematical constant Pi (3.14159...).
    
    Inputs:
    - Flow: Trigger the output.
    
    Outputs:
    - Flow: Triggered after output.
    - Result: The value of Pi.
    """
    version = "2.1.0"

    def __init__(self, node_id, name, bridge):
        super().__init__(node_id, name, bridge)
        self.is_native = True
        self.define_schema()
        self.register_handlers()
    
    def define_schema(self):
        self.input_schema = {"Flow": DataType.FLOW}
        self.output_schema = {"Flow": DataType.FLOW, "Result": DataType.FLOAT}

    def register_handlers(self):
        self.register_handler("Flow", self.output_pi)

    def output_pi(self, **kwargs):
        self.bridge.set(f"{self.node_id}_Result", math.pi, self.name)
        self.bridge.set(f"{self.node_id}_ActivePorts", ["Flow"], self.name)
        return True

@NodeRegistry.register("E", "Math/Constants")
class ENode(SuperNode):
    """
    Outputs the mathematical constant e (Euler's number, 2.71828...).
    
    Inputs:
    - Flow: Trigger the output.
    
    Outputs:
    - Flow: Triggered after output.
    - Result: The value of e.
    """
    version = "2.1.0"

    def __init__(self, node_id, name, bridge):
        super().__init__(node_id, name, bridge)
        self.is_native = True
        self.define_schema()
        self.register_handlers()
    
    def define_schema(self):
        self.input_schema = {"Flow": DataType.FLOW}
        self.output_schema = {"Flow": DataType.FLOW, "Result": DataType.FLOAT}

    def register_handlers(self):
        self.register_handler("Flow", self.output_e)

    def output_e(self, **kwargs):
        self.bridge.set(f"{self.node_id}_Result", math.e, self.name)
        self.bridge.set(f"{self.node_id}_ActivePorts", ["Flow"], self.name)
        return True
