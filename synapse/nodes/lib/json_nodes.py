from synapse.core.super_node import SuperNode
from synapse.nodes.registry import NodeRegistry
from synapse.core.types import DataType
import json
import re

@NodeRegistry.register("JSON Parse", "Data/JSON")
class JSONParseNode(SuperNode):
    """
    Parses a JSON-formatted string into a structured Data object (Dictionary or List).
    
    Inputs:
    - Flow: Execution trigger.
    - Text: The JSON string to parse.
    
    Outputs:
    - Flow: Triggered after the parsing attempt.
    - Data: The resulting dictionary or list.
    - Valid: True if the string was successfully parsed as JSON, otherwise False.
    """
    version = "2.1.0"

    def __init__(self, node_id, name, bridge):
        super().__init__(node_id, name, bridge)
        self.is_native = True
        self.define_schema()
        self.register_handlers()

    def define_schema(self):
        self.input_schema = {
            "Flow": DataType.FLOW,
            "Text": DataType.STRING
        }
        self.output_schema = {
            "Flow": DataType.FLOW,
            "Data": DataType.ANY,
            "Valid": DataType.BOOLEAN
        }

    def register_handlers(self):
        self.register_handler("Flow", self.parse_json)

    def parse_json(self, Text=None, **kwargs):
        # Fallback to properties
        data = Text if Text is not None else self.properties.get("Text", "")
        
        # If it's already a dict/list, it's technically "valid" pre-parsed data
        if isinstance(data, (dict, list)):
            self.bridge.set(f"{self.node_id}_Data", data, self.name)
            self.bridge.set(f"{self.node_id}_Valid", True, self.name)
            return True

        txt = str(data or "").strip()
        if not txt:
            self.bridge.set(f"{self.node_id}_Data", None, self.name)
            self.bridge.set(f"{self.node_id}_Valid", False, self.name)
            return True

        try:
            # Standard JSON parse
            parsed = json.loads(txt)
            self.bridge.set(f"{self.node_id}_Data", parsed, self.name)
            self.bridge.set(f"{self.node_id}_Valid", True, self.name)
        except json.JSONDecodeError:
            # Fallback for Python-style single quotes
            try:
                import ast
                parsed = ast.literal_eval(txt)
                if isinstance(parsed, (dict, list)):
                    self.bridge.set(f"{self.node_id}_Data", parsed, self.name)
                    self.bridge.set(f"{self.node_id}_Valid", True, self.name)
                else:
                    raise ValueError("Not a dictionary or list")
            except Exception:
                self.bridge.set(f"{self.node_id}_Data", None, self.name)
                self.bridge.set(f"{self.node_id}_Valid", False, self.name)
        
        return True

@NodeRegistry.register("JSON Stringify", "Data/JSON")
class JSONStringifyNode(SuperNode):
    """
    Converts a structured Data object (Dictionary or List) into a JSON-formatted string.
    
    Inputs:
    - Flow: Execution trigger.
    - Data: The object (Dictionary or List) to serialize.
    
    Outputs:
    - Flow: Triggered if serialization is successful.
    - Text: The resulting JSON string.
    """
    version = "2.1.0"

    def __init__(self, node_id, name, bridge):
        super().__init__(node_id, name, bridge)
        self.is_native = True
        self.properties["Indent"] = 2
        self.define_schema()
        self.register_handlers()

    def define_schema(self):
        self.input_schema = {
            "Flow": DataType.FLOW,
            "Data": DataType.ANY
        }
        self.output_schema = {
            "Flow": DataType.FLOW,
            "Text": DataType.STRING
        }

    def register_handlers(self):
        self.register_handler("Flow", self.stringify_json)

    def stringify_json(self, Data=None, **kwargs):
        # Fallback to properties
        data_obj = Data if Data is not None else self.properties.get("Data")
        indent = int(self.properties.get("Indent", self.properties.get("Indent", 2)))
        try:
            txt = json.dumps(data_obj, indent=indent, default=str)
        except Exception as e:
            self.logger.warning(f"Stringify Error: {e}")
            txt = str(data_obj)
            
        self.bridge.set(f"{self.node_id}_Text", txt, self.name)
        return True

