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
