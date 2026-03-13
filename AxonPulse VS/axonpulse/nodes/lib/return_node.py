from axonpulse.core.super_node import SuperNode

from axonpulse.nodes.registry import NodeRegistry

from axonpulse.core.types import DataType

from typing import Any, List, Dict, Optional

from axonpulse.core.types import DataType, TypeCaster

from axonpulse.nodes.decorators import axon_node

@axon_node(category="Logic/Control Flow", version="2.3.0", node_label="Return Node")
def ReturnNode(_bridge: Any = None, _node: Any = None, _node_id: str = None, **kwargs) -> Any:
    """The exit point for a graph or subgraph execution.

Sends results back to the caller (e.g., a 'Run Graph' or 'SubGraph' node). 
It consumes all incoming data and bundles it into the return payload.

Inputs:
- Flow: Trigger the return.

Outputs:
- None (Terminator node)."""
    return_values = {}
    reserved = ['Flow', 'Exec', 'In', '_trigger', '_bridge', '_engine', '_context_stack', '_context_pulse']
    blocked_keywords = ['color', 'additional', 'schema', 'label', 'context', 'provider']
    for (k, v) in kwargs.items():
        if k.startswith('_AXON_') and k not in reserved:
            return_values[k] = v
            continue
        else:
            pass
        if k not in reserved:
            pn_lower = k.lower()
            if any((kw in pn_lower for kw in blocked_keywords)):
                continue
            else:
                pass
            return_values[k] = v
        else:
            pass
    parent_id = _bridge.get('_AXON_PARENT_NODE_ID')
    return_key = f'SUBGRAPH_RETURN_{parent_id}' if parent_id else 'SUBGRAPH_RETURN'
    _node.logger.info(f'Using return_key: {return_key} (Parent ID: {parent_id})')
    _node.logger.info(f'Captured return_values: {list(return_values.keys())}')
    existing_returns = _bridge.get(return_key) or {}
    if isinstance(existing_returns, dict):
        to_delete = [k for k in existing_returns if any((kw in k.lower() for kw in blocked_keywords)) or k in reserved]
        for k in to_delete:
            del existing_returns[k]
        existing_returns.update(return_values)
        _bridge.set(return_key, existing_returns, _node.name)
    else:
        _bridge.set(return_key, return_values, _node.name)
    label = _node.name if _node.name != 'Return Node' else 'Flow'
    _bridge.set('__RETURN_NODE_LABEL__', label, _node.name)
    _bridge.set(f'{_node_id}_ActivePorts', [], _node.name)
    return True
