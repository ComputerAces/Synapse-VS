from axonpulse.core.super_node import SuperNode

from axonpulse.nodes.registry import NodeRegistry

from axonpulse.core.types import DataType

from typing import Any, List, Dict, Optional

from axonpulse.core.types import DataType, TypeCaster

from axonpulse.nodes.decorators import axon_node

@axon_node(category="Workflow", version="2.3.0", node_label="Project Var Get", outputs=['Value'])
def ProjectVarGetNode(Var_Name: str = '', _bridge: Any = None, _node: Any = None, _node_id: str = None, **kwargs) -> Any:
    """Retrieves a global project variable from the bridge.
Project variables persist across different graphs within the same project.

Inputs:
- Flow: Trigger the retrieval.
- Var Name: The name of the project variable to get.

Outputs:
- Flow: Pulse triggered after retrieval.
- Value: The current value of the project variable."""
    var_name = kwargs.get('Var Name') or _node.properties.get('Var Name')
    if not var_name:
        _node.logger.warning('No variable name provided for Project Var Get.')
        _bridge.set(f'{_node_id}_ActivePorts', ['Flow'], _node.name)
    else:
        pass
    full_key = f'ProjectVars.{var_name}'
    value = _bridge.get(full_key)
    _bridge.set(f'{_node_id}_ActivePorts', ['Flow'], _node.name)
    return value


@axon_node(category="Workflow", version="2.3.0", node_label="Project Var Set")
def ProjectVarSetNode(Var_Name: str = '', Value: Any = '', _bridge: Any = None, _node: Any = None, _node_id: str = None, **kwargs) -> Any:
    """Sets a global project variable in the bridge.
Project variables persist across different graphs within the same project.

Inputs:
- Flow: Trigger the update.
- Var Name: The name of the project variable to set.
- Value: The new value to assign to the variable.

Outputs:
- Flow: Pulse triggered after the variable is updated."""
    var_name = kwargs.get('Var Name') or _node.properties.get('Var Name')
    val_to_set = kwargs.get('Value') or _node.properties.get('Value')
    if not var_name:
        _node.logger.warning('No variable name provided for Project Var Set.')
        _bridge.set(f'{_node_id}_ActivePorts', ['Flow'], _node.name)
        return True
    else:
        pass
    full_key = f'ProjectVars.{var_name}'
    _bridge.set(full_key, val_to_set, _node.name)
    _node.logger.info(f"Updated Project Variable '{var_name}' to: {val_to_set}")
    _bridge.set(f'{_node_id}_ActivePorts', ['Flow'], _node.name)
    return True


@axon_node(category="Workflow", version="2.3.0", node_label="Project Metadata Get", outputs=['Name', 'Version', 'Category', 'Description'])
def ProjectMetadataGetNode(_bridge: Any = None, _node: Any = None, _node_id: str = None, **kwargs) -> Any:
    """Retrieves project metadata (Name, Version, Category, Description) from the bridge.

### Outputs:
- Flow (flow): Pulse triggered after retrieval.
- Name (string): Project Name.
- Version (string): Project Version.
- Category (string): Project Category.
- Description (string): Project Description."""
    name = _bridge.get('ProjectMeta.project_name') or ''
    version = _bridge.get('ProjectMeta.project_version') or '1.0.0'
    category = _bridge.get('ProjectMeta.project_category') or ''
    description = _bridge.get('ProjectMeta.project_description') or ''
    _bridge.set(f'{_node_id}_ActivePorts', ['Flow'], _node.name)
    return {'Name': name, 'Version': version, 'Category': category, 'Description': description}


@axon_node(category="Workflow", version="2.3.0", node_label="Project Metadata Set")
def ProjectMetadataSetNode(Name: str = '', Version: str = '1.0.0', Category: str = '', Description: str = '', _bridge: Any = None, _node: Any = None, _node_id: str = None, **kwargs) -> Any:
    """Updates project metadata in the bridge.

### Inputs:
- Flow (flow): Trigger the update.
- Name (string): New Project Name.
- Version (string): New Project Version.
- Category (string): New Project Category.
- Description (string): New Project Description.

### Outputs:
- Flow (flow): Pulse triggered after the update."""
    name = kwargs.get('Name') or _node.properties.get('Name')
    version = kwargs.get('Version') or _node.properties.get('Version')
    category = kwargs.get('Category') or _node.properties.get('Category')
    description = kwargs.get('Description') or _node.properties.get('Description')
    if name is not None:
        _bridge.set('ProjectMeta.project_name', name, _node.name)
    else:
        pass
    if version is not None:
        _bridge.set('ProjectMeta.project_version', version, _node.name)
    else:
        pass
    if category is not None:
        _bridge.set('ProjectMeta.project_category', category, _node.name)
    else:
        pass
    if description is not None:
        _bridge.set('ProjectMeta.project_description', description, _node.name)
    else:
        pass
    _node.logger.info(f'Updated Project Metadata: {name} v{version}')
    _bridge.set(f'{_node_id}_ActivePorts', ['Flow'], _node.name)
    return True
