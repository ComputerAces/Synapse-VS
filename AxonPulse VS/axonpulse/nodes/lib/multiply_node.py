from axonpulse.core.super_node import SuperNode

from axonpulse.nodes.registry import NodeRegistry

from axonpulse.core.types import DataType

from typing import Any, List, Dict, Optional

from axonpulse.core.types import DataType, TypeCaster

from axonpulse.nodes.decorators import axon_node

@axon_node(category="Math/Arithmetic", version="2.3.0", node_label="Multiply")
def MultiplyNode(A: float = 1, B: float = 1, _bridge: Any = None, _node: Any = None, _node_id: str = None, **kwargs) -> Any:
    """Performs multiplication of two numeric values.
Automatically handles integer and float conversion for the result.

Inputs:
- Flow: Trigger the multiplication.
- A: The first factor.
- B: The second factor.

Outputs:
- Flow: Triggered after the product is calculated.
- Result: The product of A and B."""
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
    try:
        result = float(val_a) * float(val_b)
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
