from axonpulse.core.super_node import SuperNode

from axonpulse.nodes.registry import NodeRegistry

from axonpulse.core.types import DataType

from typing import Any, List, Dict, Optional

from axonpulse.core.types import DataType, TypeCaster

from axonpulse.nodes.decorators import axon_node

@axon_node(category="Data", version="2.3.0", node_label="String")
def StringNode(Value: str = '', _bridge: Any = None, _node: Any = None, _node_id: str = None, **kwargs) -> Any:
    """Manages a text string value. Supports dynamic updates via the Flow input.

Inputs:
- Flow: Trigger the string retrieval/update.
- Value: Optional text string to set.

Outputs:
- Flow: Triggered after the string is processed.
- Result: The current text string."""
    val_input = Value if Value is not None else kwargs.get('Value')
    if val_input is not None:
        _node.properties['Value'] = str(val_input)
    else:
        pass
    val = _node.properties.get('Value', '')
    _bridge.set(f'{_node_id}_ActivePorts', ['Flow'], _node.name)
    return val
