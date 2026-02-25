from synapse.core.super_node import SuperNode
from synapse.nodes.registry import NodeRegistry
from synapse.core.types import DataType
import json

@NodeRegistry.register("Dict Create", "Data/Dictionaries")
class DictCreateNode(SuperNode):
    """
    Creates a dictionary object from an existing dictionary or an optional JSON-formatted string.
    
    Inputs:
    - Flow: Execution trigger.
    - JSON Data: A dictionary or JSON string to initialize the dictionary with.
    
    Outputs:
    - Flow: Triggered after the dictionary is created.
    - Dictionary: The resulting dictionary object.
    """
    version = "2.1.0"

    def __init__(self, node_id, name, bridge):
        super().__init__(node_id, name, bridge)
        self.properties["JSON Data"] = "{}"
        self.define_schema()
        self.register_handlers()

    def define_schema(self):
        self.input_schema = {
            "Flow": DataType.FLOW,
            "JSON Data": DataType.ANY
        }
        self.output_schema = {
            "Flow": DataType.FLOW,
            "Dictionary": DataType.DICT
        }

    def register_handlers(self):
        self.register_handler("Flow", self.create_dict)

    def create_dict(self, JSON_Data=None, **kwargs):
        # Fallback to optional input or property
        json_raw = JSON_Data if JSON_Data is not None else self.properties.get("JSON Data", "{}")
        
        try:
            if isinstance(json_raw, dict):
                data = json_raw
            else:
                final_raw = json_raw
                if isinstance(final_raw, dict):
                    data = final_raw
                else:
                    data = json.loads(str(final_raw)) if final_raw else {}
                    
            self.bridge.set(f"{self.node_id}_Dictionary", data, self.name)
            return True
        except Exception as e:
            self.logger.error(f"JSON Parse Error: {e}")
            return False

@NodeRegistry.register("Dict Get", "Data/Dictionaries")
class DictGetNode(SuperNode):
    """
    Retrieves a value from a dictionary using a specified key.
    
    Inputs:
    - Flow: Execution trigger.
    - Dictionary: The dictionary object to search.
    - Key: The key to look for in the dictionary.
    
    Outputs:
    - Flow: Triggered after the search is performed.
    - Value: The value associated with the key (if found).
    - Found: True if the key exists in the dictionary, otherwise False.
    """
    version = "2.1.0"

    def __init__(self, node_id, name, bridge):
        super().__init__(node_id, name, bridge)
        self.define_schema()
        self.register_handlers()

    def define_schema(self):
        self.input_schema = {
            "Flow": DataType.FLOW,
            "Dictionary": DataType.DICT,
            "Key": DataType.STRING
        }
        self.output_schema = {
            "Flow": DataType.FLOW,
            "Value": DataType.ANY,
            "Found": DataType.BOOLEAN
        }

    def register_handlers(self):
        self.register_handler("Flow", self.get_value)

    def get_value(self, Dictionary=None, Key=None, **kwargs):
        # Fallback
        d = Dictionary if Dictionary is not None else self.properties.get("Dictionary", {})
        k = Key if Key is not None else self.properties.get("Key", "")

        if isinstance(d, dict) and k in d:
            self.bridge.set(f"{self.node_id}_Value", d[k], self.name)
            self.bridge.set(f"{self.node_id}_Found", True, self.name)
        else:
            self.bridge.set(f"{self.node_id}_Found", False, self.name)
        return True

