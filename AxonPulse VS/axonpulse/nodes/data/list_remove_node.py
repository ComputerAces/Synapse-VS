from axonpulse.core.super_node import SuperNode

from axonpulse.nodes.registry import NodeRegistry

from axonpulse.core.types import DataType

from typing import Any, List, Dict, Optional

from axonpulse.core.types import DataType, TypeCaster

from axonpulse.nodes.decorators import axon_node

@axon_node(category="Data", version="2.3.0", node_label="List Remove")
def ListRemoveNode(List: list, Index: float, _bridge: Any = None, _node: Any = None, _node_id: str = None, **kwargs) -> Any:
    """Removes an item from a list at the specified index.
Returns a new list containing the remaining elements.

Inputs:
- Flow: Trigger the removal.
- List: The source list to modify.
- Index: The zero-based position of the item to remove.

Outputs:
- Flow: Triggered after the item is removed.
- Result: The modified list."""
    list_in = List if List is not None else kwargs.get('List') or []
    index_in = Index if Index is not None else kwargs.get('Index') or 0
    try:
        new_list = list(list_in) if isinstance(list_in, list) else [list_in]
        idx = int(index_in)
        if 0 <= idx < len(new_list):
            new_list.pop(idx)
        else:
            _node.logger.warning(f'Index {idx} out of bounds.')
    except Exception as e:
        _node.logger.error(f'Error: {e}')
        new_list = list_in
    finally:
        pass
    _bridge.set(f'{_node_id}_ActivePorts', ['Flow'], _node.name)
    return new_list