@NodeRegistry.register("JSON Value", "Data/JSON")
class JSONValueNode(SuperNode):
    """
    Extracts a value from a JSON object or string using a path (e.g., 'user.name' or 'items[0].id').
    
    Inputs:
    - Flow: Execution trigger.
    - Data: The JSON object or string to search.
    - Path: The dot-notated or bracketed path to the desired value.
    
    Outputs:
    - Flow: Triggered after the extraction attempt.
    - Value: The extracted value (if found).
    - Found: True if the path was successfully resolved, otherwise False.
    """
    version = "2.1.0"

    def __init__(self, node_id, name, bridge):
        super().__init__(node_id, name, bridge)
        self.is_native = True
        self.properties["Path"] = ""
        self.define_schema()
        self.register_handlers()

    def define_schema(self):
        self.input_schema = {
            "Flow": DataType.FLOW,
            "Data": DataType.ANY,
            "Path": DataType.STRING
        }
        self.output_schema = {
            "Flow": DataType.FLOW,
            "Value": DataType.ANY,
            "True Path": DataType.ANY,
            "Found": DataType.BOOLEAN
        }

    def register_handlers(self):
        self.register_handler("Flow", self.extract_value)

    def extract_value(self, Data=None, Path=None, **kwargs):
        # Fallback to properties
        data_obj = Data if Data is not None else self.properties.get("Data")
        path_str = Path if Path is not None else self.properties.get("Path", self.properties.get("Path", ""))

        obj = data_obj
        if isinstance(obj, str):
            try:
                obj = json.loads(obj)
            except json.JSONDecodeError:
                self.bridge.set(f"{self.node_id}_Found", False, self.name)
                return True

        if not path_str:
            self.bridge.set(f"{self.node_id}_Value", obj, self.name)
            self.bridge.set(f"{self.node_id}_True Path", "", self.name)
            self.bridge.set(f"{self.node_id}_Found", True, self.name)
            return True

        result, tpath, found = self._resolve_path(obj, path_str)
        self.bridge.set(f"{self.node_id}_Value", result, self.name)
        self.bridge.set(f"{self.node_id}_True Path", tpath, self.name)
        self.bridge.set(f"{self.node_id}_Found", found, self.name)
        return True

    def _resolve_path(self, obj, path, current_path=""):
        tokens = re.findall(r'[^.\[\]]+|\[[^\]]*\]', path)
        current = obj
        actual_path = current_path
        
        def append_path(base, suffix, is_bracket=False):
            if is_bracket:
                # Array index or pure key notation
                if isinstance(suffix, int) or (isinstance(suffix, str) and suffix.isdigit()):
                    return f"{base}[{suffix}]"
                return f"{base}.{suffix}" if base else str(suffix)
            if not base: return str(suffix)
            return f"{base}.{suffix}"

        try:
            i = 0
            while i < len(tokens):
                token = tokens[i]
                if current is None: return None, "", False
                
                # [NEW] Lookahead for literal bracket keys
                # If current token + next bracket token matches a literal string key in the dictionary
                # (e.g., token="div", tokens[i+1]="[2]", and dict has key "div[2]")
                if isinstance(current, dict) and i + 1 < len(tokens):
                    next_token = tokens[i+1]
                    if next_token.startswith('[') and next_token.endswith(']'):
                        literal_key = f"{token}{next_token}"
                        if literal_key in current:
                            current = current[literal_key]
                            actual_path = append_path(actual_path, literal_key, False)
                            i += 2
                            continue
                            
                # Check for bracketed token: [0], [*], or ["key"]
                if token.startswith('[') and token.endswith(']'):
                    inner = token[1:-1]
                    
                    # Handle [*]
                    if inner == '*':
                        if isinstance(current, list):
                            remaining_tokens = tokens[tokens.index(token)+1:]
                            if remaining_tokens:
                                remain_str = ""
                                for t in remaining_tokens:
                                    if t.startswith('['): remain_str += t
                                    else: remain_str += ("." + t) if remain_str else t
                                    
                                res_list = []
                                path_list = []
                                for i, item in enumerate(current):
                                    next_base = append_path(actual_path, i, True)
                                    val, p, ok = self._resolve_path(item, remain_str, next_base)
                                    res_list.append(val)
                                    path_list.append(p)
                                return res_list, path_list, True
                            else:
                                path_list = [append_path(actual_path, i, True) for i in range(len(current))]
                                return current, path_list, True
                        return None, "", False
                    
                    # Handle ["key"] or ['key']
                    if (inner.startswith('"') and inner.endswith('"')) or \
                       (inner.startswith("'") and inner.endswith("'")):
                        key = inner[1:-1]
                        # Implicit indexing: if current is a list but we have a key, try current[0][key]
                        if isinstance(current, list) and current:
                            if isinstance(current[0], dict) and key in current[0]:
                                current = current[0][key]
                                actual_path = append_path(append_path(actual_path, 0, True), key, False)
                                continue
                        
                        if isinstance(current, dict) and key in current:
                            current = current[key]
                            actual_path = append_path(actual_path, inner, True)
                        else: return None, "", False
                        continue
                        
                    # Handle [0] (digit index)
                    if inner.isdigit():
                        idx = int(inner)
                        if isinstance(current, list) and idx < len(current):
                            current = current[idx]
                            actual_path = append_path(actual_path, idx, True)
                        else: return None, "", False
                        continue
                    
                    # If it's just [key] without quotes, treat as dictionary key
                    key = inner
                    if isinstance(current, dict) and key in current:
                        current = current[key]
                        actual_path = append_path(actual_path, inner, True)
                    else: return None, "", False
                    i += 1
                    continue

                # Standard Dot/Key token
                if isinstance(current, dict):
                    if token in current: 
                        current = current[token]
                        actual_path = append_path(actual_path, token, False)
                    else: return None, "", False
                elif isinstance(current, list):
                    # Implicitly index first element if token is a key name
                    try:
                        idx = int(token)
                        if idx < len(current): 
                            current = current[idx]
                            actual_path = append_path(actual_path, idx, True)
                        else: return None, "", False
                    except ValueError:
                        # Not an integer, check if first element has this key
                        if current and isinstance(current[0], dict) and token in current[0]:
                            current = current[0][token]
                            actual_path = append_path(append_path(actual_path, 0, True), token, False)
                        else: return None, "", False
                else: return None, "", False
                
                i += 1
                
            return current, actual_path, True
        except Exception:
            return None, "", False

