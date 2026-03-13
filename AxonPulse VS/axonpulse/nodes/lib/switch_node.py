from axonpulse.core.super_node import SuperNode

from axonpulse.nodes.registry import NodeRegistry

from axonpulse.core.types import DataType

from typing import Any, List, Dict, Optional

from axonpulse.core.types import DataType, TypeCaster

from axonpulse.nodes.decorators import axon_node

@axon_node(category="Flow/Control", version="2.3.0", node_label="Switch", outputs=['Default'])
def SwitchNode(Value: Any = '', _bridge: Any = None, _node: Any = None, _node_id: str = None, **kwargs) -> Any:
    """Directs execution flow based on a match between an input value and one of several named output ports.

This node functions like if-elif-else or switch-case statements in programming. 
It compares the 'Value' against the names of all custom output ports (cases). 
Matching is string-based and case-insensitive. If no match is found, the 'Default' port is triggered.

Inputs:
- Flow: Execution trigger.
- Value: The data item to evaluate.

Outputs:
- Default: Pulse triggered if no matching case is found.
- [Dynamic Cases]: Custom ports where the port name defines the matching value."""
    val_str = str(Value) if Value is not None else str(_node.properties.get('Value', ''))
    val_str = val_str.strip()
    val_lower = val_str.lower()
    chosen_port = 'Default'
    for port_name in self.output_schema.keys():
        if port_name in ['Default', 'Flow']:
            continue
        else:
            pass
        if val_str == port_name or val_lower == port_name.lower():
            chosen_port = port_name
            break
        else:
            pass
        try:
            if float(val_str) == float(port_name):
                chosen_port = port_name
                break
            else:
                pass
        except (ValueError, TypeError):
            pass
        finally:
            pass
    _node.logger.info(f"Switching on '{val_str}' -> {chosen_port}")
    _bridge.set(f'{_node_id}_ActivePorts', [chosen_port], _node.name)
    return True
