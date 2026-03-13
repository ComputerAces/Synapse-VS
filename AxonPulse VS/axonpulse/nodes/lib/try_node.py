from axonpulse.core.super_node import SuperNode

from axonpulse.nodes.registry import NodeRegistry

from axonpulse.core.types import DataType

from typing import Any, List, Dict, Optional

from axonpulse.core.types import DataType, TypeCaster

from axonpulse.nodes.decorators import axon_node

@axon_node(category="Logic/Control Flow", version="2.3.0", node_label="Try Node", outputs=['Catch', 'FailedNode', 'ErrorCode'])
def TryNode(_bridge: Any = None, _node: Any = None, _node_id: str = None, **kwargs) -> Any:
    """Initiates a protected execution block (Exception Handler).

Wraps downstream flow in a try-catch pattern. If any node in the 
'Flow' branch encounters an error, the engine will intercept it 
and pulse the 'Catch' port of this node.

Inputs:
- Flow: Trigger the protected branch.

Outputs:
- Flow: The primary pulse to protect.
- Catch: Pulse triggered only on execution failure.
- FailedNode: Name or ID of the node that threw the error.
- ErrorCode: Error message or status code."""
    _bridge.set(f'{_node_id}_ActivePorts', ['Flow'], _node.name)
    return {'FailedNode': '', 'ErrorCode': 0}
