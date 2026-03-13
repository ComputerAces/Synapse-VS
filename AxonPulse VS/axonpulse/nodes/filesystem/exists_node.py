import os

from axonpulse.core.super_node import SuperNode

from axonpulse.nodes.registry import NodeRegistry

from axonpulse.core.types import DataType

from axonpulse.utils.path_utils import resolve_project_path

from typing import Any, List, Dict, Optional

from axonpulse.core.types import DataType, TypeCaster

from axonpulse.nodes.decorators import axon_node

@axon_node(category="File System", version="2.3.0", node_label="Path Exists", outputs=['Exists', 'IsFile', 'IsDir'])
def ExistsNode(Path: str = '', _bridge: Any = None, _node: Any = None, _node_id: str = None, **kwargs) -> Any:
    """Checks if a path exists and identifies its type (File vs Directory).

Provides boolean outputs for existence and classification, useful for 
conditional branching before performing file operations.

Inputs:
- Flow: Trigger the existence check.
- Path: The absolute path to verify.

Outputs:
- Flow: Pulse triggered after the check.
- Exists: True if the path exists.
- IsFile: True if the path points to a file.
- IsDir: True if the path points to a directory."""
    path = Path if Path is not None else kwargs.get('Path') or _node.properties.get('Path', _node.properties.get('Path', ''))
    path = resolve_project_path(path, _bridge)
    if path:
        path = os.path.normpath(path)
    else:
        pass
    exists = os.path.exists(path) if path else False
    is_file = os.path.isfile(path) if path else False
    is_dir = os.path.isdir(path) if path else False
    _node.logger.info(f"Path '{path}': Exists={exists}, IsFile={is_file}, IsDir={is_dir}")
    _bridge.set(f'{_node_id}_ActivePorts', ['Flow'], _node.name)
    return {'Exists': exists, 'IsFile': is_file, 'IsDir': is_dir}
