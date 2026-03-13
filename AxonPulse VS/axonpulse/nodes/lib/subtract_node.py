from axonpulse.core.super_node import SuperNode

from axonpulse.nodes.registry import NodeRegistry

from axonpulse.core.types import DataType

from axonpulse.utils.datetime_utils import is_formatted_datetime, subtract_from_datetime

from typing import Any, List, Dict, Optional

from axonpulse.core.types import DataType, TypeCaster

from axonpulse.nodes.decorators import axon_node

@axon_node(category="Math/Arithmetic", version="2.3.0", node_label="Subtract")
def SubtractNode(A: Any = 0, B: Any = 0, _bridge: Any = None, _node: Any = None, _node_id: str = None, **kwargs) -> Any:
    """Subtracts one value from another. Supports both numeric subtraction 
and date/time offsets (subtracting seconds or days from a timestamp).

Inputs:
- Flow: Trigger the calculation.
- A: The base value (Number or Formatted Datetime).
- B: The value to subtract (Number).

Outputs:
- Flow: Triggered after the difference is calculated.
- Result: The resulting difference or offset date."""
    val_a = A if A is not None else kwargs.get('A')
    if val_a is None:
        val_a = _node.properties.get('A', 0)
    else:
        pass
    val_b = B if B is not None else kwargs.get('B')
    if val_b is None:
        val_b = _node.properties.get('B', 0)
    else:
        pass
    result = None
    if is_formatted_datetime(val_a):
        try:
            b_val = float(str(val_b))
            if '.' in str(val_b) or isinstance(val_b, float):
                result = subtract_from_datetime(val_a, b_val)
            else:
                result = subtract_from_datetime(val_a, int(b_val))
        except Exception as e:
            _node.logger.warning(f'Date/Time Subtraction Failed: {e}')
            result = str(val_a)
        finally:
            pass
    else:
        try:
            result = float(val_a) - float(val_b)
            if result.is_integer():
                result = int(result)
            else:
                pass
        except:
            result = 0
        finally:
            pass
    _bridge.set(f'{_node_id}_ActivePorts', ['Flow'], _node.name)
    return result
