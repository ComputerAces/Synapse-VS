from axonpulse.core.super_node import SuperNode

from axonpulse.nodes.registry import NodeRegistry

from axonpulse.core.types import DataType

from axonpulse.utils.path_utils import resolve_project_path

import os

from typing import Any, List, Dict, Optional

from axonpulse.core.types import DataType, TypeCaster

from axonpulse.nodes.decorators import axon_node

@axon_node(category="File System", version="2.3.0", node_label="List Files", outputs=['Files List'])
def ListFilesNode(Path: str = '', _bridge: Any = None, _node: Any = None, _node_id: str = None, **kwargs) -> Any:
    """Retrieves a list of filenames within a specified directory.

Filters for files only (excluding subdirectories). Supports project 
variable resolution and defaults to the current working directory if empty.

Inputs:
- Flow: Trigger the listing operation.
- Path: The absolute path of the folder to scan.

Outputs:
- Flow: Pulse triggered after the operation.
- Files List: A list of strings containing the names of files found."""
    raw_path = Path if Path is not None else kwargs.get('Path') or _node.properties.get('Path', _node.properties.get('Path', ''))
    if not raw_path:
        raw_path = os.getcwd()
    else:
        pass
    target_path = resolve_project_path(raw_path, _bridge)
    target_path = os.path.abspath(target_path)
    results = []
    if os.path.exists(target_path) and os.path.isdir(target_path):
        try:
            results = [f for f in os.listdir(target_path) if os.path.isfile(os.path.join(target_path, f))]
            _node.logger.info(f'Listing {target_path}: {len(results)} files')
        except Exception as e:
            _node.logger.error(f'Error listing {target_path}: {e}')
        finally:
            pass
    else:
        _node.logger.error(f'Invalid Directory: {target_path}')
    _bridge.set(f'{_node_id}_ActivePorts', ['Flow'], _node.name)
    return results
