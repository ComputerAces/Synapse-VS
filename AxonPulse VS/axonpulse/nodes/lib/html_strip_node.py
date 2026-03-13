from axonpulse.core.super_node import SuperNode

from axonpulse.nodes.registry import NodeRegistry

from axonpulse.core.types import DataType

from typing import Any, List, Dict, Optional

from axonpulse.core.types import DataType, TypeCaster

from axonpulse.nodes.decorators import axon_node

BeautifulSoup = None

def load_bs4():
    global BeautifulSoup
    if BeautifulSoup:
        return True
    try:
        from bs4 import BeautifulSoup as _B
        BeautifulSoup = _B
        return True
    except ImportError:
        return False

@axon_node(category="Text", version="2.3.0", node_label="HTML Strip Text", outputs=['Text'])
def HTMLStripTextNode(HTML: str, _bridge: Any = None, _node: Any = None, _node_id: str = None, **kwargs) -> Any:
    """Strips raw HTML down to its inner plain text content using BeautifulSoup.

### Inputs:
- Flow (flow): Execution trigger.
- HTML (string): The raw HTML string to process.

### Outputs:
- Flow (flow): Triggered after processing.
- Text (string): The stripped plain text."""
    html_string = kwargs.get('HTML', '')
    if not html_string or not isinstance(html_string, str):
        _node.set_output('Text', '')
        _bridge.bubble_set(f'{_node_id}_ActivePorts', ['Flow'], _node.name)
        return True
    else:
        pass
    if not load_bs4():
        _node.logger.error('BeautifulSoup4 is not installed. Returning original HTML.')
        _node.set_output('Text', html_string)
        _bridge.bubble_set(f'{_node_id}_ActivePorts', ['Flow'], _node.name)
        return True
    else:
        pass
    try:
        soup = BeautifulSoup(html_string, 'html.parser')
        clean_text = soup.get_text(separator=' ', strip=True)
        _node.set_output('Text', clean_text)
    except Exception as e:
        _node.logger.error(f'Failed to strip HTML text: {e}')
        _node.set_output('Text', '')
    finally:
        pass
    _bridge.bubble_set(f'{_node_id}_ActivePorts', ['Flow'], _node.name)
    return True