@NodeRegistry.register("JSON Query", "Data/JSON")
class JSONQueryNode(SuperNode):
    """
    Filters a list of objects based on a simple query string (e.g., 'age > 20 AND status == "active"').
    
    Inputs:
    - Flow: Execution trigger.
    - Data: The list of objects (dictionaries) to query.
    - Query: The query string specifying the filtering conditions.
    
    Outputs:
    - Flow: Triggered after the query is executed.
    - Results: The list of items that match the query.
    - Count: The number of items found.
    """
    version = "2.1.0"

    def __init__(self, node_id, name, bridge):
        super().__init__(node_id, name, bridge)
        self.is_native = True
        self.properties["Query"] = ""
        self.define_schema()
        self.register_handlers()

    def define_schema(self):
        self.input_schema = {
            "Flow": DataType.FLOW,
            "Data": DataType.LIST,
            "Query": DataType.STRING
        }
        self.output_schema = {
            "Flow": DataType.FLOW,
            "Results": DataType.LIST,
            "Count": DataType.NUMBER
        }

    def register_handlers(self):
        self.register_handler("Flow", self.query_data)

    def query_data(self, Data=None, Query=None, **kwargs):
        # Fallback to properties
        data_obj = Data if Data is not None else self.properties.get("Data")
        query_str = Query if Query is not None else self.properties.get("Query", self.properties.get("Query", ""))
        
        if isinstance(data_obj, str):
            try: data_obj = json.loads(data_obj)
            except Exception as e:
                self.logger.warning(f"Query Parse Error: {e}")
                return False
        
        if not isinstance(data_obj, list): 
            # If explicit empty logic logic or fail
            return True # Fail gracefully
            
        if not query_str or not query_str.strip():
            self.bridge.set(f"{self.node_id}_Results", data_obj, self.name)
            self.bridge.set(f"{self.node_id}_Count", len(data_obj), self.name)
            return True

        conditions = [c.strip() for c in re.split(r'\bAND\b', query_str, flags=re.IGNORECASE)]
        results = [item for item in data_obj if isinstance(item, dict) and all(self._eval_condition(item, c) for c in conditions)]
        
        self.bridge.set(f"{self.node_id}_Results", results, self.name)
        self.bridge.set(f"{self.node_id}_Count", len(results), self.name)
        return True

    def _eval_condition(self, item, condition):
        pattern = r"^(\w+(?:\.\w+)*)\s*(==|!=|>=|<=|>|<|contains)\s*(.+)$"
        m = re.match(pattern, condition.strip())
        if not m: return False
        field_path, op, val_str = m.group(1), m.group(2), m.group(3).strip()
        field_val = item
        for key in field_path.split('.'):
            if isinstance(field_val, dict) and key in field_val: field_val = field_val[key]
            else: return False
        comp_val = self._parse_value(val_str)
        try:
            if op == "==": return field_val == comp_val
            if op == "!=": return field_val != comp_val
            if op == ">": return float(field_val) > float(comp_val)
            if op == "<": return float(field_val) < float(comp_val)
            if op == ">=": return float(field_val) >= float(comp_val)
            if op == "<=": return float(field_val) <= float(comp_val)
            if op == "contains":
                if isinstance(field_val, str): return str(comp_val) in field_val
                if isinstance(field_val, list): return comp_val in field_val
            return False
        except: return False

    def _parse_value(self, val_str):
        if (val_str.startswith("'") and val_str.endswith("'")) or (val_str.startswith('"') and val_str.endswith('"')):
            return val_str[1:-1]
        try:
            if '.' in val_str: return float(val_str)
            return int(val_str)
        except: pass
        if val_str.lower() == 'true': return True
        if val_str.lower() == 'false': return False
        if val_str.lower() in ('null', 'none'): return None
        return val_str

