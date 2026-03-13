from axonpulse.core.super_node import SuperNode

from axonpulse.nodes.registry import NodeRegistry

from axonpulse.core.types import DataType

from typing import Any, List, Dict, Optional

from axonpulse.core.types import DataType, TypeCaster

from axonpulse.nodes.decorators import axon_node

@axon_node(category="Logic", version="2.3.0", node_label="Service Return")
def ServiceReturnNode(_bridge: Any = None, _node: Any = None, _node_id: str = None, **kwargs) -> Any:
    """Signals the end of a service or subgraph execution phase.

Used within service graphs to return control and data back to 
the parent graph. It packages all non-flow inputs into a 
return payload.

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
    existing_returns = _bridge.get(return_key) or {}
    if isinstance(existing_returns, dict):
        to_delete = [k for k in existing_returns if any((kw in k.lower() for kw in blocked_keywords)) or k in reserved]
        for k in to_delete:
            del existing_returns[k]
        existing_returns.update(return_values)
        _bridge.set(return_key, existing_returns, _node.name)
    else:
        _bridge.set(return_key, return_values, _node.name)
    _bridge.set('__RETURN_NODE_LABEL__', 'Flow', _node.name)
    print(f'[{_node.name}] Service Yielding control to parent...')
    _bridge.set('_AXON_YIELD', True, _node.name)
    return return_values
