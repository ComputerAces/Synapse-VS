from axonpulse.core.super_node import SuperNode

from axonpulse.nodes.registry import NodeRegistry

from axonpulse.core.types import DataType

from typing import Any, List, Dict, Optional

from axonpulse.core.types import DataType, TypeCaster

from axonpulse.nodes.decorators import axon_node

@axon_node(category="Data", version="2.3.0", node_label="Split Text", outputs=['List'])
def SplitTextNode(Text: str = '', Delimiter: str = ' ', _bridge: Any = None, _node: Any = None, _node_id: str = None, **kwargs) -> Any:
    """Divides a text string into a list of substrings based on a specified delimiter.

Inputs:
- Flow: Trigger the split operation.
- Text: The source string to be divided.
- Delimiter: The character or substring used to split the text.

Outputs:
- Flow: Triggered after the text is split.
- List: The resulting list of substrings."""
    text_val = Text if Text is not None else kwargs.get('Text') or _node.properties.get('Text', '')
    delim_val = Delimiter if Delimiter is not None else kwargs.get('Delimiter') or _node.properties.get('Delimiter', ' ')
    text_str = str(text_val)
    delim_str = str(delim_val)
    if not delim_str:
        result = list(text_str)
    else:
        result = text_str.split(delim_str)
    print(f"[{_node.name}] Split Text: '{text_str}' by '{delim_str}' -> {result}")
    _bridge.set(f'{_node_id}_ActivePorts', ['Flow'], _node.name)
    return result