@NodeRegistry.register("JSON Keys", "Data/JSON")
class JSONKeysNode(SuperNode):
    """
    Retrieves the keys from a JSON object or the indices from a JSON list at a specified path.
    
    Inputs:
    - Flow: Execution trigger.
    - Data: The JSON object or list.
    - Path: Optional path to a nested object or list within the Data.
    
    Outputs:
    - Flow: Triggered after the keys are retrieved.
    - Keys: A list containing the keys or indices.
    - Length: The number of keys or indices found.
    """
    version = "2.1.0"

    def __init__(self, node_id, name, bridge):
        super().__init__(node_id, name, bridge)
        self.is_native = True
        self.properties["Path"] = ""
        self.define_schema()
        self.register_handlers()

    def define_schema(self):
        self.input_schema = {
            "Flow": DataType.FLOW,
            "Data": DataType.ANY,
            "Path": DataType.STRING
        }
        self.output_schema = {
            "Flow": DataType.FLOW,
            "Keys": DataType.LIST,
            "Length": DataType.NUMBER
        }

    def register_handlers(self):
        self.register_handler("Flow", self.get_keys)

    def get_keys(self, Data=None, Path=None, **kwargs):
        # Fallback to properties
        data_obj = Data if Data is not None else self.properties.get("Data")
        path_str = Path if Path is not None else self.properties.get("Path", self.properties.get("Path", ""))

        if path_str is not None:
            clean_str = str(path_str).strip()
            if not clean_str or clean_str == "/":
                path_str = ""

        obj = data_obj
        if isinstance(obj, str):
            try: obj = json.loads(obj)
            except Exception as e: 
                self.logger.warning(f"Keys Parse Error: {e}")
                self.bridge.set(f"{self.node_id}_Keys", [], self.name)
                self.bridge.set(f"{self.node_id}_Length", 0, self.name)
                return True

        # Resolve path if provided
        if path_str:
            # Avoid full Node initialization to prevent pickling errors on bridge/logger
            temp_node = JSONValueNode.__new__(JSONValueNode)
            obj, tpath, found = temp_node._resolve_path(obj, path_str)
            if not found:
                self.bridge.set(f"{self.node_id}_Keys", [], self.name)
                self.bridge.set(f"{self.node_id}_Length", 0, self.name)
                return True

        if isinstance(obj, dict): keys = list(obj.keys())
        elif isinstance(obj, list): keys = list(range(len(obj)))
        else: keys = []
        
        self.bridge.set(f"{self.node_id}_Keys", keys, self.name)
        self.bridge.set(f"{self.node_id}_Length", len(keys), self.name)
        return True


