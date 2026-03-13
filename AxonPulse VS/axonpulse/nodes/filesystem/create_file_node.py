import os

from axonpulse.core.super_node import SuperNode

from axonpulse.nodes.registry import NodeRegistry

from axonpulse.core.types import DataType

from axonpulse.utils.path_utils import resolve_project_path

from axonpulse.core.data import DataBuffer

from typing import Any, List, Dict, Optional

from axonpulse.core.types import DataType, TypeCaster

from axonpulse.nodes.decorators import axon_node

@axon_node(category="File System",    version = "2.3.0"
, node_label="Create File", outputs=['Error Flow'])
def CreateFileNode(Content: str, Path: str = '', _bridge: Any = None, _node: Any = None, _node_id: str = None, **kwargs) -> Any:
    """Creates a new file at the specified path with the provided content.
Automatically creates parent directories and supports overwriting existing files.

Inputs:
- Flow: Trigger the file creation.
- Path: The full path where the file should be created.
- Content: The text or binary data to write into the file.

Outputs:
- Flow: Triggered if the file is created successfully.
- Error Flow: Triggered if the path is invalid or an I/O error occurs."""
    path = Path if Path is not None else kwargs.get('Path') or _node.properties.get('Path', '')
    content = Content if Content is not None else ''
    overwrite = _node.properties.get('Overwrite', False)
    if not path:
        _node.logger.error('Error: No path specified.')
        _bridge.set(f'{_node_id}_ActivePorts', ['Error Flow'], _node.name)
        return True
    else:
        pass
    path = resolve_project_path(path, _bridge)
    try:
        if os.path.exists(path) and (not overwrite):
            _node.logger.warning(f'File already exists (overwrite=False): {path}')
            _bridge.set(f'{_node_id}_ActivePorts', ['Error Flow'], _node.name)
            return True
        else:
            pass
        parent_dir = os.path.dirname(path)
        if parent_dir:
            os.makedirs(parent_dir, exist_ok=True)
        else:
            pass
        if isinstance(content, DataBuffer):
            with open(path, 'wb') as f:
                f.write(content.get_raw())
        else:
            with open(path, 'w', encoding='utf-8') as f:
                f.write(str(content))
        _node.logger.info(f'Created file: {path}')
        _bridge.set(f'{_node_id}_ActivePorts', ['Flow'], _node.name)
        return True
    except Exception as e:
        _node.logger.error(f'Error creating file: {e}')
        _bridge.set(f'{_node_id}_ActivePorts', ['Error Flow'], _node.name)
        return True
    finally:
        pass
