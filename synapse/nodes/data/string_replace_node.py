from synapse.core.super_node import SuperNode
from synapse.nodes.registry import NodeRegistry
from synapse.core.types import DataType

@NodeRegistry.register("String Replace", "Data")
class StringReplaceNode(SuperNode):
    """
    Replaces occurrences of a substring within a source string. 
    Supports replacing the first occurrence or all occurrences, with an optional start position.
    
    Inputs:
    - Flow: Trigger the replacement.
    - Source: The text string to modify.
    - Find: The substring to look for.
    - Replace: The replacement substring.
    - Start Position: The index to begin searching from.
    - All: If True, replaces all occurrences; otherwise, replaces only the first.
    
    Outputs:
    - Flow: Triggered after the replacement is complete.
    - Result: The modified string.
    """
    version = "2.1.0"
    allow_dynamic_inputs = False

    def __init__(self, node_id, name, bridge):
        super().__init__(node_id, name, bridge)
        self.is_native = True
        self.properties["Source"] = ""
        self.properties["Find"] = ""
        self.properties["Replace"] = ""
        self.properties["Start Position"] = 0
        self.properties["All"] = True # Default to replace all
        self.define_schema()
        self.register_handlers()
        
    def register_handlers(self):
        self.register_handler("Flow", self.process_replace)

    def define_schema(self):
        self.input_schema = {
            "Flow": DataType.FLOW,
            "Source": DataType.STRING,
            "Find": DataType.STRING,
            "Replace": DataType.STRING,
            "Start Position": DataType.NUMBER,
            "All": DataType.BOOLEAN
        }
        self.output_schema = {
            "Flow": DataType.FLOW,
            "Result": DataType.STRING
        }

    def process_replace(self, Source=None, Find=None, Replace=None, Start_Position=None, All=None, **kwargs):
        # 1. Resolve Inputs
        src = Source if Source is not None else kwargs.get("Source") or self.properties.get("Source", "")
        find_str = Find if Find is not None else kwargs.get("Find") or self.properties.get("Find", "")
        rep_str = Replace if Replace is not None else kwargs.get("Replace") or self.properties.get("Replace", "")
        replace_all = All if All is not None else kwargs.get("All") if "All" in kwargs else self.properties.get("All", True)
        
        start_idx = Start_Position if Start_Position is not None else kwargs.get("Start Position") or self.properties.get("Start Position", 0)

        # Fallback to int
        try:
            start_idx = int(float(start_idx))
        except:
            start_idx = 0

        if src is None: src = ""
        src = str(src)
        find_str = str(find_str)
        rep_str = str(rep_str)

        # 2. Logic
        if start_idx < 0:
            start_idx = 0
            
        if start_idx >= len(src):
            result = src
        else:
            prefix = src[:start_idx]
            suffix = src[start_idx:]
            
            if replace_all:
                # Replace all occurrences in the suffix
                modified_suffix = suffix.replace(find_str, rep_str)
            else:
                # Replace only the FIRST occurrence in the suffix
                modified_suffix = suffix.replace(find_str, rep_str, 1)
                
            result = prefix + modified_suffix

        # 3. Output
        self.bridge.set(f"{self.node_id}_Result", result, self.name)
        self.bridge.set(f"{self.node_id}_ActivePorts", ["Flow"], self.name)
        return True
