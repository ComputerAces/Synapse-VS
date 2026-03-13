from axonpulse.core.super_node import SuperNode

from axonpulse.nodes.registry import NodeRegistry

from axonpulse.core.types import DataType, TypeCaster

import struct

from typing import Any, List, Dict, Optional

from axonpulse.nodes.decorators import axon_node

@axon_node(category="Media/Color", version="2.3.0", node_label="Color Constant")
def ColorConstantNode(Color: Any = '#800080FF', _bridge: Any = None, _node: Any = None, _node_id: str = None, **kwargs) -> Any:
    """Outputs a fixed color value.
Supports RGBA hex strings (e.g., "#800080FF") and manages the color data type.

Inputs:
- Flow: Trigger the output.
- Color: Optional input to override the constant value.

Outputs:
- Flow: Triggered after output.
- Result: The specified color in RGBA hex format."""
    col = Color if Color is not None else _node.properties.get('Color', '#800080FF')
    if isinstance(col, list):
        if len(col) >= 3:
            (r, g, b) = (col[0], col[1], col[2])
            a = col[3] if len(col) > 3 else 255
            col = '#{:02x}{:02x}{:02x}{:02x}'.format(r, g, b, a)
        else:
            col = '#800080FF'
    else:
        pass
    _node.logger.info(f'Outputting color: {col}')
    _bridge.set(f'{_node_id}_ActivePorts', ['Flow'], _node.name)
    return col


@axon_node(category="Media/Color", version="2.3.0", node_label="Split Color", outputs=['R', 'G', 'B', 'A'])
def ColorSplitNode(Color: Any = [128, 0, 128, 255], _bridge: Any = None, _node: Any = None, _node_id: str = None, **kwargs) -> Any:
    """Deconstructs a color value into its individual Red, Green, Blue, and Alpha components.
Supports both RGBA hex strings and list formats.

Inputs:
- Flow: Trigger the split.
- Color: The color value to split.

Outputs:
- Flow: Triggered after split.
- R, G, B, A: The numerical components (0-255)."""
    color = Color if Color is not None else kwargs.get('Color') or _node.properties.get('Color', '#800080FF')
    (r, g, b, a) = (0, 0, 0, 255)
    if isinstance(color, str) and color.startswith('#'):
        try:
            hex_val = color.lstrip('#')
            if len(hex_val) == 6:
                (r, g, b) = struct.unpack('BBB', bytes.fromhex(hex_val))
                a = 255
            elif len(hex_val) == 8:
                (r, g, b, a) = struct.unpack('BBBB', bytes.fromhex(hex_val))
            else:
                pass
        except:
            pass
        finally:
            pass
    elif isinstance(color, list) and len(color) >= 3:
        r = color[0]
        g = color[1]
        b = color[2]
        a = color[3] if len(color) > 3 else 255
    else:
        pass
    _bridge.set(f'{_node_id}_ActivePorts', ['Flow'], _node.name)
    return {'R': r, 'G': g, 'B': b, 'A': a}


@axon_node(category="Media/Color", version="2.3.0", node_label="Merge Color", outputs=['Color'])
def ColorMergeNode(R: float = 0, G: float = 0, B: float = 0, A: float = 255, _bridge: Any = None, _node: Any = None, _node_id: str = None, **kwargs) -> Any:
    """Combines individual Red, Green, Blue, and Alpha components into a single color value.
Resulting output is an RGBA hex string.

Inputs:
- Flow: Trigger the merge.
- R, G, B, A: Numerical components (0-255).

Outputs:
- Flow: Triggered after merge.
- Color: The combined color in RGBA hex format."""
    r_val = R if R is not None else kwargs.get('R') or _node.properties.get('R', 0)
    g_val = G if G is not None else kwargs.get('G') or _node.properties.get('G', 0)
    b_val = B if B is not None else kwargs.get('B') or _node.properties.get('B', 0)
    a_val = A if A is not None else kwargs.get('A') or _node.properties.get('A', 255)
    try:
        r = max(0, min(255, int(TypeCaster.to_number(r_val))))
        g = max(0, min(255, int(TypeCaster.to_number(g_val))))
        b = max(0, min(255, int(TypeCaster.to_number(b_val))))
        a = max(0, min(255, int(TypeCaster.to_number(a_val))))
        hex_color = '#{:02x}{:02x}{:02x}{:02x}'.format(r, g, b, a)
    except Exception as e:
        _node.logger.error(f'Error merging color: {e}')
    finally:
        pass
    _bridge.set(f'{_node_id}_ActivePorts', ['Flow'], _node.name)
    return hex_color
