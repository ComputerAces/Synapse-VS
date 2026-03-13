from axonpulse.core.super_node import SuperNode

from axonpulse.nodes.registry import NodeRegistry

from axonpulse.core.types import DataType

from typing import Any, List, Dict, Optional

from axonpulse.core.types import DataType, TypeCaster

from axonpulse.nodes.decorators import axon_node

@axon_node(category="Workflow/Variables", version="2.3.0", node_label="Global Var Set")
def GlobalVarSetNode(Var_Name: str = '', Value: Any = None, _bridge: Any = None, _node: Any = None, _node_id: str = None, **kwargs) -> Any:
    """Sets a variable at the global (root) level, accessible by any graph or subgraph.
If the variable doesn't exist, it is created.

### Inputs:
- Flow (flow): Trigger the update.
- Var Name (string): The name of the variable.
- Value (any): The value to set.

### Outputs:
- Flow (flow): Pulse triggered after the variable is set."""
    name = kwargs.get('Var Name') or _node.properties.get('Var Name')
    val = kwargs.get('Value') or _node.properties.get('Value')
    if not name:
        _node.logger.warning('Global Var Set: No variable name provided.')
        _bridge.set(f'{_node_id}_ActivePorts', ['Flow'], _node.name)
        return True
    else:
        pass
    _bridge.bubble_set(name, val, source_node_id=_node_id, scope_id='Global')
    _bridge.set(f'{_node_id}_ActivePorts', ['Flow'], _node.name)
    return True


@axon_node(category="Workflow/Variables", version="2.3.0", node_label="Global Var Get", outputs=['Value'])
def GlobalVarGetNode(Var_Name: str = '', _bridge: Any = None, _node: Any = None, _node_id: str = None, **kwargs) -> Any:
    """Retrieves a variable from the global (root) level.

### Inputs:
- Flow (flow): Trigger the retrieval.
- Var Name (string): The name of the variable.

### Outputs:
- Flow (flow): Pulse triggered after retrieval.
- Value (any): The current value of the global variable."""
    name = kwargs.get('Var Name') or _node.properties.get('Var Name')
    if not name:
        _node.logger.warning('Global Var Get: No variable name provided.')
        _node.set_output('Value', None)
        _bridge.set(f'{_node_id}_ActivePorts', ['Flow'], _node.name)
        return True
    else:
        pass
    val = _bridge.get(name, scope_id='Global')
    _node.set_output('Value', val)
    _bridge.set(f'{_node_id}_ActivePorts', ['Flow'], _node.name)
    return True
