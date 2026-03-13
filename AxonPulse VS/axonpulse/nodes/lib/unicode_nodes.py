from axonpulse.core.super_node import SuperNode

from axonpulse.nodes.registry import NodeRegistry

from axonpulse.core.types import DataType

import codecs

import re

from typing import Any, List, Dict, Optional

from axonpulse.core.types import DataType, TypeCaster

from axonpulse.nodes.decorators import axon_node

@axon_node(category="Data/Strings", version="2.3.0", node_label="Unicode To Text", outputs=['Error Flow', 'Result'])
def UnicodeToTextNode(Text: str, _bridge: Any = None, _node: Any = None, _node_id: str = None, **kwargs) -> Any:
    """Converts a string containing literal escaped unicode sequences (e.g. \u00a0) into standard readable text.

Inputs:
- Flow: Execution trigger.
- Text: The string containing escaped unicode sequences.

Outputs:
- Flow: Triggered after conversion.
- Error Flow: Triggered if conversion fails.
- Result: The decoded, human-readable string."""
    val = Text if Text is not None else kwargs.get('Text', '')
    if val is None:
        val = ''
    else:
        pass
    try:
        result = codecs.decode(str(val), 'unicode_escape')
    except Exception as e:
        _node.logger.warning(f'Native unicode decode failed: {e}. Falling back to robust regex matching.')
        try:
            s = str(val)
            s = re.sub('\\\\u([0-9a-fA-F]{4})', lambda m: chr(int(m.group(1), 16)), s)
            s = re.sub('\\\\x([0-9a-fA-F]{2})', lambda m: chr(int(m.group(1), 16)), s)
            s = s.replace('\\n', '\n').replace('\\t', '\t').replace('\\r', '\r')
            result = s
        except Exception as inner_e:
            _node.logger.error(f'Fallback unicode parsing failed: {inner_e}')
            _bridge.set(f'{_node_id}_ActivePorts', ['Error Flow'], _node.name)
        finally:
            pass
    finally:
        pass
    _bridge.set(f'{_node_id}_ActivePorts', ['Flow'], _node.name)
    return {'Result': result}


@axon_node(category="Data/Strings", version="2.3.0", node_label="Text To Unicode", outputs=['Error Flow', 'Result'])
def TextToUnicodeNode(Text: str, _bridge: Any = None, _node: Any = None, _node_id: str = None, **kwargs) -> Any:
    """Converts standard readable text into a string containing literal escaped unicode sequences.

Inputs:
- Flow: Execution trigger.
- Text: The standard human-readable string.

Outputs:
- Flow: Triggered after conversion.
- Error Flow: Triggered if conversion fails.
- Result: The string containing literal unicode escapes."""
    val = Text if Text is not None else kwargs.get('Text', '')
    if val is None:
        val = ''
    else:
        pass
    try:
        result = str(val).encode('unicode_escape').decode('utf-8')
        _bridge.set(f'{_node_id}_ActivePorts', ['Flow'], _node.name)
    except Exception as e:
        _node.logger.error(f'Failed to encode unicode: {e}')
        _bridge.set(f'{_node_id}_ActivePorts', ['Error Flow'], _node.name)
    finally:
        pass
    return {'Result': result}
