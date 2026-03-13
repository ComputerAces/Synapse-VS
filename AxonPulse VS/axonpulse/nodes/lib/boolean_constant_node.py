from axonpulse.core.super_node import SuperNode

from axonpulse.nodes.registry import NodeRegistry

from axonpulse.core.types import DataType

from typing import Any, List, Dict, Optional

from axonpulse.core.types import DataType, TypeCaster

from axonpulse.nodes.decorators import axon_node

@axon_node(category="Logic", version="2.3.0", node_label="Boolean Type")
def BooleanTypeNode(Value: bool = 'True', _bridge: Any = None, _node: Any = None, _node_id: str = None, **kwargs) -> Any:
    """A constant boolean node that outputs a fixed True or False value.
Useful for setting toggles or flags within a graph.

Inputs:
- Flow: Triggered upon execution.
- Value: The constant boolean value to output.

Outputs:
- Flow: Triggered upon execution.
- Result: The constant boolean value."""
    prop_val = _node.properties.get('Value', 'True')
    val = str(prop_val).lower() == 'true'
    _bridge.set(f'{_node_id}_ActivePorts', ['Flow'], _node.name)
    return val
