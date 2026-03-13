from axonpulse.core.super_node import SuperNode

from axonpulse.nodes.registry import NodeRegistry

from axonpulse.core.types import DataType

import math

from typing import Any, List, Dict, Optional

from axonpulse.core.types import DataType, TypeCaster

from axonpulse.nodes.decorators import axon_node

@axon_node(category="Math/Trigonometry", version="2.3.0", node_label="Sin")
def SinNode(Angle: Any = 0.0, Degrees: bool = False, _bridge: Any = None, _node: Any = None, _node_id: str = None, **kwargs) -> Any:
    """Calculates the sine of a given angle.

Processes the input 'Angle'. If 'Degrees' is True, the angle is 
treated as degrees and converted to radians before calculation. 
Otherwise, it is treated as radians.

Inputs:
- Flow: Trigger the calculation.
- Angle: The input angle to process.
- Degrees: Whether the angle is in degrees (True) or radians (False).

Outputs:
- Flow: Triggered after calculation.
- Result: The sine of the angle."""
    val = Angle if Angle is not None else _node.properties.get('Angle', 0.0)
    angle = float(val)
    use_degrees = Degrees if Degrees is not None else _node.properties.get('Degrees', False)
    if use_degrees:
        angle = math.radians(angle)
    else:
        pass
    _bridge.set(f'{_node_id}_ActivePorts', ['Flow'], _node.name)
    return math.sin(angle)


@axon_node(category="Math/Trigonometry", version="2.3.0", node_label="Cos")
def CosNode(Angle: Any = 0.0, Degrees: bool = False, _bridge: Any = None, _node: Any = None, _node_id: str = None, **kwargs) -> Any:
    """Calculates the cosine of a given angle.
Supports both Degrees and Radians based on the Degrees property.

Inputs:
- Flow: Trigger the calculation.
- Angle: The input angle to process.

Outputs:
- Flow: Triggered after calculation.
- Result: The cosine of the angle."""
    val = Angle if Angle is not None else _node.properties.get('Angle', 0.0)
    angle = float(val)
    use_degrees = Degrees if Degrees is not None else _node.properties.get('Degrees', False)
    if use_degrees:
        angle = math.radians(angle)
    else:
        pass
    _bridge.set(f'{_node_id}_ActivePorts', ['Flow'], _node.name)
    return math.cos(angle)


@axon_node(category="Math/Trigonometry", version="2.3.0", node_label="Tan")
def TanNode(Angle: Any = 0.0, Degrees: bool = False, _bridge: Any = None, _node: Any = None, _node_id: str = None, **kwargs) -> Any:
    """Calculates the tangent of a given angle.

Processes the input 'Angle'. If 'Degrees' is True, the angle is 
treated as degrees and converted to radians before calculation. 
Otherwise, it is treated as radians.

Inputs:
- Flow: Trigger the calculation.
- Angle: The input angle to process.
- Degrees: Whether the angle is in degrees (True) or radians (False).

Outputs:
- Flow: Triggered after calculation.
- Result: The tangent of the angle."""
    val = Angle if Angle is not None else _node.properties.get('Angle', 0.0)
    angle = float(val)
    use_degrees = Degrees if Degrees is not None else _node.properties.get('Degrees', False)
    if use_degrees:
        angle = math.radians(angle)
    else:
        pass
    _bridge.set(f'{_node_id}_ActivePorts', ['Flow'], _node.name)
    return math.tan(angle)


@axon_node(category="Math/Trigonometry", version="2.3.0", node_label="Asin")
def AsinNode(Value: Any = 0.0, _bridge: Any = None, _node: Any = None, _node_id: str = None, **kwargs) -> Any:
    """Calculates the arc sine (inverse sine) of a value.
The input value must be between -1 and 1.

Inputs:
- Flow: Trigger the calculation.
- Value: The numerical value to process (-1 to 1).

Outputs:
- Flow: Triggered after calculation.
- Result: The angle in radians (or degrees if the Degrees property is set)."""
    val = Value if Value is not None else _node.properties.get('Value', 0.0)
    value = float(val)
    try:
        result = math.asin(max(-1, min(1, value)))
        if _node.properties.get('Degrees', _node.properties.get('Degrees', False)):
            result = math.degrees(result)
        else:
            pass
    except ValueError:
        _node.logger.warning(f'Asin Error: Value {value} out of range -1 to 1')
    finally:
        pass
    _bridge.set(f'{_node_id}_ActivePorts', ['Flow'], _node.name)
    return result


@axon_node(category="Math/Trigonometry", version="2.3.0", node_label="Acos")
def AcosNode(Value: Any = 0.0, _bridge: Any = None, _node: Any = None, _node_id: str = None, **kwargs) -> Any:
    """Calculates the arc cosine (inverse cosine) of a value.
The input value must be between -1 and 1.

Inputs:
- Flow: Trigger the calculation.
- Value: The numerical value to process (-1 to 1).

Outputs:
- Flow: Triggered after calculation.
- Result: The angle in radians (or degrees if the Degrees property is set)."""
    val = Value if Value is not None else _node.properties.get('Value', 0.0)
    value = float(val)
    try:
        result = math.acos(max(-1, min(1, value)))
        if _node.properties.get('Degrees', _node.properties.get('Degrees', False)):
            result = math.degrees(result)
        else:
            pass
    except ValueError:
        _node.logger.warning(f'Acos Error: Value {value} out of range -1 to 1')
    finally:
        pass
    _bridge.set(f'{_node_id}_ActivePorts', ['Flow'], _node.name)
    return result


