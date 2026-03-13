from axonpulse.core.super_node import SuperNode

from axonpulse.nodes.registry import NodeRegistry

from axonpulse.core.types import DataType

import json

from typing import Any, List, Dict, Optional

from axonpulse.core.types import DataType, TypeCaster

from axonpulse.nodes.decorators import axon_node

@axon_node(category="Data", version="2.3.0", node_label="String To Data", outputs=['Error Flow', 'Data'])
def StringToDataNode(String: str = '', _bridge: Any = None, _node: Any = None, _node_id: str = None, **kwargs) -> Any:
    """Parses a JSON-formatted string into a structured Data object (Dictionary or List).

Inputs:
- Flow: Trigger the conversion.
- String: The JSON string to parse.

Outputs:
- Flow: Triggered if parsing is successful.
- Error Flow: Triggered if the string is not valid JSON.
- Data: The resulting Dictionary or List."""
    val = String if String is not None else kwargs.get('String') or _node.properties.get('String', '')
    if not val:
        _bridge.set(f'{_node_id}_ActivePorts', ['Flow'], _node.name)
    else:
        pass
    try:
        result = json.loads(val)
        _bridge.set(f'{_node_id}_ActivePorts', ['Flow'], _node.name)
    except Exception as e:
        _node.logger.error(f'String To Data Error: {e}')
        _bridge.set(f'{_node_id}_ActivePorts', ['Error Flow'], _node.name)
    finally:
        pass
    return {'Data': {}, 'Data': result}