@NodeRegistry.register("JSON Search", "Data/JSON")
class JSONSearchNode(SuperNode):
    """
    Recursively searches a JSON object (dictionary/list) for a specific string.
    
    Inputs:
    - Flow: Execution trigger.
    - Data: The JSON object (dictionary or list) to search.
    - Search: The string to look for.
    - Match Case: If true, the search is case-sensitive.
    - Exact Match: If true, the search string must match the value entirely.
    
    Outputs:
    - Flow: Triggered after the search finishes.
    - Paths: A list of paths (strings) where the matching values were found.
    - Values: A list of the actual values that matched.
    """
    version = "2.1.0"

    def __init__(self, node_id, name, bridge):
        super().__init__(node_id, name, bridge)
        self.is_native = True
        self.properties["Search"] = ""
        self.properties["Match Case"] = False
        self.properties["Exact Match"] = False
        self.define_schema()
        self.register_handlers()

    def define_schema(self):
        self.input_schema = {
            "Flow": DataType.FLOW,
            "Data": DataType.ANY,
            "Search": DataType.STRING,
            "Match Case": DataType.BOOLEAN,
            "Exact Match": DataType.BOOLEAN
        }
        self.output_schema = {
            "Flow": DataType.FLOW,
            "Paths": DataType.LIST,
            "Values": DataType.LIST
        }

    def register_handlers(self):
        self.register_handler("Flow", self.search_json)

    def search_json(self, Data=None, Search=None, **kwargs):
        # Fallbacks
        data_obj = Data if Data is not None else self.properties.get("Data")
        search_query = Search if Search is not None else self.properties.get("Search", "")
        match_case = kwargs.get("Match Case", self.properties.get("Match Case", False))
        exact_match = kwargs.get("Exact Match", self.properties.get("Exact Match", False))

        if isinstance(data_obj, str):
            try:
                data_obj = json.loads(data_obj)
            except:
                pass # Try to search it as a generic string if it fails to parse

        if not search_query:
            self.bridge.set(f"{self.node_id}_Paths", [], self.name)
            self.bridge.set(f"{self.node_id}_Values", [], self.name)
            return True

        if not match_case:
            search_query = str(search_query).lower()
        else:
            search_query = str(search_query)

        paths = []
        values = []

        def match_value(val):
            val_str = str(val)
            if not match_case:
                val_str = val_str.lower()
            
            if exact_match:
                return val_str == search_query
            else:
                return search_query in val_str

        def recurse(current, current_path=""):
            if isinstance(current, dict):
                for k, v in current.items():
                    # Strictly enforce dotted paths without bracket enclosures
                    next_path = f"{current_path}.{k}" if current_path else str(k)
                        
                    # Check match
                    matched = False
                    if match_value(k):
                        matched = True
                    elif not isinstance(v, (dict, list)) and match_value(v):
                        matched = True
                        
                    if matched:
                         paths.append(next_path)
                         values.append(v)
                    
                    if isinstance(v, (dict, list)):
                        recurse(v, next_path)
                        
            elif isinstance(current, list):
                for i, v in enumerate(current):
                    next_path = f"{current_path}[{i}]"
                    
                    matched = False
                    if not isinstance(v, (dict, list)) and match_value(v):
                        matched = True
                        
                    if matched:
                        paths.append(next_path)
                        values.append(v)
                        
                    if isinstance(v, (dict, list)):
                        recurse(v, next_path)

        # Start recursion
        if isinstance(data_obj, (dict, list)):
            recurse(data_obj)
        else:
            if match_value(data_obj):
                paths.append("")
                values.append(data_obj)

        self.bridge.set(f"{self.node_id}_Paths", paths, self.name)
        self.bridge.set(f"{self.node_id}_Values", values, self.name)
        return True
