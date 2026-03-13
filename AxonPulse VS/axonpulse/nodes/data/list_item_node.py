from axonpulse.core.super_node import SuperNode

from axonpulse.nodes.registry import NodeRegistry

from axonpulse.core.types import DataType

from typing import Any, List, Dict, Optional

from axonpulse.core.types import DataType, TypeCaster

from axonpulse.nodes.decorators import axon_node

@axon_node(category="Data", version="2.3.0", node_label="List Item Node", outputs=['Item', 'Error Flow'])
def ListItemNode(List: list, Index: float = 0, _bridge: Any = None, _node: Any = None, _node_id: str = None, **kwargs) -> Any:
    """Retrieves a single item from a list at the specified index.
Includes safeguards for index-out-of-range errors and invalid inputs.

Inputs:
- Flow: Trigger the item retrieval.
- List: The target list to extract an item from.
- Index: The zero-based position of the item.

Outputs:
- Flow: Triggered if the item is successfully retrieved.
- Item: The extracted data item.
- Error Flow: Triggered if the index is invalid or out of range."""
    target_list = List if List is not None else kwargs.get('List') or []
    index = Index if Index is not None else kwargs.get('Index') or _node.properties.get('Index', 0)
    try:
        index = int(index)
    except (ValueError, TypeError):
        err = f"Index '{index}' is not a valid integer."
        _node.logger.error(err)
        _bridge.set(f'{_node_id}_ActivePorts', ['Error Flow'], _node.name)
        _bridge.set('_SYSTEM_LAST_ERROR_MESSAGE', err, _node.name)
    finally:
        pass
    if not isinstance(target_list, list):
        err = f"Input 'List' is not a list. Got {type(target_list)}."
        _node.logger.error(err)
        _bridge.set(f'{_node_id}_ActivePorts', ['Error Flow'], _node.name)
        _bridge.set('_SYSTEM_LAST_ERROR_MESSAGE', err, _node.name)
    else:
        pass
    if 0 <= index < len(target_list):
        item = target_list[index]
        _bridge.set(f'{_node_id}_ActivePorts', ['Flow'], _node.name)
    else:
        err = f'Index {index} out of range (Length: {len(target_list)}).'
        _node.logger.error(err)
        _bridge.set(f'{_node_id}_ActivePorts', ['Error Flow'], _node.name)
        _bridge.set('_SYSTEM_LAST_ERROR_MESSAGE', err, _node.name)
    return {'Item': None, 'Item': item}
