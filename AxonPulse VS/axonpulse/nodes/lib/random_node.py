from axonpulse.core.super_node import SuperNode

from axonpulse.nodes.registry import NodeRegistry

import random

from axonpulse.core.types import DataType

from typing import Any, List, Dict, Optional

from axonpulse.core.types import DataType, TypeCaster

from axonpulse.nodes.decorators import axon_node

@axon_node(category="Math/Random", version="2.3.0", node_label="Random")
def RandomNode(Min: Any = 0, Max: Any = 100, Random_Type: str = 'Number', _bridge: Any = None, _node: Any = None, _node_id: str = None, **kwargs) -> Any:
    """Generates a pseudo-random number or currency value within a specified range.
Supports both integer 'Number' and decimal 'Currency' (2 decimal places) types.

Inputs:
- Flow: Trigger the random generation.
- Min: The minimum value of the range.
- Max: The maximum value of the range.
- Random Type: The type of output ('Number' or 'Currency').

Outputs:
- Flow: Pulse triggered after generation.
- Result: The generated random value."""
    min_val = float(Min if Min is not None else kwargs.get('Min') or _node.properties.get('Min', 0))
    max_val = float(Max if Max is not None else kwargs.get('Max') or _node.properties.get('Max', 100))
    rtype = kwargs.get('Random Type') or _node.properties.get('Random Type') or 'Number'
    if rtype == 'Currency':
        val = random.uniform(min_val, max_val)
        val = round(val, 2)
    else:
        start = int(min_val)
        stop = int(max_val)
        if stop <= start:
            stop = start + 1
        else:
            pass
        val = random.randrange(start, stop)
    _node.logger.info(f'Random ({rtype}): {val}')
    _bridge.set(f'{_node_id}_ActivePorts', ['Flow'], _node.name)
    return val
