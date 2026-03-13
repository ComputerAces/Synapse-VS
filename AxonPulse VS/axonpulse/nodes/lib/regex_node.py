import re

from axonpulse.core.super_node import SuperNode

from axonpulse.nodes.registry import NodeRegistry

from axonpulse.core.types import DataType

from typing import Any, List, Dict, Optional

from axonpulse.core.types import DataType, TypeCaster

from axonpulse.nodes.decorators import axon_node

@axon_node(category="Data/Strings", version="2.3.0", node_label="Regex", outputs=['Found', 'Matches'])
def RegexNode(Text: str = '', Pattern: str = '', _bridge: Any = None, _node: Any = None, _node_id: str = None, **kwargs) -> Any:
    """Checks if a string matches a regular expression pattern.

Inputs:
- Flow: Execution trigger.
- Text: The string to search.
- Pattern: The regular expression pattern.

Outputs:
- Flow: Triggered after search.
- Found: True if a match was found.
- Matches: List of all matches found."""
    text = Text if Text is not None else kwargs.get('Text') or _node.properties.get('Text', '')
    pattern = Pattern if Pattern is not None else kwargs.get('Pattern') or _node.properties.get('Pattern', '')
    matches = []
    found = False
    try:
        if pattern and text:
            matches = re.findall(pattern, str(text))
            found = len(matches) > 0
        else:
            pass
    except Exception as e:
        _node.logger.error(f'Regex Error: {e}')
    finally:
        pass
    _bridge.set(f'{_node_id}_ActivePorts', ['Flow'], _node.name)
    return {'Found': found, 'Matches': matches}
