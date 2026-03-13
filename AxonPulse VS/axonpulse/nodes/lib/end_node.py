from axonpulse.core.super_node import SuperNode

from axonpulse.nodes.registry import NodeRegistry

from axonpulse.core.types import DataType

from typing import Any, List, Dict, Optional

from axonpulse.core.types import DataType, TypeCaster

from axonpulse.nodes.decorators import axon_node

@axon_node(category="Logic/Control Flow", version="2.3.0", node_label="End Node")
def EndNode(_bridge: Any = None, _node: Any = None, _node_id: str = None, **kwargs) -> Any:
    """Terminates the execution of the current branch.

When flow reaches this node, the execution engine stops processing further nodes 
in this specific sequence. It is used to mark the logical conclusion of a 
workflow where no further output pulse is desired.

Inputs:
- Flow: Execution trigger.

Outputs:
- None: This node is a terminator and has no outputs."""
    _bridge.set(f'{_node_id}_ActivePorts', [], _node.name)
    return True
