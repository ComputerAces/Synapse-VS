from axonpulse.core.super_node import SuperNode

from axonpulse.nodes.registry import NodeRegistry

from axonpulse.core.types import DataType

from typing import Any, List, Dict, Optional

from axonpulse.core.types import DataType, TypeCaster

from axonpulse.nodes.decorators import axon_node

@axon_node(category="Data", version="2.3.0", node_label="Number")
def NumberNode(Value: float = 0, _bridge: Any = None, _node: Any = None, _node_id: str = None, **kwargs) -> Any:
    """Manages a numerical value. Supports automatic conversion from strings and dynamic updates.

Inputs:
- Flow: Trigger the number retrieval/update.
- Value: Optional numerical value to set.

Outputs:
- Flow: Triggered after the value is processed.
- Result: The current numerical value."""
    is_val_provided = Value is not None or 'Value' in kwargs
    raw_val = Value if Value is not None else kwargs.get('Value') or _node.properties.get('Value', 0)
    try:
        val = float(raw_val)
        if val.is_integer():
            val = int(val)
        else:
            pass
    except (ValueError, TypeError):
        val = 0
    finally:
        pass
    if is_val_provided:
        _node.properties['Value'] = val
    else:
        pass
    _bridge.set(f'{_node_id}_ActivePorts', ['Flow'], _node.name)
    return val
