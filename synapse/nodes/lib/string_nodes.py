from synapse.core.super_node import SuperNode
from synapse.nodes.registry import NodeRegistry
from synapse.core.types import DataType

@NodeRegistry.register("String Join", "Data/Strings")
class StringJoinNode(SuperNode):
    """
    Concatenates a list of strings into a single string using a specified separator.
    
    Inputs:
    - Flow: Execution trigger.
    - List: The list of string items to join.
    - Separator: The string to insert between items.
    
    Outputs:
    - Flow: Triggered after the join is complete.
    - Result: The concatenated string.
    """
    version = "2.1.0"

    def __init__(self, node_id, name, bridge):
        super().__init__(node_id, name, bridge)
        self.is_native = True
        self.properties["Separator"] = " "
        self.define_schema()
        self.register_handlers()

    def define_schema(self):
        self.input_schema = {
            "Flow": DataType.FLOW,
            "List": DataType.LIST,
            "Separator": DataType.STRING
        }
        self.output_schema = {
            "Flow": DataType.FLOW,
            "Result": DataType.STRING
        }

    def register_handlers(self):
        self.register_handler("Flow", self.join_strings)

    def join_strings(self, List=None, Separator=None, **kwargs):
        # SuperNode auto-casts inputs, but we fallback to properties if None
        items = List if List is not None else self.properties.get("List", [])
        sep = Separator if Separator is not None else self.properties.get("Separator", " ")
        
        if not isinstance(items, list): items = [str(items)]
        result = str(sep).join(str(i) for i in items)
        
        self.bridge.set(f"{self.node_id}_Result", result, self.name)
        return True

@NodeRegistry.register("Substring", "Data/Strings")
class StringPartNode(SuperNode):
    """
    Extracts a portion of a string based on start and end indices.
    
    Inputs:
    - Flow: Execution trigger.
    - String: The source string.
    - Start: The starting index (inclusive).
    - End: The ending index (exclusive). If empty, extracts to the end.
    
    Outputs:
    - Flow: Triggered after the extraction.
    - Result: The extracted portion of the string.
    """
    version = "2.1.0"

    def __init__(self, node_id, name, bridge):
        super().__init__(node_id, name, bridge)
        self.properties["Start"] = 0
        self.properties["End"] = ""
        self.define_schema()
        self.register_handlers()

    def define_schema(self):
        self.input_schema = {
            "Flow": DataType.FLOW,
            "String": DataType.STRING,
            "Start": DataType.INTEGER,
            "End": DataType.INTEGER # Optional
        }
        self.output_schema = {
            "Flow": DataType.FLOW,
            "Result": DataType.STRING
        }

    def register_handlers(self):
        self.register_handler("Flow", self.substring)

    def substring(self, String="", Start=0, End=None, **kwargs):
        # Fix: explicitly check for None to allow empty strings
        s_val = String if String is not None else self.properties.get("String", "")
        start_val = Start if Start is not None else self.properties.get("Start", 0)
        end_val = End if End is not None else self.properties.get("End", "")

        try:
            start_idx = int(start_val)
            if end_val == "" or end_val is None: 
                result = str(s_val)[start_idx:]
            else:
                end_idx = int(end_val)
                result = str(s_val)[start_idx:end_idx]
        except Exception as e:
            self.logger.warning(f"Substring Error: {e}")
            result = str(s_val)
            
        self.bridge.set(f"{self.node_id}_Result", result, self.name)
        return True

@NodeRegistry.register("String Length", "Data/Strings")
class StringLengthNode(SuperNode):
    """
    Calculates the number of characters in a string.
    
    Inputs:
    - Flow: Execution trigger.
    - String: The string to measure.
    
    Outputs:
    - Flow: Triggered after the calculation.
    - Result: The character count.
    """
    version = "2.1.0"

    def __init__(self, node_id, name, bridge):
        super().__init__(node_id, name, bridge)
        self.define_schema()
        self.register_handlers()

    def define_schema(self):
        self.input_schema = {
            "Flow": DataType.FLOW,
            "String": DataType.STRING
        }
        self.output_schema = {
            "Flow": DataType.FLOW,
            "Result": DataType.INTEGER
        }

    def register_handlers(self):
        self.register_handler("Flow", self.calc_length)

    def calc_length(self, String="", **kwargs):
        s_val = String if String is not None else self.properties.get("String", "")
        result = len(str(s_val))
        self.bridge.set(f"{self.node_id}_Result", result, self.name)
        return True

