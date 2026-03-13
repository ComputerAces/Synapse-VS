from axonpulse.core.super_node import SuperNode

from axonpulse.nodes.registry import NodeRegistry

from axonpulse.core.types import DataType

from typing import Any, List, Dict, Optional

from axonpulse.core.types import DataType, TypeCaster

from axonpulse.nodes.decorators import axon_node

@axon_node(category="Logic", version="2.3.0", node_label="Sender")
def SenderNode(Data: Any, Tag: str = 'channel_1', _bridge: Any = None, _node: Any = None, _node_id: str = None, **kwargs) -> Any:
    """Broadcasts data across the graph using a specific 'Tag'.

Acts as a wireless transmitter. Data sent to this node can be 
retrieved by 'Receiver' nodes using the same 'Tag'. Supports 
dynamic inputs which are bundled into the broadcast payload.

Inputs:
- Flow: Trigger the broadcast.
- Tag: The unique identifier for the communication channel.
- Data: The primary payload to send.

Outputs:
- None (Ends execution branch or sinks pulse)."""
    tag = Tag or _node.properties.get('Tag', 'channel_1')
    payload = {}
    if Data is not None:
        payload['Data'] = Data
    else:
        pass
    payload.update(kwargs)
    payload.pop('Flow', None)
    key = f'__WIRELESS_{tag}__'
    _bridge.set(key, payload, _node.name)
    print(f"[{_node.name}] Broadcasting on '{tag}': {payload}")
    return True
