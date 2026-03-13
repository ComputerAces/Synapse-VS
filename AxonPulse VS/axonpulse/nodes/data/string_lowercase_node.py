from axonpulse.core.super_node import SuperNode

from axonpulse.nodes.registry import NodeRegistry

from axonpulse.core.types import DataType

from typing import Any, List, Dict, Optional

from axonpulse.core.types import DataType, TypeCaster

from axonpulse.nodes.decorators import axon_node

@axon_node(category="Data", version="2.3.0", node_label="String Lowercase")
def StringLowercaseNode(Value: str = '', _bridge: Any = None, _node: Any = None, _node_id: str = None, **kwargs) -> Any:
    """Converts all characters in a text string to lowercase.

Inputs:
- Flow: Trigger the conversion.
- Value: The source text string.

Outputs:
- Flow: Triggered after conversion.
- Result: The lowercase version of the string."""
    val = Value if Value is not None else kwargs.get('Value') or _node.properties.get('Value', '')
    if val is None:
        val = ''
    else:
        pass
    result = str(val).lower()
    _bridge.set(f'{_node_id}_ActivePorts', ['Flow'], _node.name)
    return result
