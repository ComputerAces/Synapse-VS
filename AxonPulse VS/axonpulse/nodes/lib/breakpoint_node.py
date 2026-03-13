from axonpulse.core.super_node import SuperNode

from axonpulse.nodes.registry import NodeRegistry

from axonpulse.core.types import DataType

import os

from typing import Any, List, Dict, Optional

from axonpulse.core.types import DataType, TypeCaster

from axonpulse.nodes.decorators import axon_node

@axon_node(category="Flow/Debug", version="2.3.0", node_label="Breakpoint")
def BreakpointNode(_bridge: Any = None, _node: Any = None, _node_id: str = None, **kwargs) -> Any:
    """Temporarily pauses graph execution at this point, allowing manual inspection of state.
Execution can be resumed by the user through the UI or by deleting the pause signal file.
Skipped automatically in Headless mode.

Inputs:
- Flow: Trigger execution to pause here.

Outputs:
- Flow: Triggered immediately (Engine handles the pause step contextually)."""
    headless = _bridge.get('_SYSTEM_HEADLESS')
    if headless:
        _node.logger.info('Breakpoint skipped (Headless Mode).')
        _bridge.set(f'{_node_id}_ActivePorts', ['Flow'], _node.name)
        return True
    else:
        pass
    try:
        _node.logger.warning(f'Breakpoint hit in {_node.name}. Halting Execution Engine.')
        _bridge.set('_AXON_BREAKPOINT_NODE_NAME', _node.name, _node.name)
        _bridge.set('_AXON_BREAKPOINT_ACTIVE', True, _node.name)
        _bridge.set(f'{_node_id}_ActivePorts', ['Flow'], _node.name)
        return ('_YSYIELD',)
    except Exception as e:
        _node.logger.error(f'Failed to trigger Breakpoint: {e}')
        _bridge.set(f'{_node_id}_ActivePorts', ['Flow'], _node.name)
        return True
    finally:
        pass
