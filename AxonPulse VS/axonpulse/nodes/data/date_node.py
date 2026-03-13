from axonpulse.core.super_node import SuperNode

from axonpulse.nodes.registry import NodeRegistry

from axonpulse.core.types import DataType

from datetime import datetime

from typing import Any, List, Dict, Optional

from axonpulse.core.types import DataType, TypeCaster

from axonpulse.nodes.decorators import axon_node

@axon_node(category="Data", version="2.3.0", node_label="Date")
def DateNode(Value: str = datetime.now().strftime('%Y-%m-%d'), _bridge: Any = None, _node: Any = None, _node_id: str = None, **kwargs) -> Any:
    """Manages a date string value. Defaults to the current system date if not specified.

Inputs:
- Flow: Trigger the date retrieval/update.
- Value: Optional date string (YYYY-MM-DD) to set.

Outputs:
- Flow: Triggered after the date is processed.
- Result: The current date string."""
    val_input = Value if Value is not None else kwargs.get('Value')
    if val_input is not None:
        _node.properties['Value'] = str(val_input)
    else:
        pass
    val = _node.properties.get('Value')
    if not val:
        val = datetime.now().strftime('%Y-%m-%d')
    else:
        pass
    _bridge.set(f'{_node_id}_ActivePorts', ['Flow'], _node.name)
    return val
