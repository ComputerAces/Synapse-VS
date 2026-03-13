from axonpulse.core.super_node import SuperNode

from axonpulse.nodes.registry import NodeRegistry

from axonpulse.core.types import DataType

from typing import Any, List, Dict, Optional

from axonpulse.core.types import DataType, TypeCaster

from axonpulse.nodes.decorators import axon_node

@axon_node(category="Data", version="2.3.0", node_label="String Replace")
def StringReplaceNode(Source: str = '', Find: str = '', Replace: str = '', Start_Position: float = 0, All: bool = True, _bridge: Any = None, _node: Any = None, _node_id: str = None, **kwargs) -> Any:
    """Replaces occurrences of a substring within a source string. 
Supports replacing the first occurrence or all occurrences, with an optional start position.

Inputs:
- Flow: Trigger the replacement.
- Source: The text string to modify.
- Find: The substring to look for.
- Replace: The replacement substring.
- Start Position: The index to begin searching from.
- All: If True, replaces all occurrences; otherwise, replaces only the first.

Outputs:
- Flow: Triggered after the replacement is complete.
- Result: The modified string."""
    src = Source if Source is not None else kwargs.get('Source') or _node.properties.get('Source', '')
    find_str = Find if Find is not None else kwargs.get('Find') or _node.properties.get('Find', '')
    rep_str = Replace if Replace is not None else kwargs.get('Replace') or _node.properties.get('Replace', '')
    replace_all = All if All is not None else kwargs.get('All') if 'All' in kwargs else _node.properties.get('All', True)
    start_idx = Start_Position if Start_Position is not None else kwargs.get('Start Position') or _node.properties.get('Start Position', 0)
    try:
        start_idx = int(float(start_idx))
    except:
        start_idx = 0
    finally:
        pass
    if src is None:
        src = ''
    else:
        pass
    src = str(src)
    find_str = str(find_str)
    rep_str = str(rep_str)
    if start_idx < 0:
        start_idx = 0
    else:
        pass
    if start_idx >= len(src):
        result = src
    else:
        prefix = src[:start_idx]
        suffix = src[start_idx:]
        if replace_all:
            modified_suffix = suffix.replace(find_str, rep_str)
        else:
            modified_suffix = suffix.replace(find_str, rep_str, 1)
        result = prefix + modified_suffix
    _bridge.set(f'{_node_id}_ActivePorts', ['Flow'], _node.name)
    return result
