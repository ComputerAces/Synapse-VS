from axonpulse.core.super_node import SuperNode

from axonpulse.nodes.registry import NodeRegistry

from axonpulse.core.types import DataType

import re

from typing import Any, List, Dict, Optional

from axonpulse.core.types import DataType, TypeCaster

from axonpulse.nodes.decorators import axon_node

@axon_node(category="Data", version="2.3.0", node_label="List Node", outputs=['List', 'Length'])
def ListNode(_bridge: Any = None, _node: Any = None, _node_id: str = None, **kwargs) -> Any:
    """Creates a new list from multiple dynamic inputs.
Each input port designated as 'Item X' is collected into the resulting list.

Inputs:
- Flow: Trigger the list creation.
- [Dynamic]: Various 'Item' inputs to include in the list.

Outputs:
- Flow: Triggered after the list is created.
- List: The resulting Python list.
- Length: The number of items in the list."""
    items = []
    additional = _node.properties.get('Additional Inputs', [])
    item_pattern = re.compile('^Item (\\d+)$', re.IGNORECASE)
    for port_name in additional:
        match = item_pattern.match(port_name)
        if not match:
            continue
        else:
            pass
        val = kwargs.get(port_name)
        if val is None:
            val = _node.properties.get(port_name)
            if val is None:
                search_key = port_name.lower()
                for (k, v) in _node.properties.items():
                    if k.lower() == search_key:
                        val = v
                        break
                    else:
                        pass
            else:
                pass
        else:
            pass
        if val is not None:
            items.append(val)
        else:
            pass
    length = len(items)
    _bridge.set(f'{_node_id}_ActivePorts', ['Flow'], _node.name)
    return {'List': items, 'Length': length}