@NodeRegistry.register("Dict Set", "Data/Dictionaries")
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
    version = "2.1.0"

    def __init__(self, node_id, name, bridge):
        super().__init__(node_id, name, bridge)
        self.define_schema()
        self.register_handlers()

    def define_schema(self):
        self.input_schema = {
            "Flow": DataType.FLOW,
            "Dictionary": DataType.DICT,
            "Key": DataType.STRING,
            "Value": DataType.ANY
        }
        self.output_schema = {
            "Flow": DataType.FLOW,
            "Output Dict": DataType.DICT
        }

    def register_handlers(self):
        self.register_handler("Flow", self.set_value)

    def set_value(self, Dictionary=None, Key=None, Value=None, **kwargs):
        d = Dictionary if Dictionary is not None else self.properties.get("Dictionary", {})
        k = Key if Key is not None else self.properties.get("Key", "")
        v = Value if Value is not None else self.properties.get("Value")

        if not isinstance(d, dict):
            d = {}
            
        if k:
            # Simple check for complex path
            if "." in k or "[" in k:
                self._set_nested_value(d, k, v)
            else:
                d[k] = v
            
        self.bridge.set(f"{self.node_id}_Output Dict", d, self.name)
        return True

    def _set_nested_value(self, obj, path, value):
        import re
        tokens = re.findall(r'[^.\[\]]+|\[[^\]]+\]', path)
        current = obj
        
        # Parse tokens
        token_info = []
        for token in tokens:
            is_bracketed = False
            key = token
            if token.startswith('[') and token.endswith(']'):
                is_bracketed = True
                key = token[1:-1]
                if (key.startswith('"') and key.endswith('"')) or \
                   (key.startswith("'") and key.endswith("'")):
                    key = key[1:-1]
            token_info.append({"key": key, "bracketed": is_bracketed, "digit": key.isdigit()})

        # Traverse
        for i in range(len(token_info) - 1):
            info = token_info[i]
            next_info = token_info[i+1]
            key = info["key"]
            
            if info["digit"]:
                # List access
                idx = int(key)
                if not isinstance(current, list): break 
                # Expand list if needed
                while len(current) <= idx: current.append({})
                
                # Check target container type
                if not isinstance(current[idx], (dict, list)):
                    # Overwrite if not container
                    current[idx] = [] if (next_info["bracketed"] or next_info["digit"]) else {}
                current = current[idx]
            else:
                # Dict access
                if isinstance(current, list):
                    # If current is list but key is string, try last item? or fail?
                    # Original logic implicitly handled some list traversal quirks or expected Dict.
                    # Preserving original 'autovivification' style logic:
                    if not current or not isinstance(current[-1], dict): current.append({})
                    current = current[-1]
                
                if key not in current:
                    current[key] = [] if (next_info["bracketed"] or next_info["digit"]) else {}
                current = current[key]
        
        # Set final value
        last_info = token_info[-1]
        last_key = last_info["key"]
        if last_info["digit"]:
            idx = int(last_key)
            if isinstance(current, list):
                while len(current) <= idx: current.append(None)
                current[idx] = value
        else:
            if isinstance(current, list): current.append({last_key: value})
            elif isinstance(current, dict): current[last_key] = value

@NodeRegistry.register("Dict Remove", "Data/Dictionaries")
class DictRemoveNode(SuperNode):
    """
    Removes a key and its associated value from a dictionary.
    
    Inputs:
    - Flow: Execution trigger.
    - Dictionary: The dictionary object to modify.
    - Key: The key to remove.
    
    Outputs:
    - Flow: Triggered after the key is removed.
    - Output Dict: The modified dictionary object.
    """
    version = "2.1.0"

    def __init__(self, node_id, name, bridge):
        super().__init__(node_id, name, bridge)
        self.define_schema()
        self.register_handlers()

    def define_schema(self):
        self.input_schema = {
            "Flow": DataType.FLOW,
            "Dictionary": DataType.DICT,
            "Key": DataType.STRING
        }
        self.output_schema = {
            "Flow": DataType.FLOW,
            "Output Dict": DataType.DICT
        }

    def register_handlers(self):
        self.register_handler("Flow", self.remove_key)

    def remove_key(self, Dictionary=None, Key=None, **kwargs):
        d = Dictionary if Dictionary is not None else self.properties.get("Dictionary", {})
        k = Key if Key is not None else self.properties.get("Key", "")

        if isinstance(d, dict) and k in d:
            del d[k]
        self.bridge.set(f"{self.node_id}_Output Dict", d, self.name)
        return True