@NodeRegistry.register("String Find", "Data/Strings")
class StringFindNode(SuperNode):
    """
    Finds the first occurrence of a substring within a larger string.
    
    Inputs:
    - Flow: Execution trigger.
    - String: The main string to search within.
    - Substring: The text to find.
    - Start Index: The position to start searching from (default: 0).
    
    Outputs:
    - Flow: Triggered after the search is complete.
    - Position: The index of the substring (-1 if not found).
    """
    version = "2.1.0"

    def __init__(self, node_id, name, bridge):
        super().__init__(node_id, name, bridge)
        self.is_native = True
        self.properties["Start Index"] = 0
        self.define_schema()
        self.register_handlers()

    def define_schema(self):
        self.input_schema = {
            "Flow": DataType.FLOW,
            "String": DataType.STRING,
            "Substring": DataType.STRING,
            "Start Index": DataType.INTEGER
        }
        self.output_schema = {
            "Flow": DataType.FLOW,
            "Position": DataType.INTEGER
        }

    def register_handlers(self):
        self.register_handler("Flow", self.find_string)

    def find_string(self, String="", Substring="", **kwargs):
        s_val = String if String is not None else self.properties.get("String", "")
        sub_val = Substring if Substring is not None else self.properties.get("Substring", "")
        
        # We need to manually extract Start Index from kwargs or properties due to name spaces
        start_idx = kwargs.get("Start Index")
        if start_idx is None:
            start_idx = self.properties.get("Start Index", 0)

        # Ensure types to prevent crashes
        s_str = str(s_val) if s_val is not None else ""
        sub_str = str(sub_val) if sub_val is not None else ""
        
        try:
            start_pos = int(start_idx)
        except (ValueError, TypeError):
            start_pos = 0

        result = s_str.find(sub_str, start_pos)
        
        self.bridge.set(f"{self.node_id}_Position", result, self.name)
        return True


@NodeRegistry.register("String Combine", "Data/Strings")
class StringCombineNode(SuperNode):
    """
    Combines multiple dynamically added input variables into a single concatenated string.
    
    Inputs:
    - Flow: Execution trigger.
    - [Dynamic Inputs]: Add as many string inputs as you need via the node's context menu.
    
    Outputs:
    - Flow: Triggered after concatenation.
    - Result: The combined string.
    """
    version = "2.1.0"
    allow_dynamic_inputs = True

    def __init__(self, node_id, name, bridge):
        super().__init__(node_id, name, bridge)
        self.is_native = True
        self.hidden_fields = ["additional_inputs"]
        self.define_schema()
        self.register_handlers()

    def define_schema(self):
        self.input_schema = {
            "Flow": DataType.FLOW
        }
        self.output_schema = {
            "Flow": DataType.FLOW,
            "Result": DataType.STRING
        }

    def register_handlers(self):
        self.register_handler("Flow", self.combine_strings)

    def combine_strings(self, **kwargs):
        # We need to collect all dynamic inputs and append them in order.
        # Check current inputs defined in properties to preserve visual order.
        dynamic_inputs = self.properties.get("additional_inputs") or self.properties.get("Additional Inputs", [])
        
        # [FIX] If the UI accidentally stringified the list, parse it back to a list
        if isinstance(dynamic_inputs, str):
            import ast
            try:
                dynamic_inputs = ast.literal_eval(dynamic_inputs)
            except Exception:
                dynamic_inputs = []
        
        if not isinstance(dynamic_inputs, list):
            dynamic_inputs = []
        
        combined_string = ""
        for pin_name in dynamic_inputs:
            # First try kwargs, then properties
            val = kwargs.get(pin_name)
            if val is None:
                val = self.properties.get(pin_name, "")
            
            # [FIX] UI often encodes untyped properties as ['str', 'value']
            # We must unwrap it before combining
            if isinstance(val, list) and len(val) == 2 and isinstance(val[0], str):
                # Check if it looks like a type identifier (e.g. 'str', 'int', 'bool', 'any')
                if val[0].lower() in ["str", "string", "int", "integer", "float", "number", "bool", "boolean", "any"]:
                    val = val[1]
            
            # Append string representation
            if val is not None:
                combined_string += str(val)

        self.bridge.set(f"{self.node_id}_Result", combined_string, self.name)
        return True
