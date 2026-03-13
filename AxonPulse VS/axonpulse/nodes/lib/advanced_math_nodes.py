from axonpulse.core.super_node import SuperNode

from axonpulse.nodes.registry import NodeRegistry

from axonpulse.core.types import DataType

import math

from typing import Any, List, Dict, Optional

from axonpulse.core.types import DataType, TypeCaster

from axonpulse.nodes.decorators import axon_node

@axon_node(category="Math/Advanced", version="2.3.0", node_label="Power")
def PowerNode(Base: Any = 0.0, Exponent: Any = 1.0, _bridge: Any = None, _node: Any = None, _node_id: str = None, **kwargs) -> Any:
    """Calculates the power of a base number raised to an exponent.
Supports negative exponents and fractional bases.

Inputs:
- Flow: Trigger the calculation.
- Base: The number to be raised.
- Exponent: The power to raise the base to.

Outputs:
- Flow: Triggered after calculation.
- Result: The calculated power."""
    base = Base if Base is not None else _node.properties.get('Base', _node.properties.get('Base', 0.0))
    exponent = Exponent if Exponent is not None else _node.properties.get('Exponent', _node.properties.get('Exponent', 1.0))
    try:
        result = math.pow(base, exponent)
    except Exception as e:
        _node.logger.warning(f'Power Error: {e}')
    finally:
        pass
    _bridge.set(f'{_node_id}_ActivePorts', ['Flow'], _node.name)
    return 0.0


@axon_node(category="Math/Advanced", version="2.3.0", node_label="Sqrt")
def SqrtNode(Value: Any = 0.0, _bridge: Any = None, _node: Any = None, _node_id: str = None, **kwargs) -> Any:
    """Calculates the square root of a given numerical value.
Ensures the input is non-negative (clamped to 0) to avoid imaginary results.

Inputs:
- Flow: Trigger the calculation.
- Value: The number to process.

Outputs:
- Flow: Triggered after calculation.
- Result: The square root of the input."""
    val = Value if Value is not None else _node.properties.get('Value', _node.properties.get('Value', 0.0))
    try:
        result = math.sqrt(max(0, val))
    except Exception as e:
        _node.logger.warning(f'Sqrt Error: {e}')
    finally:
        pass
    _bridge.set(f'{_node_id}_ActivePorts', ['Flow'], _node.name)
    return 0.0


@axon_node(category="Math/Advanced", version="2.3.0", node_label="Logarithm", outputs=['Result', 'Error Flow'])
def LogarithmNode(Value: Any = 1.0, Base: Any = math.e, Precision: float = 8, _bridge: Any = None, _node: Any = None, _node_id: str = None, **kwargs) -> Any:
    """Calculates the logarithm of a value to a specified base.
Handles mathematical undefined cases (non-positive values) through an Error Flow.

Inputs:
- Flow: Trigger the calculation.
- Value: The positive number to calculate the log for.
- Base: The logarithmic base (defaults to e).

Outputs:
- Flow: Triggered after success.
- Result: The calculated logarithm.
- Error Flow: Triggered if the input is non-positive or calculation fails."""
    val = Value if Value is not None else _node.properties.get('Value', _node.properties.get('Value', 1.0))
    base = Base if Base is not None else _node.properties.get('Base', _node.properties.get('Base', math.e))
    precision = int(Precision if Precision is not None else _node.properties.get('Precision', 8))
    if val <= 0:
        _node.logger.error(f'Math Error: Logarithm of non-positive number ({val}) is undefined.')
        _bridge.set(f'{_node_id}_ActivePorts', ['Error Flow'], _node.name)
    else:
        pass
    try:
        result = math.log(val, base)
        if precision >= 0:
            result = round(result, precision)
        else:
            pass
        _bridge.set(f'{_node_id}_ActivePorts', ['Flow'], _node.name)
    except Exception as e:
        _node.logger.error(f'Calculation Error: {e}')
        _bridge.set(f'{_node_id}_ActivePorts', ['Error Flow'], _node.name)
    finally:
        pass
    return {'Result': result}


@axon_node(category="Math/Advanced", version="2.3.0", node_label="Log10")
def Log10Node(Value: Any = 1.0, _bridge: Any = None, _node: Any = None, _node_id: str = None, **kwargs) -> Any:
    """Calculates the base-10 logarithm of a given value.
Input must be a positive number.

Inputs:
- Flow: Trigger the calculation.
- Value: The positive number to process.

Outputs:
- Flow: Triggered after calculation.
- Result: The base-10 logarithm."""
    val = Value if Value is not None else _node.properties.get('Value', _node.properties.get('Value', 1.0))
    if val <= 0:
        _node.logger.error(f'Math Error: Logarithm of non-positive number ({val}) is undefined.')
    else:
        pass
    try:
        result = math.log10(val)
    except Exception as e:
        _node.logger.error(f'Calculation Error: {e}')
    finally:
        pass
    _bridge.set(f'{_node_id}_ActivePorts', ['Flow'], _node.name)
    return 0.0


