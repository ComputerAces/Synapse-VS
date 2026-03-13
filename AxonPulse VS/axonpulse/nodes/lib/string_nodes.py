from axonpulse.core.super_node import SuperNode

from axonpulse.nodes.registry import NodeRegistry

from axonpulse.core.types import DataType

from typing import Any, List, Dict, Optional

from axonpulse.core.types import DataType, TypeCaster

from axonpulse.nodes.decorators import axon_node

@axon_node(category="Data/Strings", version="2.3.0", node_label="String Join")
def StringJoinNode(List: list, Separator: str = ' ', _bridge: Any = None, _node: Any = None, _node_id: str = None, **kwargs) -> Any:
    """Concatenates a list of strings into a single string using a specified separator.

Inputs:
- Flow: Execution trigger.
- List: The list of string items to join.
- Separator: The string to insert between items.

Outputs:
- Flow: Triggered after the join is complete.
- Result: The concatenated string."""
    items = List if List is not None else _node.properties.get('List', [])
    sep = Separator if Separator is not None else _node.properties.get('Separator', ' ')
    if not isinstance(items, list):
        items = [str(items)]
    else:
        pass
    result = str(sep).join((str(i) for i in items))
    return result


@axon_node(category="Data/Strings", version="2.3.0", node_label="Substring")
def StringPartNode(String: str, Start: float = 0, End: float = '', _bridge: Any = None, _node: Any = None, _node_id: str = None, **kwargs) -> Any:
    """Extracts a portion of a string based on start and end indices.

Inputs:
- Flow: Execution trigger.
- String: The source string.
- Start: The starting index (inclusive).
- End: The ending index (exclusive). If empty, extracts to the end.

Outputs:
- Flow: Triggered after the extraction.
- Result: The extracted portion of the string."""
    s_val = String if String is not None else _node.properties.get('String', '')
    start_val = Start if Start is not None else _node.properties.get('Start', 0)
    end_val = End if End is not None else _node.properties.get('End', '')
    try:
        start_idx = int(start_val)
        if end_val == '' or end_val is None:
            result = str(s_val)[start_idx:]
        else:
            end_idx = int(end_val)
            result = str(s_val)[start_idx:end_idx]
    except Exception as e:
        _node.logger.warning(f'Substring Error: {e}')
        result = str(s_val)
    finally:
        pass
    return result


@axon_node(category="Data/Strings", version="2.3.0", node_label="String Length")
def StringLengthNode(String: str, _bridge: Any = None, _node: Any = None, _node_id: str = None, **kwargs) -> Any:
    """Calculates the number of characters in a string.

Inputs:
- Flow: Execution trigger.
- String: The string to measure.

Outputs:
- Flow: Triggered after the calculation.
- Result: The character count."""
    s_val = String if String is not None else _node.properties.get('String', '')
    result = len(str(s_val))
    return result


@axon_node(category="Data/Strings", version="2.3.0", node_label="String Find", outputs=['Position'])
def StringFindNode(String: str, Substring: str, Start_Index: float = 0, _bridge: Any = None, _node: Any = None, _node_id: str = None, **kwargs) -> Any:
    """Finds the first occurrence of a substring within a larger string.

Inputs:
- Flow: Execution trigger.
- String: The main string to search within.
- Substring: The text to find.
- Start Index: The position to start searching from (default: 0).

Outputs:
- Flow: Triggered after the search is complete.
- Position: The index of the substring (-1 if not found)."""
    s_val = String if String is not None else _node.properties.get('String', '')
    sub_val = Substring if Substring is not None else _node.properties.get('Substring', '')
    start_idx = kwargs.get('Start Index')
    if start_idx is None:
        start_idx = _node.properties.get('Start Index', 0)
    else:
        pass
    s_str = str(s_val) if s_val is not None else ''
    sub_str = str(sub_val) if sub_val is not None else ''
    try:
        start_pos = int(start_idx)
    except (ValueError, TypeError):
        start_pos = 0
    finally:
        pass
    result = s_str.find(sub_str, start_pos)
    return result


@axon_node(category="Data/Strings", version="2.3.0", node_label="String Combine")
def StringCombineNode(_bridge: Any = None, _node: Any = None, _node_id: str = None, **kwargs) -> Any:
    """Combines multiple dynamically added input variables into a single concatenated string.

Inputs:
- Flow: Execution trigger.
- [Dynamic Inputs]: Add as many string inputs as you need via the node's context menu.

Outputs:
- Flow: Triggered after concatenation.
- Result: The combined string."""
    dynamic_inputs = _node.properties.get('Additional Inputs', [])
    if isinstance(dynamic_inputs, str):
        import ast
        try:
            dynamic_inputs = ast.literal_eval(dynamic_inputs)
        except Exception:
            dynamic_inputs = []
        finally:
            pass
    else:
        pass
    if not isinstance(dynamic_inputs, list):
        dynamic_inputs = []
    else:
        pass
    combined_string = ''
    if dynamic_inputs:
        for pin_name in dynamic_inputs:
            val = kwargs.get(pin_name)
            if val is None:
                val = _node.properties.get(pin_name, '')
            else:
                pass
            if isinstance(val, list) and len(val) == 2 and isinstance(val[0], str):
                if val[0].lower() in ['str', 'string', 'int', 'integer', 'float', 'number', 'bool', 'boolean', 'any']:
                    val = val[1]
                else:
                    pass
            else:
                pass
            if val is not None and val != '':
                combined_string += str(val)
            else:
                pass
    else:
        for (k, val) in kwargs.items():
            if k == 'Flow':
                continue
            else:
                pass
            if val is not None and val != '':
                combined_string += str(val)
            else:
                pass
    return combined_string
