from axonpulse.core.super_node import SuperNode

from axonpulse.nodes.registry import NodeRegistry

from axonpulse.core.types import DataType

from enum import Enum

from typing import Any, List, Dict, Optional

from axonpulse.core.types import DataType, TypeCaster

from axonpulse.nodes.decorators import axon_node

@axon_node(category="Enums", version="2.3.0", node_label="Random Type")
def RandomTypeEnumNode(Value: float = 'Number', _bridge: Any = None, _node: Any = None, _node_id: str = None) -> Any:
    """Standardizes the selection of random generation algorithms.

Provides a consistent label for common random types like 'Number' (float), 
'Integer', or 'Unique ID' (UUID). This node is typically linked to a 
'Random' node to define its behavior.

Inputs:
- Value: The random type selection (Number, Integer, UID).

Outputs:
- Result: The selected type string."""
    val = _node.properties.get('Value', 'Number')
    return val
