from axonpulse.core.super_node import SuperNode

from axonpulse.nodes.registry import NodeRegistry

from axonpulse.core.types import DataType

from typing import Any, List, Dict, Optional

from axonpulse.core.types import DataType, TypeCaster

from axonpulse.nodes.decorators import axon_node

@axon_node(category="Data", version="2.3.0", node_label="Currency")
def CurrencyNode(Value: float = 0.0, _bridge: Any = None, _node: Any = None, _node_id: str = None, **kwargs) -> Any:
    """Standardizes a numerical value into a currency format (rounded to 2 decimal places).

Inputs:
- Flow: Trigger the currency formatting.
- Value: The raw numerical value to process.

Outputs:
- Flow: Triggered after the value is formatted.
- Result: The formatted numerical value (2-decimal float)."""
    is_val_provided = Value is not None or 'Value' in kwargs
    raw = Value if Value is not None else kwargs.get('Value') or _node.properties.get('Value', 0.0)
    try:
        val = float(raw)
    except (ValueError, TypeError):
        val = 0.0
    finally:
        pass
    val = round(val, 2)
    if is_val_provided:
        _node.properties['Value'] = val
    else:
        pass
    _bridge.set(f'{_node_id}_ActivePorts', ['Flow'], _node.name)
    return val
