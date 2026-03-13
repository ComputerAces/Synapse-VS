from axonpulse.core.super_node import SuperNode

from axonpulse.nodes.registry import NodeRegistry

from axonpulse.core.types import DataType, TypeCaster

from typing import Any, List, Dict, Optional

from axonpulse.nodes.decorators import axon_node

@axon_node(category="Math/Logic", version="2.3.0", node_label="Boolean Flip")
def BooleanFlipNode(Value: bool = False, _bridge: Any = None, _node: Any = None, _node_id: str = None, **kwargs) -> Any:
    """Inverts the provided boolean value (True becomes False, and vice-versa).

Inputs:
- Flow: Trigger the inversion.
- Value: The boolean value to flip.

Outputs:
- Flow: Triggered after the flip.
- Result: The inverted boolean result."""
    val = Value if Value is not None else _node.properties.get('Value', False)
    result = not TypeCaster.to_bool(val)
    _bridge.set(f'{_node_id}_ActivePorts', ['Flow'], _node.name)
    return result


@axon_node(category="Math/Logic", version="2.3.0", node_label="AND")
def AndNode(_bridge: Any = None, _node: Any = None, _node_id: str = None, **kwargs) -> Any:
    """Performs a logical AND operation on a set of boolean inputs.
Returns True only if all provided inputs are True.

Inputs:
- Flow: Trigger the logical check.
- Item 0, Item 1...: Boolean values to evaluate (supports dynamic expansion).

Outputs:
- Flow: Triggered after evaluation.
- Result: True if all inputs are True, False otherwise."""
    candidates = {k: v for (k, v) in kwargs.items() if k.startswith('Item')}
    for (k, v) in _node.properties.items():
        if k.startswith('Item') and k not in candidates:
            candidates[k] = v
        else:
            pass
    inputs = [TypeCaster.to_bool(v) for v in candidates.values()]
    result = all(inputs) if inputs else False
    _bridge.set(f'{_node_id}_ActivePorts', ['Flow'], _node.name)
    return result


@axon_node(category="Math/Logic", version="2.3.0", node_label="OR")
def OrNode(_bridge: Any = None, _node: Any = None, _node_id: str = None, **kwargs) -> Any:
    """Performs a logical OR operation on a set of boolean inputs.

Returns True if at least one of the provided inputs is True. 
Supports dynamic input expansion.

Inputs:
- Flow: Trigger the logical check.
- Item 0, Item 1...: Boolean values to evaluate.

Outputs:
- Flow: Triggered after evaluation.
- Result: True if any input is True, False otherwise."""
    candidates = {k: v for (k, v) in kwargs.items() if k.startswith('Item')}
    for (k, v) in _node.properties.items():
        if k.startswith('Item') and k not in candidates:
            candidates[k] = v
        else:
            pass
    inputs = [TypeCaster.to_bool(v) for v in candidates.values()]
    result = any(inputs) if inputs else False
    _bridge.set(f'{_node_id}_ActivePorts', ['Flow'], _node.name)
    return result


@axon_node(category="Math/Logic", version="2.3.0", node_label="XOR")
def XorNode(_bridge: Any = None, _node: Any = None, _node_id: str = None, **kwargs) -> Any:
    """Performs a logical XOR (Exclusive OR) operation.

Returns True if an odd number of inputs are True. Supports 
dynamic input expansion.

Inputs:
- Flow: Trigger the logical check.
- Item 0, Item 1...: Boolean values to evaluate.

Outputs:
- Flow: Triggered after evaluation.
- Result: True if the XOR condition is met."""
    candidates = {k: v for (k, v) in kwargs.items() if k.startswith('Item')}
    for (k, v) in _node.properties.items():
        if k.startswith('Item') and k not in candidates:
            candidates[k] = v
        else:
            pass
    inputs = [TypeCaster.to_bool(v) for v in candidates.values()]
    true_count = sum((1 for v in inputs if v))
    result = true_count % 2 == 1
    _bridge.set(f'{_node_id}_ActivePorts', ['Flow'], _node.name)
    return result


@axon_node(category="Math/Logic", version="2.3.0", node_label="NOT")
def NotNode(In: bool = False, _bridge: Any = None, _node: Any = None, _node_id: str = None, **kwargs) -> Any:
    """Logical NOT operator. Inverts the input boolean.

Inputs:
- Flow: Trigger execution.
- In: The input boolean value.

Outputs:
- Flow: Triggered after inversion.
- Result: The inverted result."""
    val = In if In is not None else _node.properties.get('In', False)
    _bridge.set(f'{_node_id}_ActivePorts', ['Flow'], _node.name)
    return not TypeCaster.to_bool(val)


@axon_node(category="Math/Logic", version="2.3.0", node_label="NAND")
def NandNode(_bridge: Any = None, _node: Any = None, _node_id: str = None, **kwargs) -> Any:
    """Performs a logical NAND operation.

Returns True if at least one input is False. Returns False only 
if all provided inputs are True. Supports dynamic input expansion.

Inputs:
- Flow: Trigger the logical check.
- Item 0, Item 1...: Boolean values to evaluate.

Outputs:
- Flow: Triggered after evaluation.
- Result: The NAND result."""
    candidates = {k: v for (k, v) in kwargs.items() if k.startswith('Item')}
    for (k, v) in _node.properties.items():
        if k.startswith('Item') and k not in candidates:
            candidates[k] = v
        else:
            pass
    inputs = [TypeCaster.to_bool(v) for v in candidates.values()]
    result = not all(inputs) if inputs else True
    _bridge.set(f'{_node_id}_ActivePorts', ['Flow'], _node.name)
    return result


@axon_node(category="Math/Logic", version="2.3.0", node_label="NOR")
def NorNode(_bridge: Any = None, _node: Any = None, _node_id: str = None, **kwargs) -> Any:
    """Performs a logical NOR operation.

Returns True only if all provided inputs are False. Returns False 
 if at least one input is True. Supports dynamic input expansion.

Inputs:
- Flow: Trigger the logical check.
- Item 0, Item 1...: Boolean values to evaluate.

Outputs:
- Flow: Triggered after evaluation.
- Result: The NOR result."""
    candidates = {k: v for (k, v) in kwargs.items() if k.startswith('Item')}
    for (k, v) in _node.properties.items():
        if k.startswith('Item') and k not in candidates:
            candidates[k] = v
        else:
            pass
    inputs = [TypeCaster.to_bool(v) for v in candidates.values()]
    result = not any(inputs) if inputs else True
    _bridge.set(f'{_node_id}_ActivePorts', ['Flow'], _node.name)
    return result


@axon_node(category="Math/Logic", version="2.3.0", node_label="XNOR")
def XnorNode(_bridge: Any = None, _node: Any = None, _node_id: str = None, **kwargs) -> Any:
    """Performs a logical XNOR operation.

Returns True if an even number of inputs are True. Supports 
dynamic input expansion.

Inputs:
- Flow: Trigger the logical check.
- Item 0, Item 1...: Boolean values to evaluate.

Outputs:
- Flow: Triggered after evaluation.
- Result: The XNOR result."""
    candidates = {k: v for (k, v) in kwargs.items() if k.startswith('Item')}
    for (k, v) in _node.properties.items():
        if k.startswith('Item') and k not in candidates:
            candidates[k] = v
        else:
            pass
    inputs = [TypeCaster.to_bool(v) for v in candidates.values()]
    true_count = sum((1 for v in inputs if v))
    result = true_count % 2 == 0
    _bridge.set(f'{_node_id}_ActivePorts', ['Flow'], _node.name)
    return result
