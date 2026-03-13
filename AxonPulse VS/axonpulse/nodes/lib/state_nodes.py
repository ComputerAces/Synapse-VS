from axonpulse.core.super_node import SuperNode

from axonpulse.nodes.registry import NodeRegistry

from axonpulse.core.types import DataType

from typing import Any, List, Dict, Optional

from axonpulse.core.types import DataType, TypeCaster

from axonpulse.nodes.decorators import axon_node

@axon_node(category="System/State", version="2.3.0", node_label="User Activity", outputs=['User Activity', 'Mouse Idle Time', 'Keyboard Idle Time'])
def UserActivityNode(_bridge: Any = None, _node: Any = None, _node_id: str = None, **kwargs) -> Any:
    """Outputs mouse and keyboard idle counters from the engine's ActivityTracker.

The engine runs a background thread that increments idle counters every 250ms.
When the mouse moves, its counter resets to 0. When a key is pressed, its 
counter resets to 0. Each counter is independent.

Inputs:
- Flow: Trigger a read of current idle counters.

Outputs:
- Flow: Always triggered after read.
- User Activity: Boolean — True if either counter is 0 (recent activity).
- Mouse Idle Time: Milliseconds since last mouse movement (resets to 0 on move).
- Keyboard Idle Time: Milliseconds since last key press (resets to 0 on press)."""
    from axonpulse.core.activity_tracker import get_tracker
    tracker = get_tracker()
    mouse_idle = float(tracker.mouse_idle_ms)
    keyboard_idle = float(tracker.keyboard_idle_ms)
    is_active = mouse_idle == 0.0 or keyboard_idle == 0.0
    _bridge.set(f'{_node_id}_ActivePorts', ['Flow'], _node.name)
    return {'User Activity': 1 if is_active else 0, 'Mouse Idle Time': mouse_idle, 'Keyboard Idle Time': keyboard_idle}
