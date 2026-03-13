from axonpulse.core.super_node import SuperNode

from axonpulse.nodes.registry import NodeRegistry

from axonpulse.core.types import DataType

from typing import Any, List, Dict, Optional

from axonpulse.core.types import DataType, TypeCaster

from axonpulse.nodes.decorators import axon_node

@axon_node(category="Math/Advanced", version="2.3.0", node_label="Lerp")
def LerpNode(A: Any = 0.0, B: Any = 1.0, T: Any = 0.5, _bridge: Any = None, _node: Any = None, _node_id: str = None, **kwargs) -> Any:
    """Performs Linear Interpolation (Lerp) between two values based on a weight factor.

Formula: Result = A + (B - A) * T. 
If T is 0.0, the result is A. If T is 1.0, the result is B.

Inputs:
- Flow: Trigger the calculation.
- A: The start value (0%).
- B: The end value (100%).
- T: The interpolation factor (typically 0.0 to 1.0).

Outputs:
- Flow: Triggered after calculation.
- Result: The interpolated value."""
    a = A if A is not None else kwargs.get('A') or _node.properties.get('A', 0.0)
    b = B if B is not None else kwargs.get('B') or _node.properties.get('B', 1.0)
    t = T if T is not None else kwargs.get('T') or _node.properties.get('T', 0.5)
    try:
        res = a + (b - a) * t
    except Exception as e:
        _node.logger.error(f'Lerp Error: {e}')
    finally:
        pass
    _bridge.set(f'{_node_id}_ActivePorts', ['Flow'], _node.name)
    return 0.0


@axon_node(category="Math/Advanced", version="2.3.0", node_label="Inverse Lerp", outputs=['T'])
def InverseLerpNode(A: Any = 0.0, B: Any = 1.0, Value: Any = 0.5, _bridge: Any = None, _node: Any = None, _node_id: str = None, **kwargs) -> Any:
    """Calculates the normalized interpolant (T) for a value within a specific range [A, B].

This is the inverse of the Lerp operation. It determines where 'Value' sits 
relative to A and B.

Inputs:
- Flow: Trigger the calculation.
- A: The lower bound (maps to 0.0).
- B: The upper bound (maps to 1.0).
- Value: The number to normalize.

Outputs:
- Flow: Triggered after calculation.
- T: The normalized position (0.0 to 1.0)."""
    a = A if A is not None else kwargs.get('A') or _node.properties.get('A', 0.0)
    b = B if B is not None else kwargs.get('B') or _node.properties.get('B', 1.0)
    val = Value if Value is not None else kwargs.get('Value') or _node.properties.get('Value', 0.5)
    if b == a:
        t = 0.0
    else:
        t = (val - a) / (b - a)
    _bridge.set(f'{_node_id}_ActivePorts', ['Flow'], _node.name)
    return t


@axon_node(category="Math/Advanced", version="2.3.0", node_label="Remap")
def RemapNode(In_Min: Any, In_Max: Any, Out_Min: Any, Out_Max: Any, Value: Any = 0.0, _bridge: Any = None, _node: Any = None, _node_id: str = None, **kwargs) -> Any:
    """Maps a value from an input range [InMin, InMax] to an output range [OutMin, OutMax].

This node first normalizes the input value and then applies it to the output target range.

Inputs:
- Flow: Trigger the operation.
- Value: The number to remap.
- In Min: The start of the input range.
- In Max: The end of the input range.
- Out Min: The start of the output range.
- Out Max: The end of the output range.

Outputs:
- Flow: Triggered after transformation.
- Result: The value mapped to the new range."""
    val = Value if Value is not None else kwargs.get('Value') or _node.properties.get('Value', 0.0)
    in_min = In_Min if In_Min is not None else kwargs.get('In Min') or _node.properties.get('InMin', 0.0)
    in_max = In_Max if In_Max is not None else kwargs.get('In Max') or _node.properties.get('InMax', 1.0)
    out_min = Out_Min if Out_Min is not None else kwargs.get('Out Min') or _node.properties.get('OutMin', 0.0)
    out_max = Out_Max if Out_Max is not None else kwargs.get('Out Max') or _node.properties.get('OutMax', 100.0)
    if in_max == in_min:
        t = 0.0
    else:
        t = (val - in_min) / (in_max - in_min)
    result = out_min + (out_max - out_min) * t
    _bridge.set(f'{_node_id}_ActivePorts', ['Flow'], _node.name)
    return result
