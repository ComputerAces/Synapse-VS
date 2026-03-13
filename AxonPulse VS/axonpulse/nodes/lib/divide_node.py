from axonpulse.core.super_node import SuperNode

from axonpulse.nodes.registry import NodeRegistry

from axonpulse.core.types import DataType

from typing import Any, List, Dict, Optional

from axonpulse.core.types import DataType, TypeCaster

from axonpulse.nodes.decorators import axon_node

@axon_node(category="Math/Arithmetic", version="2.3.0", node_label="Divide", outputs=['Error Flow', 'Result'])
def DivideNode(A: float = 1, B: float = 1, Handle_Div_0: bool = False, _bridge: Any = None, _node: Any = None, _node_id: str = None, **kwargs) -> Any:
    """Divides two numbers and provides the quotient.

Inputs:
- Flow: Execution trigger.
- A: The dividend.
- B: The divisor.
- Handle Div 0: If true, returns 0 instead of triggering Error Flow on division by zero.

Outputs:
- Flow: Triggered on successful division.
- Error Flow: Triggered if division by zero occurs and not handled.
- Result: The quotient."""
    val_a = A if A is not None else kwargs.get('A')
    if val_a is None:
        val_a = _node.properties.get('A', 1)
    else:
        pass
    val_b = B if B is not None else kwargs.get('B')
    if val_b is None:
        val_b = _node.properties.get('B', 1)
    else:
        pass
    handle_zero = kwargs.get('Handle Div 0') if kwargs.get('Handle Div 0') is not None else _node.properties.get('Handle Div 0', False)
    try:
        divisor = float(val_b)
        if divisor == 0:
            if handle_zero:
                _bridge.set(f'{_node_id}_ActivePorts', ['Flow'], _node.name)
            else:
                _node.logger.error('Division by zero.')
                _bridge.set(f'{_node_id}_ActivePorts', ['Error Flow'], _node.name)
        else:
            pass
        result = float(val_a) / divisor
        if result.is_integer():
            result = int(result)
        else:
            pass
        _bridge.set(f'{_node_id}_ActivePorts', ['Flow'], _node.name)
    except Exception as e:
        _node.logger.error(f'Divide Error: {e}')
        _bridge.set(f'{_node_id}_ActivePorts', ['Error Flow'], _node.name)
    finally:
        pass
    return {'Result': 0, 'Result': result}
