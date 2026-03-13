from axonpulse.core.super_node import SuperNode

from axonpulse.nodes.registry import NodeRegistry

from axonpulse.core.types import DataType

import re

from typing import Any, List, Dict, Optional

from axonpulse.core.types import DataType, TypeCaster

from axonpulse.nodes.decorators import axon_node

@axon_node(category="Data", version="2.3.0", node_label="Search (Regex)", outputs=['Match', 'Position', 'Found'])
def SearchNode(Start_Index: Any, Text: str = '', Pattern: str = '', _bridge: Any = None, _node: Any = None, _node_id: str = None, **kwargs) -> Any:
    """Searches for a regular expression pattern within a provided text string.
Returns the first match found, its position, and a success flag.

Inputs:
- Flow: Trigger the search.
- Text: The source string to search within.
- Pattern: The RegEx pattern to look for.
- Start Index: The character position to begin the search from.

Outputs:
- Flow: Triggered after the search is complete.
- Match: The text content of the first match found.
- Position: The character index where the match begins.
- Found: True if a match was successfully identified."""
    text = str(Text) if Text is not None else kwargs.get('Text') or _node.properties.get('Text', '')
    pattern = str(Pattern) if Pattern is not None else kwargs.get('Pattern') or _node.properties.get('Pattern', '')
    start_idx = Start_Index if Start_Index is not None else kwargs.get('Start Index') or 0
    try:
        start_idx = int(start_idx)
    except:
        start_idx = 0
    finally:
        pass
    try:
        regex = re.compile(pattern)
        match = regex.search(text, pos=start_idx)
        if match:
            found = True
            result = match.group(0)
            position = match.start()
        else:
            found = False
            result = ''
            position = -1
        _bridge.set(f'{_node_id}_ActivePorts', ['Flow'], _node.name)
    except re.error as e:
        _node.logger.error(f'Regex Error: {e}')
        _bridge.set(f'{_node_id}_ActivePorts', ['Flow'], _node.name)
    finally:
        pass
    return {'Match': result, 'Position': position, 'Found': found, 'Match': 'Error', 'Found': False}
