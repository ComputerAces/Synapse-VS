from axonpulse.core.super_node import SuperNode

from axonpulse.nodes.registry import NodeRegistry

from axonpulse.core.types import DataType

from typing import Any, List, Dict, Optional

from axonpulse.core.types import DataType, TypeCaster

from axonpulse.nodes.decorators import axon_node

@axon_node(category="Data", version="2.3.0", node_label="Char Node", outputs=['Char'])
def CharNode(Code: Any = 65, _bridge: Any = None, _node: Any = None, _node_id: str = None, **kwargs) -> Any:
    """Converts a numerical ASCII/Unicode code point into its character representation.
Supports the full Unicode character range (0 to 1,114,111).

Inputs:
- Flow: Trigger the conversion.
- Code: The integer code point (e.g., 65 for 'A').

Outputs:
- Flow: Triggered after conversion.
- Char: The resulting string character."""
    code_val = Code if Code is not None else kwargs.get('Code') or _node.properties.get('Code', 65)
    try:
        val = int(code_val)
        if 0 <= val <= 1114111:
            result = chr(val)
        else:
            _node.logger.error(f'Code {val} out of range.')
            result = ''
    except (ValueError, TypeError):
        _node.logger.error(f"Invalid code '{code_val}'.")
        result = ''
    finally:
        pass
    _bridge.set(f'{_node_id}_ActivePorts', ['Flow'], _node.name)
    return result
