from axonpulse.core.super_node import SuperNode

from axonpulse.nodes.registry import NodeRegistry

from axonpulse.core.types import DataType

from typing import Any, List, Dict, Optional

from axonpulse.core.types import DataType, TypeCaster

from axonpulse.nodes.decorators import axon_node

@axon_node(category="Data/Buffers", version="2.3.0", node_label="Raw Data", outputs=['Buffered Data'])
def RawDataNode(Data: Any = None, _bridge: Any = None, _node: Any = None, _node_id: str = None, **kwargs) -> Any:
    """A stateful buffer that stores any data type when triggered by a flow.
Useful for holding values between execution cycles or across graph branches.

### Inputs:
- Flow (flow): Trigger to update the buffered value from the 'Data' input.
- Data (any): The value to be stored in the buffer.

### Outputs:
- Flow (flow): Continues execution after the buffer is updated.
- Data (any): The currently stored value (persistent across pulses)."""
    '\n        When pulsed, update internal data if a new value is provided, \n        then push the current value to the output.\n        '
    if Data is not None:
        _node.properties['Data'] = Data
    else:
        pass
    current_val = _node.properties.get('Data')
    _bridge.set(f'{_node_id}_ActivePorts', ['Flow'], _node.name)
    return current_val
