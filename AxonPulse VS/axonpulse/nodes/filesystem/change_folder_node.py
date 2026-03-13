import os

from axonpulse.core.super_node import SuperNode

from axonpulse.nodes.registry import NodeRegistry

from axonpulse.core.types import DataType

from typing import Any, List, Dict, Optional

from axonpulse.core.types import DataType, TypeCaster

from axonpulse.nodes.decorators import axon_node

@axon_node(category="File System", version = "2.3.0", node_label="Change Folder", outputs=['Error Flow'])
def ChangeFolderNode(Path: str = '', _bridge: Any = None, _node: Any = None, _node_id: str = None, **kwargs) -> Any:
    """Changes the current working directory or global path reference for file operations.
Validates that the target path exists and is a directory before applying the change.

Inputs:
- Flow: Trigger the path change.
- Path: The absolute or relative path to switch to.

Outputs:
- Flow: Triggered if the path was successfully changed.
- Error Flow: Triggered if the path is invalid or inaccessible."""
    val = Path if Path is not None else kwargs.get('Path') or _node.properties.get('Path', '')
    success = False
    if val:
        if os.path.exists(val) and os.path.isdir(val):
            abs_path = os.path.abspath(val)
            _node.logger.info(f'Changing Global Path -> {abs_path}')
            _bridge.set('path', abs_path, _node.name)
            success = True
        else:
            _node.logger.error(f'Path not found or not dir: {val}')
    else:
        pass
    target = 'Flow' if success else 'Error Flow'
    _bridge.set(f'{_node_id}_ActivePorts', [target], _node.name)
    return True