@axon_node(category="Math/Advanced", version="2.3.0", node_label="Exp")
def ExpNode(Value: Any = 0.0, _bridge: Any = None, _node: Any = None, _node_id: str = None, **kwargs) -> Any:
    """Exponential Function (e^x). Calculates the result of Euler's number (e ≈ 2.71828) raised to the power of the input 'Value'.

This node is the inverse of the natural logarithm (LN). It is fundamental in modeling processes that grow or decay 
proportionally to their current value, such as population dynamics, radioactive decay, and continuously compounded interest.

Inputs:
- Flow: Trigger the calculation.
- Value: The exponent (x) for 'e'.

Outputs:
- Flow: Triggered after calculation completion.
- Result: The calculated value (e^Value)."""
    val = Value if Value is not None else _node.properties.get('Value', _node.properties.get('Value', 0.0))
    try:
        result = math.exp(val)
    except Exception as e:
        _node.logger.warning(f'Exp Error: {e}')
    finally:
        pass
    _bridge.set(f'{_node_id}_ActivePorts', ['Flow'], _node.name)
    return 0.0


@axon_node(category="Math/Arithmetic", version="2.3.0", node_label="Abs")
def AbsNode(Value: Any = 0.0, _bridge: Any = None, _node: Any = None, _node_id: str = None, **kwargs) -> Any:
    """Calculates the absolute value (magnitude) of a numerical input.
Ensures the result is non-negative.

Inputs:
- Flow: Trigger the calculation.
- Value: The number to process.

Outputs:
- Flow: Triggered after calculation.
- Result: The absolute value of the input."""
    val = Value if Value is not None else _node.properties.get('Value', _node.properties.get('Value', 0.0))
    _bridge.set(f'{_node_id}_ActivePorts', ['Flow'], _node.name)
    return abs(val)


@axon_node(category="Math/Rounding", version="2.3.0", node_label="Floor")
def FloorNode(Value: Any = 0.0, _bridge: Any = None, _node: Any = None, _node_id: str = None, **kwargs) -> Any:
    """Rounds a numerical value down to the nearest integer that is less than or equal to the input.

Unlike standard rounding which may round up or down depending on the decimal part, Floor always moves 
the value towards negative infinity. 
Example: 3.7 -> 3.0, -3.2 -> -4.0.

Inputs:
- Flow: Trigger the floor operation.
- Value: The number to round down.

Outputs:
- Flow: Triggered after the value is processed.
- Result: The largest integer less than or equal to 'Value'."""
    val = Value if Value is not None else _node.properties.get('Value', _node.properties.get('Value', 0.0))
    _bridge.set(f'{_node_id}_ActivePorts', ['Flow'], _node.name)
    return math.floor(val)


@axon_node(category="Math/Rounding", version="2.3.0", node_label="Ceil")
def CeilNode(Value: Any = 0.0, _bridge: Any = None, _node: Any = None, _node_id: str = None, **kwargs) -> Any:
    """Rounds a numerical value up to the nearest integer.

Inputs:
- Flow: Trigger the ceiling operation.
- Value: The number to round up.

Outputs:
- Flow: Triggered after rounding.
- Result: The resulting integer."""
    val = Value if Value is not None else _node.properties.get('Value', _node.properties.get('Value', 0.0))
    _bridge.set(f'{_node_id}_ActivePorts', ['Flow'], _node.name)
    return math.ceil(val)


@axon_node(category="Math/Rounding", version="2.3.0", node_label="Round")
def RoundNode(Value: Any = 0.0, Decimals: Any = 0, _bridge: Any = None, _node: Any = None, _node_id: str = None, **kwargs) -> Any:
    """Rounds a numerical value to a specified number of decimal places.

Inputs:
- Flow: Trigger the round operation.
- Value: The number to round.
- Decimals: The number of decimal places to keep.

Outputs:
- Flow: Triggered after rounding.
- Result: The rounded number."""
    val = Value if Value is not None else _node.properties.get('Value', _node.properties.get('Value', 0.0))
    decimals = Decimals if Decimals is not None else _node.properties.get('Decimals', _node.properties.get('Decimals', 0))
    try:
        pass
    except:
        pass
    finally:
        pass
    _bridge.set(f'{_node_id}_ActivePorts', ['Flow'], _node.name)
    return round(val)


