from axonpulse.core.super_node import SuperNode

from axonpulse.nodes.registry import NodeRegistry

from axonpulse.core.types import DataType

from typing import Any, List, Dict, Optional

from axonpulse.core.types import DataType, TypeCaster

from axonpulse.nodes.decorators import axon_node

@axon_node(category="Logic", version="2.3.0", node_label="Receiver", outputs=['Data'])
def ReceiverNode(Tag: str = 'channel_1', _bridge: Any = None, _node: Any = None, _node_id: str = None, **kwargs) -> Any:
    """Listens for data broadcasted across the graph using a specific 'Tag'.

Acts as a wireless receiver for values sent by 'Sender' nodes. When 
triggered, it retrieves the payload associated with the 'Tag' from 
the engine's global memory.

Inputs:
- Flow: Trigger the retrieval.
- Tag: The unique identifier for the communication channel.

Outputs:
- Flow: Triggered after data is retrieved.
- Data: The primary payload (if single value) or the full dictionary."""
    tag = Tag or _node.properties.get('Tag', 'channel_1')
    key = f'__WIRELESS_{tag}__'
    payload = _bridge.get(key)
    if not isinstance(payload, dict):
        payload = {'Data': payload}
    else:
        pass
    if payload:
        for (k, v) in payload.items():
            _bridge.set(f'{_node_id}_{k}', v, _node.name)
    else:
        pass
    _bridge.set(f'{_node_id}_ActivePorts', ['Flow'], _node.name)
    return True
