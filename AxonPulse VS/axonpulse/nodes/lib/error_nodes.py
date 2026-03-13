from axonpulse.core.super_node import SuperNode

from axonpulse.nodes.registry import NodeRegistry

from axonpulse.core.types import DataType

from typing import Any, List, Dict, Optional

from axonpulse.core.types import DataType, TypeCaster

from axonpulse.nodes.decorators import axon_node

@axon_node(category="Flow/Error Handling", version="2.3.0", node_label="Last Error Node", outputs=['Error Object'])
def LastErrorNode(_bridge: Any = None, _node: Any = None, _node_id: str = None, **kwargs) -> Any:
    """Retrieves information about the most recent error caught by the engine.

This node is typically used within a Catch block or immediately after a 
failure to inspect error details such as the message, node ID, and trace.

Inputs:
- Flow: Trigger the retrieval.

Outputs:
- Flow: Pulse triggered after retrieval.
- Error Object: An Error object containing Message, Node ID, and context."""
    from axonpulse.core.data import ErrorObject
    last_err = _bridge.get('_SYSTEM_GLOBAL_LAST_ERROR')
    if not last_err:
        last_err = ErrorObject('System', 'Last Error Node', {}, 'No error recorded.')
    else:
        pass
    _node.logger.info('Error object retrieved.')
    _bridge.set(f'{_node_id}_ActivePorts', ['Flow'], _node.name)
    return last_err


@axon_node(category="Flow/Error Handling", version="2.3.0", node_label="Raise Error", outputs=['Error'])
def RaiseErrorNode(Message: str = 'Manual Error Triggered', _bridge: Any = None, _node: Any = None, _node_id: str = None, **kwargs) -> Any:
    """Artificially triggers an error to halt execution or test Error Handling.

When flow reaches this node, it forces a Python exception with the 
specified message, which will be caught by any active Try/Catch blocks.

Inputs:
- Flow: Trigger the error.
- Message: The custom error message to report.

Outputs:
- Flow: Pulse triggered on success (rarely reached due to error).
- Error: Pulse triggered if the engine supports non-halting errors."""
    msg = Message if Message is not None else kwargs.get('Message') or _node.properties.get('Message', 'Manual Error Triggered')
    _node.logger.error(f'Raising manual exception: {msg}')
    raise Exception(msg)
    return True
