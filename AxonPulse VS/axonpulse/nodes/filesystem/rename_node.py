import os

from axonpulse.core.super_node import SuperNode

from axonpulse.nodes.registry import NodeRegistry

from axonpulse.core.types import DataType

from axonpulse.utils.path_utils import resolve_project_path

from typing import Any, List, Dict, Optional

from axonpulse.core.types import DataType, TypeCaster

from axonpulse.nodes.decorators import axon_node

@axon_node(category="File System", version="2.3.0", node_label="Rename File", outputs=['Error Flow'])
def RenameNode(OldPath: str = '', NewName: str = '', _bridge: Any = None, _node: Any = None, _node_id: str = None, **kwargs) -> Any:
    """Changes the name of a file or directory while keeping it in the same folder.

This node takes a full path and a new name string, then performs an 
in-place rename within the parent directory.

Inputs:
- Flow: Trigger the rename operation.
- OldPath: The current absolute path of the file.
- NewName: The new name (filename only, not a path).

Outputs:
- Flow: Pulse triggered on successful rename.
- Error Flow: Pulse triggered if the file is missing or rename fails."""
    old = OldPath if OldPath is not None else kwargs.get('OldPath') or _node.properties.get('OldPath', _node.properties.get('OldPath', ''))
    new = NewName if NewName is not None else kwargs.get('NewName') or _node.properties.get('NewName', _node.properties.get('NewName', ''))
    old = resolve_project_path(old, _bridge)
    if not old or not os.path.exists(old):
        _node.logger.error(f'Error: Source not found {old}')
        _bridge.set(f'{_node_id}_ActivePorts', ['Error Flow'], _node.name)
        return True
    else:
        pass
    base_dir = os.path.dirname(old)
    new_path = os.path.join(base_dir, new)
    try:
        os.rename(old, new_path)
        _node.logger.info(f'Renamed to {new_path}')
        _bridge.set(f'{_node_id}_ActivePorts', ['Flow'], _node.name)
        return True
    except Exception as e:
        _node.logger.error(f'Rename Error: {e}')
        _bridge.set(f'{_node_id}_ActivePorts', ['Error Flow'], _node.name)
    finally:
        pass
    return True
