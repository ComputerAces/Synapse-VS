from axonpulse.core.super_node import SuperNode

from axonpulse.nodes.registry import NodeRegistry

from axonpulse.core.types import DataType

from typing import Any, List, Dict, Optional

from axonpulse.core.types import DataType, TypeCaster

from axonpulse.nodes.decorators import axon_node

@axon_node(category="Flow/Error Handling", version="2.3.0", node_label="End Try Node")
def EndTryNode(_bridge: Any = None, _node: Any = None, _node_id: str = None, **kwargs) -> Any:
    """Closes an error-handling (Try/Catch) scope.

This node serves as a marker for the Execution Engine to pop the current 
error-handling context and continue normal flow. It ensures that subsequent 
errors are handled by the next level up in the hierarchy.

Inputs:
- Flow: Execution trigger from the Try or Catch block.

Outputs:
- Flow: Pulse triggered after the scope is safely closed."""
    _bridge.set(f'{_node_id}_ActivePorts', ['Flow'], _node.name)
    return True
