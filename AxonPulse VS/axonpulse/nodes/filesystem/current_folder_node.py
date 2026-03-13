import os

from axonpulse.core.super_node import SuperNode

from axonpulse.nodes.registry import NodeRegistry

from axonpulse.core.types import DataType

from typing import Any, List, Dict, Optional

from axonpulse.core.types import DataType, TypeCaster

from axonpulse.nodes.decorators import axon_node

@axon_node(category="File System",    version = "2.3.0"
, node_label="Current Folder", outputs=['Path'])
def CurrentFolderNode(_bridge: Any = None, _node: Any = None, _node_id: str = None, **kwargs) -> Any:
    """Retrieves the absolute path of the current working directory or the specific project path context.

Inputs:
- Flow: Trigger the path retrieval.

Outputs:
- Flow: Triggered after the path is retrieved.
- Path: The absolute directory path."""
    path = _bridge.get('path')
    if not path:
        path = os.getcwd()
    else:
        pass
    _node.logger.info(f'Current Folder: {path}')
    _bridge.set(f'{_node_id}_ActivePorts', ['Flow'], _node.name)
    return path
