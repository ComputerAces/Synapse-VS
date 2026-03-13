from axonpulse.core.super_node import SuperNode

from axonpulse.nodes.registry import NodeRegistry

from axonpulse.core.types import DataType

from typing import Any, List, Dict, Optional

from axonpulse.core.types import DataType, TypeCaster

from axonpulse.nodes.decorators import axon_node

@axon_node(category="Logic", version="2.3.0", node_label="Run Split", outputs=['Valid', 'Null'])
def RunSplitNode(Value: Any, _bridge: Any = None, _node: Any = None, _node_id: str = None, **kwargs) -> Any:
    """Splits flow based on whether a value is populated or 'Null'.

Checks the 'Value' input. If it is non-empty and valid, the 'Valid' 
port is pulsed. If it is None, empty, or "none", the 'Null' 
port is pulsed.

Inputs:
- Flow: Trigger the check.
- Value: The data to validate.

Outputs:
- Valid: Pulse triggered if value is valid.
- Null: Pulse triggered if value is empty/null."""
    val = Value if Value is not None else _node.properties.get('Value', '')
    is_valid = val is not None and str(val).strip() != '' and (str(val).lower() != 'none')
    result_port = 'Valid' if is_valid else 'Null'
    print(f'[{_node.name}] RunSplit: {val} -> {result_port}')
    _bridge.set(f'{_node_id}_ActivePorts', [result_port], _node.name)
    return True
