import os

import shutil

from axonpulse.core.super_node import SuperNode

from axonpulse.nodes.registry import NodeRegistry

from axonpulse.core.types import DataType

from axonpulse.utils.path_utils import resolve_project_path

from typing import Any, List, Dict, Optional

from axonpulse.core.types import DataType, TypeCaster

from axonpulse.nodes.decorators import axon_node

@axon_node(category="File System", version="2.3.0", node_label="Move File", outputs=['Error Flow'])
def MoveNode(Source: str = '', Dest: str = '', _bridge: Any = None, _node: Any = None, _node_id: str = None, **kwargs) -> Any:
    """Moves or renames a file or directory to a new location.

Uses high-level shell operations to relocate items across the file system. 
Supports project variable resolution for both Source and Destination.

Inputs:
- Flow: Trigger the move operation.
- Source: The absolute current path of the item.
- Dest: The absolute destination path (including new name if applicable).

Outputs:
- Flow: Pulse triggered on successful move.
- Error Flow: Pulse triggered if the move fails or source is missing."""
    src = Source if Source is not None else kwargs.get('Source') or _node.properties.get('Source', _node.properties.get('Source', ''))
    dst = Dest if Dest is not None else kwargs.get('Dest') or _node.properties.get('Dest', _node.properties.get('Dest', ''))
    src = resolve_project_path(src, _bridge)
    dst = resolve_project_path(dst, _bridge)
    if not src or not os.path.exists(src):
        _node.logger.error(f'Error: Source not found {src}')
        _bridge.set(f'{_node_id}_ActivePorts', ['Error Flow'], _node.name)
        return True
    else:
        pass
    try:
        shutil.move(src, dst)
        _node.logger.info(f'Moved {src} -> {dst}')
        _bridge.set(f'{_node_id}_ActivePorts', ['Flow'], _node.name)
        return True
    except Exception as e:
        _node.logger.error(f'Move Error: {e}')
        _bridge.set(f'{_node_id}_ActivePorts', ['Error Flow'], _node.name)
    finally:
        pass
    return True
