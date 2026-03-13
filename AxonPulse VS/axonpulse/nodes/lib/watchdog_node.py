from axonpulse.core.super_node import SuperNode

from axonpulse.nodes.registry import NodeRegistry

from axonpulse.core.types import DataType

import time

from typing import Any, List, Dict, Optional

from axonpulse.core.types import DataType, TypeCaster

from axonpulse.nodes.decorators import axon_node

try:
    import psutil
except ImportError:
    psutil = None

@axon_node(category="System/Monitor", version="2.3.0", node_label="Watchdog", outputs=['CPU', 'RAM', 'Drives', 'OS'])
def WatchdogNode(_bridge: Any = None, _node: Any = None, _node_id: str = None, **kwargs) -> Any:
    """Monitors system resource usage including CPU, RAM, and Disk space.
Provides real-time telemetry about the host operating system.

Inputs:
- Flow: Trigger the resource check.

Outputs:
- Flow: Pulse triggered after data is captured.
- CPU: Total CPU usage percentage (FLOAT).
- RAM: Total RAM usage percentage (FLOAT).
- Drives: List of connected drives and their usage (LIST).
- OS: The name of the host operating system (STRING)."""
    import platform
    current_os = platform.system()
    if not psutil:
        _node.logger.error("'psutil' not installed.")
        _bridge.set(f'{_node_id}_ActivePorts', ['Flow'], _node.name)
    else:
        pass
    cpu = psutil.cpu_percent(interval=0.1)
    ram = psutil.virtual_memory().percent
    drives = []
    try:
        partitions = psutil.disk_partitions()
        for p in partitions:
            try:
                usage = psutil.disk_usage(p.mountpoint)
                total_gb = usage.total / 1024 ** 3
                used_gb = usage.used / 1024 ** 3
                drives.append(f'{p.device} {used_gb:.1f}GB/{total_gb:.1f}GB')
            except PermissionError:
                continue
            finally:
                pass
    except Exception as e:
        _node.logger.error(f'Disk Error: {e}')
    finally:
        pass
    _bridge.set(f'{_node_id}_ActivePorts', ['Flow'], _node.name)
    return {'CPU': cpu, 'RAM': ram, 'Drives': drives, 'OS': current_os}
