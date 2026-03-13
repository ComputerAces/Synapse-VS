from axonpulse.core.super_node import SuperNode

from axonpulse.nodes.registry import NodeRegistry

from axonpulse.core.types import DataType

import json

from typing import Any, List, Dict, Optional

from axonpulse.core.types import DataType, TypeCaster

from axonpulse.nodes.decorators import axon_node

@NodeRegistry.register('Dict Set', 'Data/Dictionaries')
class DictSetNode(SuperNode):
    """
    Sets or updates a value in a dictionary for a given key. Supports nested paths (e.g., 'user.profile.name').
    
    Inputs:
    - Flow: Execution trigger.
    - Dictionary: The dictionary object to modify.
    - Key: The key (or dot-notated path) to set.
    - Value: The value to assign to the key.
    
    Outputs:
    - Flow: Triggered after the value is set.
    - Output Dict: The modified dictionary object.
    """
    version = '2.1.0'

    def __init__(self, node_id, name, bridge):
        super().__init__(node_id, name, bridge)
        self.is_native = True
        self.define_schema()
        self.register_handlers()

    def define_schema(self):
        self.input_schema = {'Flow': DataType.FLOW, 'Dictionary': DataType.DICT, 'Key': DataType.STRING, 'Value': DataType.ANY}
        self.output_schema = {'Flow': DataType.FLOW, 'Output Dict': DataType.DICT}

    def register_handlers(self):
        self.register_handler('Flow', self.set_value)

    def set_value(self, Dictionary=None, Key=None, Value=None, **kwargs):
        d = Dictionary if Dictionary is not None else self.properties.get('Dictionary', {})
        k = Key if Key is not None else self.properties.get('Key', '')
        v = Value if Value is not None else self.properties.get('Value')
        if not isinstance(d, dict):
            d = {}
        if k:
            if '.' in k or '[' in k:
                self._set_nested_value(d, k, v)
            else:
                d[k] = v
        self.bridge.set(f'{self.node_id}_Output Dict', d, self.name)
        return True

    def _set_nested_value(self, obj, path, value):
        import re
        tokens = re.findall('[^.\\[\\]]+|\\[[^\\]]+\\]', path)
        current = obj
        token_info = []
        for token in tokens:
            is_bracketed = False
            key = token
            if token.startswith('[') and token.endswith(']'):
                is_bracketed = True
                key = token[1:-1]
                if key.startswith('"') and key.endswith('"') or (key.startswith("'") and key.endswith("'")):
                    key = key[1:-1]
            token_info.append({'key': key, 'bracketed': is_bracketed, 'digit': key.isdigit()})
        for i in range(len(token_info) - 1):
            info = token_info[i]
            next_info = token_info[i + 1]
            key = info['key']
            if info['digit']:
                idx = int(key)
                if not isinstance(current, list):
                    break
                while len(current) <= idx:
                    current.append({})
                if not isinstance(current[idx], (dict, list)):
                    current[idx] = [] if next_info['bracketed'] or next_info['digit'] else {}
                current = current[idx]
            else:
                if isinstance(current, list):
                    if not current or not isinstance(current[-1], dict):
                        current.append({})
                    current = current[-1]
                if key not in current:
                    current[key] = [] if next_info['bracketed'] or next_info['digit'] else {}
                current = current[key]
        last_info = token_info[-1]
        last_key = last_info['key']
        if last_info['digit']:
            idx = int(last_key)
            if isinstance(current, list):
                while len(current) <= idx:
                    current.append(None)
                current[idx] = value
        elif isinstance(current, list):
            current.append({last_key: value})
        elif isinstance(current, dict):
            current[last_key] = value

@axon_node(category="Data/Dictionaries", version="2.3.0", node_label="Dict Create", outputs=['Dictionary'])
def DictCreateNode(JSON_Data: Any = '{}', _bridge: Any = None, _node: Any = None, _node_id: str = None, **kwargs) -> Any:
    """Creates a dictionary object from an existing dictionary or an optional JSON-formatted string.

Inputs:
- Flow: Execution trigger.
- JSON Data: A dictionary or JSON string to initialize the dictionary with.

Outputs:
- Flow: Triggered after the dictionary is created.
- Dictionary: The resulting dictionary object."""
    json_raw = JSON_Data if JSON_Data is not None else _node.properties.get('JSON Data', '{}')
    try:
        if isinstance(json_raw, dict):
            data = json_raw
        else:
            final_raw = json_raw
            if isinstance(final_raw, dict):
                data = final_raw
            else:
                data = json.loads(str(final_raw)) if final_raw else {}
    except Exception as e:
        _node.logger.error(f'JSON Parse Error: {e}')
        return False
    finally:
        pass
    return data


@axon_node(category="Data/Dictionaries", version="2.3.0", node_label="Dict Get", outputs=['Value', 'Found'])
def DictGetNode(Dictionary: dict, Key: str, _bridge: Any = None, _node: Any = None, _node_id: str = None, **kwargs) -> Any:
    """Retrieves a value from a dictionary using a specified key.

Inputs:
- Flow: Execution trigger.
- Dictionary: The dictionary object to search.
- Key: The key to look for in the dictionary.

Outputs:
- Flow: Triggered after the search is performed.
- Value: The value associated with the key (if found).
- Found: True if the key exists in the dictionary, otherwise False."""
    d = Dictionary if Dictionary is not None else _node.properties.get('Dictionary', {})
    k = Key if Key is not None else _node.properties.get('Key', '')
    if isinstance(d, dict) and k in d:
        pass
    else:
        pass
    return {'Value': d[k], 'Found': True, 'Found': False}


@axon_node(category="Data/Dictionaries", version="2.3.0", node_label="Dict Remove", outputs=['Output Dict'])
def DictRemoveNode(Dictionary: dict, Key: str, _bridge: Any = None, _node: Any = None, _node_id: str = None, **kwargs) -> Any:
    """Removes a key and its associated value from a dictionary.

Inputs:
- Flow: Execution trigger.
- Dictionary: The dictionary object to modify.
- Key: The key to remove.

Outputs:
- Flow: Triggered after the key is removed.
- Output Dict: The modified dictionary object."""
    d = Dictionary if Dictionary is not None else _node.properties.get('Dictionary', {})
    k = Key if Key is not None else _node.properties.get('Key', '')
    if isinstance(d, dict) and k in d:
        del d[k]
    else:
        pass
    return d
