import os

import shutil

from axonpulse.core.super_node import SuperNode

from axonpulse.nodes.registry import NodeRegistry

from axonpulse.core.types import DataType

from axonpulse.utils.path_utils import resolve_project_path

from typing import Any, List, Dict, Optional

from axonpulse.core.types import DataType, TypeCaster

from axonpulse.nodes.decorators import axon_node

@axon_node(category="File System",    version = "2.3.0"
, node_label="Copy File", outputs=['Error Flow'])
def CopyNode(Source: str = '', Destination: str = '', _bridge: Any = None, _node: Any = None, _node_id: str = None, **kwargs) -> Any:
    """Copies a file or directory from a source path to a destination path.
Supports recursive directory copying and automatic parent directory creation.

Inputs:
- Flow: Trigger the copy operation.
- Source: The path to the file or folder to copy.
- Destination: The target path where the item should be copied.

Outputs:
- Flow: Triggered if the copy operation completes successfully.
- Error Flow: Triggered if the source is missing or an I/O error occurs."""
    source = Source if Source is not None else kwargs.get('Source') or _node.properties.get('Source', '')
    destination = Destination if Destination is not None else kwargs.get('Destination') or _node.properties.get('Destination', '')
    if not source or not destination:
        _node.logger.error('Error: Source and destination required.')
        _bridge.set(f'{_node_id}_ActivePorts', ['Error Flow'], _node.name)
        return True
    else:
        pass
    source = resolve_project_path(source, _bridge)
    destination = resolve_project_path(destination, _bridge)
    try:
        if not os.path.exists(source):
            _node.logger.error(f'Error: Source not found: {source}')
            _bridge.set(f'{_node_id}_ActivePorts', ['Error Flow'], _node.name)
            return True
        else:
            pass
        dest_dir = os.path.dirname(destination)
        if dest_dir:
            os.makedirs(dest_dir, exist_ok=True)
        else:
            pass
        if os.path.isdir(source):
            shutil.copytree(source, destination, dirs_exist_ok=True)
            _node.logger.info(f'Copied directory: {source} -> {destination}')
        else:
            shutil.copy2(source, destination)
            _node.logger.info(f'Copied file: {source} -> {destination}')
        _bridge.set(f'{_node_id}_ActivePorts', ['Flow'], _node.name)
        return True
    except Exception as e:
        _node.logger.error(f'Error executing copy: {e}')
        _bridge.set(f'{_node_id}_ActivePorts', ['Error Flow'], _node.name)
        return True
    finally:
        pass
