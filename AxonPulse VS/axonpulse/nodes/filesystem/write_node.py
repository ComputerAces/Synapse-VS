from axonpulse.core.super_node import SuperNode

from axonpulse.nodes.registry import NodeRegistry

from axonpulse.core.types import DataType

from axonpulse.utils.path_utils import resolve_project_path

import os

from typing import Any, List, Dict, Optional

from axonpulse.core.types import DataType, TypeCaster

from axonpulse.nodes.decorators import axon_node

@axon_node(category="File System", version="2.3.0", node_label="Write File", outputs=['Error Flow'])
def WriteNode(Data: Any, Path: str = 'output.txt', Mode: Any = 'Overwrite', Start_Position: float = 0, _bridge: Any = None, _node: Any = None, _node_id: str = None, **kwargs) -> Any:
    """Writes data to a specified file path with smart type detection.

Supports writing Text, Binary (bytes), JSON (as objects), and Images 
(PIL objects). Automatically creates parent directories if they are missing.

Inputs:
- Flow: Trigger the write operation.
- Path: The absolute destination file path.
- Data: The content to write (String, Bytes, Dict, or Image).
- Mode: Writing behavior ('Overwrite' or 'Append').
- Start Position: Byte offset to start writing from (optional).

Outputs:
- Flow: Pulse triggered on successful write.
- Error Flow: Pulse triggered if permission denied or error occurs."""
    path = Path if Path is not None else kwargs.get('Path') or _node.properties.get('Path', 'output.txt')
    start_pos = int(Start_Position) if Start_Position is not None else int(_node.properties.get('Start Position', 0))
    user_provider_id = self.get_provider_id('User Provider')
    if user_provider_id:
        user_provider = _bridge.get(user_provider_id)
        if user_provider and hasattr(user_provider, 'has_permission'):
            if not user_provider.has_permission('file system'):
                _node.logger.error("Permission Denied: User lacks 'file system' access.")
                _bridge.set(f'{_node_id}_ActivePorts', ['Error Flow'], _node.name)
                return True
            else:
                pass
        else:
            pass
    else:
        pass
    path = resolve_project_path(path, _bridge)
    mode_val = Mode or kwargs.get('Mode') or _node.properties.get('Mode', 'Overwrite')
    is_append = mode_val in ['Append', 'a']
    try:
        os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
        if hasattr(Data, 'save') and (not isinstance(Data, (str, bytes, bytearray))):
            try:
                Data.save(path)
                _node.logger.info(f'Smart Write: Saved Image to {os.path.basename(path)}')
                _bridge.set(f'{_node_id}_ActivePorts', ['Flow'], _node.name)
                return True
            except Exception as ie:
                _node.logger.error(f'Image Save Error: {ie}')
            finally:
                pass
        else:
            pass
        if isinstance(Data, (bytes, bytearray)):
            open_mode = 'rb+' if start_pos > 0 else 'ab' if is_append else 'wb'
            with open(path, open_mode) as f:
                if start_pos > 0:
                    f.seek(start_pos)
                else:
                    pass
                f.write(Data)
            _node.logger.info(f'Smart Write: Wrote {len(Data)} bytes (Binary)')
            _bridge.set(f'{_node_id}_ActivePorts', ['Flow'], _node.name)
            return True
        else:
            pass
        if isinstance(Data, (dict, list)):
            with open(path, 'w', encoding='utf-8') as f:
                import json
                json.dump(Data, f, indent=4)
            _node.logger.info(f'Smart Write: Wrote JSON object to {os.path.basename(path)}')
            _bridge.set(f'{_node_id}_ActivePorts', ['Flow'], _node.name)
            return True
        else:
            pass
        text_data = str(Data) if Data is not None else ''
        open_mode = 'r+' if start_pos > 0 else 'a' if is_append else 'w'
        with open(path, open_mode, encoding='utf-8') as f:
            if start_pos > 0:
                f.seek(start_pos)
            else:
                pass
            f.write(text_data)
        _node.logger.info(f'Smart Write: Wrote {len(text_data)} chars (Text)')
        _bridge.set(f'{_node_id}_ActivePorts', ['Flow'], _node.name)
        return True
    except Exception as e:
        _node.logger.error(f'Write Error: {e}')
        _bridge.set(f'{_node_id}_ActivePorts', ['Error Flow'], _node.name)
    finally:
        pass
    return True
