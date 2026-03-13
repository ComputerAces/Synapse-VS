from axonpulse.core.super_node import SuperNode

from axonpulse.nodes.registry import NodeRegistry

from axonpulse.core.types import DataType

from datetime import datetime

import sys

from typing import Any, List, Dict, Optional

from axonpulse.core.types import DataType, TypeCaster

from axonpulse.nodes.decorators import axon_node

@axon_node(category="Data", version="2.3.0", node_label="Length", outputs=['Length'])
def LengthNode(Value: Any, Min_Value: float, Max_Value: float, _bridge: Any = None, _node: Any = None, _node_id: str = None, **kwargs) -> Any:
    """Calculates the length of lists/strings or normalizes numeric/date values within a range.

Inputs:
- Flow: Trigger the length/normalization calculation.
- Value: The item to process (List, String, Number, or Date).
- Min Value: The lower bound for normalization (optional).
- Max Value: The upper bound for normalization (optional).

Outputs:
- Flow: Triggered after the value is processed.
- Length: The numeric length or normalized 0.0-1.0 value."""
    val = Value if Value is not None else kwargs.get('Value')
    min_in = Min_Value if Min_Value is not None else kwargs.get('Min Value')
    max_in = Max_Value if Max_Value is not None else kwargs.get('Max Value')
    result = 0.0
    if isinstance(val, (list, str)):
        result = len(val)
    elif isinstance(val, (int, float)):
        try:
            v_float = float(val)
            if min_in is not None and max_in is not None:
                mn = float(min_in)
                mx = float(max_in)
                if mx == mn:
                    result = 0.0
                else:
                    result = (v_float - mn) / (mx - mn)
            elif max_in is not None:
                mx = float(max_in)
                if mx == 0:
                    result = 0.0
                else:
                    result = v_float / mx
            elif isinstance(val, int):
                mx = float(sys.maxsize)
                result = v_float / mx
            else:
                mx = 3.4028235e+38
                result = v_float / mx
        except Exception as e:
            _node.logger.error(f'Error: {e}')
            result = 0.0
        finally:
            pass
    elif isinstance(val, datetime):
        try:
            default_min = datetime(1, 1, 1)
            default_max = datetime(2380, 12, 31)
            mn = min_in if isinstance(min_in, datetime) else default_min
            mx = max_in if isinstance(max_in, datetime) else default_max
            total_span = (mx - mn).total_seconds()
            current_span = (val - mn).total_seconds()
            if total_span > 0:
                result = current_span / total_span
            else:
                result = 0.0
        except Exception as e:
            _node.logger.error(f'Date Error: {e}')
            result = 0.0
        finally:
            pass
    elif val is not None:
        result = 1
    else:
        result = 0
    _bridge.set(f'{_node_id}_ActivePorts', ['Flow'], _node.name)
    return result
