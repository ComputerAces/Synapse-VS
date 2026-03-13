import os

import shutil

from axonpulse.core.super_node import SuperNode

from axonpulse.nodes.registry import NodeRegistry

from axonpulse.core.types import DataType

from axonpulse.utils.path_utils import resolve_project_path

from typing import Any, List, Dict, Optional

from axonpulse.core.types import DataType, TypeCaster

from axonpulse.nodes.decorators import axon_node

@axon_node(category="File System", version="2.3.0", node_label="Delete File", outputs=['Error Flow'])
def DeleteNode(Path: str = '', _bridge: Any = None, _node: Any = None, _node_id: str = None, **kwargs) -> Any:
    """Deletes a file or directory from the filesystem.

Inputs:
- Flow: Execution trigger.
- Path: The absolute or relative path to the item to delete.

Outputs:
- Flow: Triggered after the deletion attempt.
- Error Flow: Triggered if the deletion failed."""
    path = Path if Path is not None else kwargs.get('Path') or _node.properties.get('Path', _node.properties.get('Path', ''))
    path = resolve_project_path(path, _bridge)
    if not path or not os.path.exists(path):
        _node.logger.warning(f'Warning: File not found {path}')
        _bridge.set(f'{_node_id}_ActivePorts', ['Flow'], _node.name)
        return True
    else:
        pass
    user_provider_id = self.get_provider_id('User Provider')
    if user_provider_id:
        user_provider = _bridge.get(user_provider_id)
        if user_provider and hasattr(user_provider, 'has_permission'):
            if not user_provider.has_permission('file system'):
                _node.logger.error("Permission Denied: User lacks 'file system' access.")
                _bridge.set(f'{_node_id}_ActivePorts', ['Flow'], _node.name)
                return True
            else:
                pass
        else:
            pass
    else:
        pass
    try:
        if os.path.isdir(path):
            shutil.rmtree(path)
        else:
            os.remove(path)
        _node.logger.info(f'Deleted {path}')
        _bridge.set(f'{_node_id}_ActivePorts', ['Flow'], _node.name)
        return True
    except Exception as e:
        _node.logger.error(f'Delete Error: {e}')
        _bridge.set(f'{_node_id}_ActivePorts', ['Error Flow'], _node.name)
    finally:
        pass
    return True
