from axonpulse.core.super_node import SuperNode

from axonpulse.nodes.registry import NodeRegistry

from axonpulse.core.types import DataType

from typing import Any, List, Dict, Optional

from axonpulse.core.types import DataType, TypeCaster

from axonpulse.nodes.decorators import axon_node

@axon_node(category="Math/Advanced", version="2.3.0", node_label="Remap")
def RemapNode(Value: Any, In_Min: Any, In_Max: Any, Out_Min: Any, Out_Max: Any, _bridge: Any = None, _node: Any = None, _node_id: str = None, **kwargs) -> Any:
    """Linearly maps a value from one range [In Min, In Max] to another [Out Min, Out Max].
Commonly used for normalizing sensor data or scaling inputs for UI elements.

Inputs:
- Flow: Trigger the calculation.
- Value: The input value to remap.
- In Min: The lower bound of the input range.
- In Max: The upper bound of the input range.
- Out Min: The lower bound of the output range.
- Out Max: The upper bound of the output range.

Outputs:
- Flow: Pulse triggered after calculation.
- Result: The remapped value."""
    val_in = Value if Value is not None else kwargs.get('Value') or _node.properties.get('Value', 0.0)
    in_min = kwargs.get('In Min') if kwargs.get('In Min') is not None else _node.properties.get('In Min', 0.0)
    in_max = kwargs.get('In Max') if kwargs.get('In Max') is not None else _node.properties.get('In Max', 1.0)
    out_min = kwargs.get('Out Min') if kwargs.get('Out Min') is not None else _node.properties.get('Out Min', 0.0)
    out_max = kwargs.get('Out Max') if kwargs.get('Out Max') is not None else _node.properties.get('Out Max', 1.0)
    try:
        val = float(val_in)
        imin = float(in_min)
        imax = float(in_max)
        omin = float(out_min)
        omax = float(out_max)
        if imax == imin:
            t = 0.0
        else:
            t = (val - imin) / (imax - imin)
        res = omin + (omax - omin) * t
    except Exception as e:
        _node.logger.error(f'Error: {e}')
    finally:
        pass
    _bridge.set(f'{_node_id}_ActivePorts', ['Flow'], _node.name)
    return 0.0
