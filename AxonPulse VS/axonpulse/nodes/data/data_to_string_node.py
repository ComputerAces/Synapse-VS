from axonpulse.core.super_node import SuperNode

from axonpulse.nodes.registry import NodeRegistry

from axonpulse.core.types import DataType

import json

from typing import Any, List, Dict, Optional

from axonpulse.core.types import DataType, TypeCaster

from axonpulse.nodes.decorators import axon_node

@axon_node(category="Data", version="2.3.0", node_label="Data To String", outputs=['Error Flow', 'String'])
def DataToStringNode(Data: Any, Indent: bool = True, _bridge: Any = None, _node: Any = None, _node_id: str = None, **kwargs) -> Any:
    """Converts a structured Data object (Dictionary or List) into a JSON-formatted string.

Inputs:
- Flow: Trigger the conversion.
- Data: The object (Dictionary or List) to serialize.
- Indent: If True, uses 2-space indentation for readability.

Outputs:
- Flow: Triggered if serialization is successful.
- Error Flow: Triggered if the item cannot be serialized.
- String: The resulting JSON string."""
    val = Data if Data is not None else kwargs.get('Data')
    indent_val = Indent if Indent is not None else kwargs.get('Indent') if kwargs.get('Indent') is not None else _node.properties.get('Indent', True)
    try:
        if isinstance(val, list):
            str_list = [json.dumps(x, indent=2 if indent_val else None, ensure_ascii=False) if isinstance(x, (dict, list)) else str(x) for x in val]
            result = '\n'.join(str_list)
        else:
            result = json.dumps(val, indent=2 if indent_val else None, ensure_ascii=False)
        _bridge.set(f'{_node_id}_ActivePorts', ['Flow'], _node.name)
    except Exception as e:
        _node.logger.error(f'Data To String Error: {e}')
        _bridge.set(f'{_node_id}_ActivePorts', ['Error Flow'], _node.name)
    finally:
        pass
    return {'String': result}
