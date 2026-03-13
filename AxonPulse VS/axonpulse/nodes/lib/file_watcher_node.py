from axonpulse.core.super_node import SuperNode

from axonpulse.nodes.registry import NodeRegistry

from axonpulse.core.types import DataType

import os

import datetime

from typing import Any, List, Dict, Optional

from axonpulse.core.types import DataType, TypeCaster

from axonpulse.nodes.decorators import axon_node

@axon_node(category="IO/Files", version="2.3.0", node_label="File Watcher", outputs=['Changed', 'Time'])
def FileWatcherNode(Path: str = '', Last_Time: str = '', _bridge: Any = None, _node: Any = None, _node_id: str = None, **kwargs) -> Any:
    """Monitors a file for changes by comparing its last modification time.

This node checks if the file at 'Path' has been updated since the last check 
or since 'Last Time'. It is useful for triggering logic when a configuration 
file, log, or data export is updated by an external process.

Inputs:
- Flow: Trigger the check.
- Path: The absolute path to the file to monitor.
- Last Time: Optional ISO timestamp to compare against (replaces internal memory).

Outputs:
- Flow: Pulse triggered after the check.
- Changed: Boolean True if the file has been modified.
- Time: The ISO timestamp of the file's current modification time."""
    path_val = Path if Path is not None else kwargs.get('Path') or _node.properties.get('Path', '')
    last_time_val = Last_Time if Last_Time is not None else kwargs.get('Last Time') or _node.properties.get('Last Time', '')
    if not path_val or not os.path.exists(path_val):
        _bridge.set(f'{_node_id}_ActivePorts', ['Flow'], _node.name)
    else:
        pass
    mtime = os.path.getmtime(path_val)
    if last_time_val:
        try:
            import datetime
            dt_cmp = datetime.datetime.fromisoformat(last_time_val.replace(' ', 'T'))
            last_mtime = dt_cmp.timestamp()
        except:
            last_mtime = _node.properties.get('LastMtime', 0.0)
        finally:
            pass
    else:
        last_mtime = _node.properties.get('LastMtime', 0.0)
    changed = mtime > last_mtime
    _node.properties['LastMtime'] = mtime
    dt = datetime.datetime.fromtimestamp(mtime)
    _bridge.set(f'{_node_id}_ActivePorts', ['Flow'], _node.name)
    return {'Changed': False, 'Changed': changed, 'Time': dt.strftime('%Y-%m-%d %H:%M:%S')}
