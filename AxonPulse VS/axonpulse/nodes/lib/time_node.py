from axonpulse.core.super_node import SuperNode

from axonpulse.nodes.registry import NodeRegistry

from datetime import datetime

from axonpulse.core.types import DataType

from typing import Any, List, Dict, Optional

from axonpulse.core.types import DataType, TypeCaster

from axonpulse.nodes.decorators import axon_node

@axon_node(category="System/Time", version="2.3.0", node_label="Time", outputs=['Time'])
def TimeNode(_bridge: Any = None, _node: Any = None, _node_id: str = None, **kwargs) -> Any:
    """Captures the current system date and time.
Returns the timestamp in a standardized format inside AxonPulse tags.

Inputs:
- Flow: Trigger the time capture.

Outputs:
- Flow: Pulse triggered after time is captured.
- Time: The current timestamp string (e.g., #[2024-05-20 12:00:00]#)."""
    now_raw = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    now = f'#[{now_raw}]#'
    _bridge.set(f'{_node_id}_ActivePorts', ['Flow'], _node.name)
    return now
