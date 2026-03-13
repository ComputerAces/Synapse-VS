from axonpulse.core.super_node import SuperNode

from axonpulse.nodes.registry import NodeRegistry

from axonpulse.core.types import DataType

from typing import Any, List, Dict, Optional

from axonpulse.core.types import DataType, TypeCaster

from axonpulse.nodes.decorators import axon_node

@axon_node(category="Data", version="2.3.0", node_label="Data Type", outputs=['String Flow', 'Number Flow', 'Boolean Flow', 'List Flow', 'Dict Flow', 'None Flow', 'Unknown Flow'])
def DataTypeNode(Data: Any, _bridge: Any = None, _node: Any = None, _node_id: str = None, **kwargs) -> Any:
    """Checks the underlying type of the provided Data and routes execution
flow accordingly.

Inputs:
- Flow: Trigger type check.
- Data: Any data to check.

Outputs:
- String Flow: Triggered if Data is a string.
- Number Flow: Triggered if Data is an integer or float.
- Boolean Flow: Triggered if Data is True or False.
- List Flow: Triggered if Data is a List, Tuple, or Set.
- Dict Flow: Triggered if Data is a Dictionary / JSON object.
- None Flow: Triggered if Data is None or Empty.
- Unknown Flow: Triggered if the type is unrecognized (e.g., custom object or binary)."""
    data_obj = Data if Data is not None else _node.properties.get('Data')
    active_port = 'Unknown Flow'
    if data_obj is None:
        active_port = 'None Flow'
    elif isinstance(data_obj, str):
        active_port = 'String Flow'
    elif isinstance(data_obj, bool):
        active_port = 'Boolean Flow'
    elif isinstance(data_obj, (int, float)):
        active_port = 'Number Flow'
    elif isinstance(data_obj, (list, tuple, set)):
        active_port = 'List Flow'
    elif isinstance(data_obj, dict):
        active_port = 'Dict Flow'
    else:
        pass
    _bridge.set(f'{_node_id}_ActivePorts', [active_port], _node.name)
    return True
