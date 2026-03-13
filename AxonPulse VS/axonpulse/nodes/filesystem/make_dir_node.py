import os

from axonpulse.core.super_node import SuperNode

from axonpulse.nodes.registry import NodeRegistry

from axonpulse.core.types import DataType

from axonpulse.utils.path_utils import resolve_project_path

from typing import Any, List, Dict, Optional

from axonpulse.core.types import DataType, TypeCaster

from axonpulse.nodes.decorators import axon_node

@axon_node(category="File System", version="2.3.0", node_label="Make Directory", outputs=['Error Flow'])
def MakeDirNode(Path: str = '', _bridge: Any = None, _node: Any = None, _node_id: str = None, **kwargs) -> Any:
    """Creates a new directory at the specified path.

Automatically creates all parent directories if they do not exist 
(equivalent to 'mkdir -p'). Supports project variable resolution.

Inputs:
- Flow: Trigger the directory creation.
- Path: The absolute path of the directory to create.

Outputs:
- Flow: Pulse triggered on successful creation.
- Error Flow: Pulse triggered if the operation fails (e.g., permission denied)."""
    path = Path if Path is not None else kwargs.get('Path') or _node.properties.get('Path', _node.properties.get('Path', ''))
    if not path:
        _node.logger.error('Error: No path specified.')
        _bridge.set(f'{_node_id}_ActivePorts', ['Error Flow'], _node.name)
        return True
    else:
        pass
    path = resolve_project_path(path, _bridge)
    try:
        os.makedirs(path, exist_ok=True)
        _node.logger.info(f'Created directory: {path}')
        _bridge.set(f'{_node_id}_ActivePorts', ['Flow'], _node.name)
        return True
    except Exception as e:
        _node.logger.error(f'Error: {e}')
        _bridge.set(f'{_node_id}_ActivePorts', ['Error Flow'], _node.name)
    finally:
        pass
    return True
