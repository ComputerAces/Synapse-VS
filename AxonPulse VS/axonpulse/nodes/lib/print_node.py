from axonpulse.core.super_node import SuperNode

from axonpulse.nodes.registry import NodeRegistry

from axonpulse.core.types import DataType

from typing import Any, List, Dict, Optional

from axonpulse.core.types import DataType, TypeCaster

from axonpulse.nodes.decorators import axon_node

@axon_node(category="System/Terminal", version="2.3.0", node_label="Print")
def PrintNode(Message: str, _bridge: Any = None, _node: Any = None, _node_id: str = None, **kwargs) -> Any:
    """Outputs a message to the system terminal or console.
Useful for debugging and tracking graph execution flow.

Inputs:
- Flow: Trigger the print operation.
- Message: The string message to display.

Outputs:
- Flow: Pulse triggered after the message is printed."""
    message = Message if Message is not None else kwargs.get('Message') or 'Hello AxonPulse!'
    print(f'[{_node.name}] OUTPUT: {message}')
    _bridge.set(f'last_msg_{_node.name}', message, _node.name)
    _bridge.set(f'{_node_id}_ActivePorts', ['Flow'], _node.name)
    return True