@axon_node(category="Math/Arithmetic", version="2.3.0", node_label="Modulo")
def ModuloNode(A: Any = 0.0, B: Any = 1.0, _bridge: Any = None, _node: Any = None, _node_id: str = None, **kwargs) -> Any:
    """Calculates the remainder of a division (modulo operation).

Inputs:
- Flow: Trigger the calculation.
- A: The dividend.
- B: The divisor.

Outputs:
- Flow: Triggered after calculation.
- Result: A modulo B."""
    val_a = A if A is not None else _node.properties.get('A', _node.properties.get('A', 0.0))
    val_b = B if B is not None else _node.properties.get('B', _node.properties.get('B', 1.0))
    if val_b == 0:
        result = 0
        _node.logger.warning('Modulo by zero!')
    else:
        result = val_a % val_b
    _bridge.set(f'{_node_id}_ActivePorts', ['Flow'], _node.name)
    return result


@axon_node(category="Math/Advanced", version="2.3.0", node_label="Min")
def MinNode(A: Any = 0.0, B: Any = 0.0, _bridge: Any = None, _node: Any = None, _node_id: str = None, **kwargs) -> Any:
    """Returns the smaller of two numerical inputs.

Inputs:
- Flow: Trigger the comparison.
- A: First number.
- B: Second number.

Outputs:
- Flow: Triggered after comparison.
- Result: The minimum of A and B."""
    val_a = A if A is not None else _node.properties.get('A', _node.properties.get('A', 0.0))
    val_b = B if B is not None else _node.properties.get('B', _node.properties.get('B', 0.0))
    _bridge.set(f'{_node_id}_ActivePorts', ['Flow'], _node.name)
    return min(val_a, val_b)


@axon_node(category="Math/Advanced", version="2.3.0", node_label="Max")
def MaxNode(A: Any = 0.0, B: Any = 0.0, _bridge: Any = None, _node: Any = None, _node_id: str = None, **kwargs) -> Any:
    """Returns the larger of two numerical inputs.

Inputs:
- Flow: Trigger the comparison.
- A: First number.
- B: Second number.

Outputs:
- Flow: Triggered after comparison.
- Result: The maximum of A and B."""
    val_a = A if A is not None else _node.properties.get('A', _node.properties.get('A', 0.0))
    val_b = B if B is not None else _node.properties.get('B', _node.properties.get('B', 0.0))
    _bridge.set(f'{_node_id}_ActivePorts', ['Flow'], _node.name)
    return max(val_a, val_b)


@axon_node(category="Math/Advanced", version="2.3.0", node_label="Clamp")
def ClampNode(Value: Any = 0.0, Min: Any = 0.0, Max: Any = 1.0, _bridge: Any = None, _node: Any = None, _node_id: str = None, **kwargs) -> Any:
    """Restricts a numerical value to a defined range [Min, Max].
If the value is outside the range, it is set to the nearest boundary.

Inputs:
- Flow: Trigger the clamp operation.
- Value: The number to restrict.
- Min: The lower boundary.
- Max: The upper boundary.

Outputs:
- Flow: Triggered after processing.
- Result: The clamped value."""
    val = Value if Value is not None else _node.properties.get('Value', _node.properties.get('Value', 0.0))
    min_val = Min if Min is not None else _node.properties.get('Min', _node.properties.get('Min', 0.0))
    max_val = Max if Max is not None else _node.properties.get('Max', _node.properties.get('Max', 1.0))
    result = max(min_val, min(max_val, val))
    _bridge.set(f'{_node_id}_ActivePorts', ['Flow'], _node.name)
    return result


@axon_node(category="Math/Constants", version="2.3.0", node_label="Pi")
def PiNode(_bridge: Any = None, _node: Any = None, _node_id: str = None, **kwargs) -> Any:
    """Outputs the mathematical constant Pi (3.14159...).

Inputs:
- Flow: Trigger the output.

Outputs:
- Flow: Triggered after output.
- Result: The value of Pi."""
    _bridge.set(f'{_node_id}_ActivePorts', ['Flow'], _node.name)
    return math.pi


@axon_node(category="Math/Constants", version="2.3.0", node_label="E")
def ENode(_bridge: Any = None, _node: Any = None, _node_id: str = None, **kwargs) -> Any:
    """Outputs the mathematical constant e (Euler's number, 2.71828...).

Inputs:
- Flow: Trigger the output.

Outputs:
- Flow: Triggered after output.
- Result: The value of e."""
    _bridge.set(f'{_node_id}_ActivePorts', ['Flow'], _node.name)
    return math.e