@axon_node(category="Math/Trigonometry", version="2.3.0", node_label="Atan")
def AtanNode(Value: Any = 0.0, _bridge: Any = None, _node: Any = None, _node_id: str = None, **kwargs) -> Any:
    """Calculates the arc tangent (inverse tangent) of a value.

Inputs:
- Flow: Trigger the calculation.
- Value: The numerical value to process.

Outputs:
- Flow: Triggered after calculation.
- Result: The angle in radians (or degrees if the Degrees property is set)."""
    val = Value if Value is not None else _node.properties.get('Value', 0.0)
    value = float(val)
    result = math.atan(value)
    if _node.properties.get('Degrees', _node.properties.get('Degrees', False)):
        result = math.degrees(result)
    else:
        pass
    _bridge.set(f'{_node_id}_ActivePorts', ['Flow'], _node.name)
    return result


@axon_node(category="Math/Trigonometry", version="2.3.0", node_label="Atan2")
def Atan2Node(Y: Any = 0.0, X: Any = 1.0, _bridge: Any = None, _node: Any = None, _node_id: str = None, **kwargs) -> Any:
    """Calculates the arc tangent of Y/X, handling quadrant information correctly.
Ensures a result in the full 360-degree (2*pi) range.

Inputs:
- Flow: Trigger the calculation.
- Y: The y-coordinate value.
- X: The x-coordinate value.

Outputs:
- Flow: Triggered after calculation.
- Result: The angle in radians (or degrees if the Degrees property is set)."""
    y = float(Y) if Y is not None else float(_node.properties.get('Y', 0.0))
    x = float(X) if X is not None else float(_node.properties.get('X', 1.0))
    result = math.atan2(y, x)
    if _node.properties.get('Degrees', _node.properties.get('Degrees', False)):
        result = math.degrees(result)
    else:
        pass
    _bridge.set(f'{_node_id}_ActivePorts', ['Flow'], _node.name)
    return result


@axon_node(category="Math/Trigonometry", version="2.3.0", node_label="Degrees To Radians")
def DegreesToRadiansNode(Degrees: Any = 0.0, _bridge: Any = None, _node: Any = None, _node_id: str = None, **kwargs) -> Any:
    """Converts an angle from degrees to radians.

Inputs:
- Flow: Trigger the conversion.
- Degrees: The angle in degrees.

Outputs:
- Flow: Triggered after conversion.
- Result: The angle in radians."""
    val = Degrees if Degrees is not None else _node.properties.get('Degrees', 0.0)
    _bridge.set(f'{_node_id}_ActivePorts', ['Flow'], _node.name)
    return math.radians(float(val))


@axon_node(category="Math/Trigonometry", version="2.3.0", node_label="Radians To Degrees")
def RadiansToDegreesNode(Radians: Any = 0.0, _bridge: Any = None, _node: Any = None, _node_id: str = None, **kwargs) -> Any:
    """Converts an angle from radians to degrees.

Inputs:
- Flow: Trigger the conversion.
- Radians: The angle in radians.

Outputs:
- Flow: Triggered after conversion.
- Result: The angle in degrees."""
    val = Radians if Radians is not None else _node.properties.get('Radians', 0.0)
    _bridge.set(f'{_node_id}_ActivePorts', ['Flow'], _node.name)
    return math.degrees(float(val))


@axon_node(category="Math/Hyperbolic", version="2.3.0", node_label="Sinh")
def SinhNode(Value: Any = 0.0, _bridge: Any = None, _node: Any = None, _node_id: str = None, **kwargs) -> Any:
    """Calculates the hyperbolic sine of a given value.

Inputs:
- Flow: Trigger the calculation.
- Value: The input value.

Outputs:
- Flow: Triggered after calculation.
- Result: The hyperbolic sine."""
    val = Value if Value is not None else _node.properties.get('Value', 0.0)
    _bridge.set(f'{_node_id}_ActivePorts', ['Flow'], _node.name)
    return math.sinh(float(val))


@axon_node(category="Math/Hyperbolic", version="2.3.0", node_label="Cosh")
def CoshNode(Value: Any = 0.0, _bridge: Any = None, _node: Any = None, _node_id: str = None, **kwargs) -> Any:
    """Calculates the hyperbolic cosine of a given value.

Inputs:
- Flow: Trigger the calculation.
- Value: The input value.

Outputs:
- Flow: Triggered after calculation.
- Result: The hyperbolic cosine."""
    val = Value if Value is not None else _node.properties.get('Value', 0.0)
    _bridge.set(f'{_node_id}_ActivePorts', ['Flow'], _node.name)
    return math.cosh(float(val))


@axon_node(category="Math/Hyperbolic", version="2.3.0", node_label="Tanh")
def TanhNode(Value: Any = 0.0, _bridge: Any = None, _node: Any = None, _node_id: str = None, **kwargs) -> Any:
    """Calculates the hyperbolic tangent of a given value.

Inputs:
- Flow: Trigger the calculation.
- Value: The input value.

Outputs:
- Flow: Triggered after calculation.
- Result: The hyperbolic tangent."""
    val = Value if Value is not None else _node.properties.get('Value', 0.0)
    _bridge.set(f'{_node_id}_ActivePorts', ['Flow'], _node.name)
    return math.tanh(float(val))
