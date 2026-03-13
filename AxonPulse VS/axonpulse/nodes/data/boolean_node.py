from axonpulse.core.super_node import SuperNode

from axonpulse.nodes.registry import NodeRegistry

from axonpulse.core.types import DataType

from typing import Any, List, Dict, Optional

from axonpulse.core.types import DataType, TypeCaster

from axonpulse.nodes.decorators import axon_node

@axon_node(category="Data", version="2.3.0", node_label="Boolean")
def BooleanNode(Value: bool = 'False', _bridge: Any = None, _node: Any = None, _node_id: str = None, **kwargs) -> Any:
    """Standard data node for boolean values (True/False).
Allows manual entry or dynamic conversion of various inputs to boolean.

Inputs:
- Flow: Trigger execution to update the output result.
- Value: The value to be converted/set (supports strings like 'True', '1', 'Yes').

Outputs:
- Flow: Triggered after processing.
- Result: The resulting boolean value (True or False)."""
    is_val_provided = Value is not None or 'Value' in kwargs
    raw = Value if Value is not None else kwargs.get('Value') or _node.properties.get('Value', 'False')
    is_true = str(raw).lower() in ('true', '1', 'yes')
    val = 1 if is_true else 0
    if is_val_provided:
        _node.properties['Value'] = 'True' if is_true else 'False'
    else:
        pass
    _bridge.set(f'{_node_id}_ActivePorts', ['Flow'], _node.name)
    return val
