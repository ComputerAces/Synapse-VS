from axonpulse.core.super_node import SuperNode

from axonpulse.nodes.registry import NodeRegistry

from axonpulse.core.types import DataType

from typing import Any, List, Dict, Optional

from axonpulse.core.types import DataType, TypeCaster

from axonpulse.nodes.decorators import axon_node

@axon_node(category="Data", version="2.3.0", node_label="Replace")
def ReplaceNode(Target: Any = '', Old: Any = '', New: Any = '', _bridge: Any = None, _node: Any = None, _node_id: str = None, **kwargs) -> Any:
    """Replaces occurrences of a specified value with a new value within a string or list.

Inputs:
- Flow: Trigger the replacement operation.
- Target: The source string or list to modify.
- Old: The value or substring to be replaced.
- New: The replacement value or substring.

Outputs:
- Flow: Triggered after the replacement is complete.
- Result: The modified string or list."""
    target_val = Target if Target is not None else kwargs.get('Target') or _node.properties.get('Target')
    old_val = Old if Old is not None else kwargs.get('Old') or _node.properties.get('Old', '')
    new_val = New if New is not None else kwargs.get('New') or _node.properties.get('New', '')
    result = target_val
    if target_val is None:
        _node.logger.warning('Target is None.')
        _bridge.set(f'{_node_id}_ActivePorts', ['Flow'], _node.name)
    else:
        pass
    if isinstance(target_val, str):
        old_str = str(old_val)
        new_str = str(new_val)
        result = target_val.replace(old_str, new_str)
    elif isinstance(target_val, list):
        result = [new_val if item == old_val else item for item in target_val]
    else:
        _node.logger.warning(f'Unsupported Target type {type(target_val)}.')
    _bridge.set(f'{_node_id}_ActivePorts', ['Flow'], _node.name)
    return result
