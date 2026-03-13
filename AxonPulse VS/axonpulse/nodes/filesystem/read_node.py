from axonpulse.core.super_node import SuperNode

from axonpulse.nodes.registry import NodeRegistry

from axonpulse.core.types import DataType

from axonpulse.utils.path_utils import resolve_project_path

import os

from typing import Any, List, Dict, Optional

from axonpulse.core.types import DataType, TypeCaster

from axonpulse.nodes.decorators import axon_node

@axon_node(category="File System", version="2.3.0", node_label="Read File", outputs=['Error Flow', 'Data'])
def ReadNode(Path: str = 'data.txt', Start: Any = 0, End: Any = -1, _bridge: Any = None, _node: Any = None, _node_id: str = None, **kwargs) -> Any:
    """Reads content from a file path with support for smart type detection.

This node can read plain text, JSON (as objects), or Images (as ImageObjects). 
It supports project variable resolution (e.g., %ID%) and permission checks.

Inputs:
- Flow: Trigger the read operation.
- Path: The absolute path to the file.
- Start: Starting character offset (for text).
- End: Ending character offset (-1 for until EOF).

Outputs:
- Flow: Pulse triggered on successful read.
- Error Flow: Pulse triggered if the file is missing or error occurs.
- Data: The content retrieved (String, Dict, or ImageObject)."""
    path = Path if Path is not None else kwargs.get('Path') or _node.properties.get('Path', _node.properties.get('Path', 'data.txt'))
    start_val = Start if Start is not None else kwargs.get('Start') or _node.properties.get('Start', _node.properties.get('StartOffset'))
    if start_val is None or start_val == '':
        start_val = 0
    else:
        pass
    start = int(start_val)
    end_val = End if End is not None else kwargs.get('End') or _node.properties.get('End', _node.properties.get('EndOffset'))
    if end_val is None or end_val == '':
        end_val = -1
    else:
        pass
    end = int(end_val)
    path = resolve_project_path(path, _bridge)
    if not os.path.exists(path):
        _node.logger.error(f'File not found: {path}')
        _bridge.set(f'{_node_id}_ActivePorts', ['Error Flow'], _node.name)
    else:
        pass
    user_provider_id = self.get_provider_id('User Provider')
    if user_provider_id:
        user_provider = _bridge.get(user_provider_id)
        if user_provider and hasattr(user_provider, 'has_permission'):
            if not user_provider.has_permission('file system'):
                _node.logger.error("Permission Denied: User lacks 'file system' access.")
                _bridge.set(f'{_node_id}_ActivePorts', ['Error Flow'], _node.name)
            else:
                pass
        else:
            pass
    else:
        pass
    try:
        ext = os.path.splitext(path)[1].lower()
        data = None
        if ext in ['.jpg', '.jpeg', '.png', '.bmp', '.gif']:
            from PIL import Image as PILImg
            from axonpulse.nodes.media.camera import ImageObject
            img = PILImg.open(path)
            data = ImageObject(img)
            _node.logger.info(f'Smart Read: Loaded Image from {os.path.basename(path)}')
        elif ext == '.json':
            with open(path, 'r', encoding='utf-8') as f:
                import json
                data = json.load(f)
            _node.logger.info(f'Smart Read: Parsed JSON from {os.path.basename(path)}')
        else:
            with open(path, 'r', encoding='utf-8') as f:
                if start > 0:
                    f.seek(start)
                else:
                    pass
                if end != -1:
                    length = end - start
                    data = f.read(length) if length > 0 else ''
                else:
                    data = f.read()
            _node.logger.info(f'Read {len(data)} chars from {os.path.basename(path)}')
        if self.is_hijacked:
            provider_id = kwargs.get('HijackProviderId')
            data = _bridge.invoke_hijack(provider_id, 'Read File', data)
        else:
            pass
        _bridge.set(f'{_node_id}_ActivePorts', ['Flow'], _node.name)
    except Exception as e:
        _node.logger.error(f'Read Error: {e}')
        _bridge.set(f'{_node_id}_ActivePorts', ['Error Flow'], _node.name)
    finally:
        pass
    return {'Data': data}
