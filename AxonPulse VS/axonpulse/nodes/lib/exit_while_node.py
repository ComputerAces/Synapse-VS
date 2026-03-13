from axonpulse.core.super_node import SuperNode

from axonpulse.nodes.registry import NodeRegistry

from axonpulse.core.types import DataType

from typing import Any, List, Dict, Optional

from axonpulse.core.types import DataType, TypeCaster

from axonpulse.nodes.decorators import axon_node

@axon_node(category="Flow", version="2.3.0", node_label="Exit While")
def ExitWhileNode(_bridge: Any = None, _node: Any = None, _node_id: str = None, **kwargs) -> Any:
    """Terminates an active While loop early.

Acts as a 'break' statement. When triggered, it signals the 'While Loop' 
node to stop iterating and transition to its completion 'Flow' output.

Inputs:
- Flow: Trigger the break signal.

Outputs:
- Flow: Pulse triggered after the signal is sent."""
    _node.logger.info('EXIT WHILE triggered')
    _bridge.set(f'{_node_id}_ActivePorts', ['Flow'], _node.name)
    return True
