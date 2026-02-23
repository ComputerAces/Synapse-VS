import re
from synapse.core.super_node import SuperNode
from synapse.nodes.registry import NodeRegistry
from synapse.core.types import DataType

@NodeRegistry.register("Regex", "Data/Strings")
class RegexNode(SuperNode):
    """
    Checks if a string matches a regular expression pattern.
    
    Inputs:
    - Flow: Execution trigger.
    - Text: The string to search.
    - Pattern: The regular expression pattern.
    
    Outputs:
    - Flow: Triggered after search.
    - Found: True if a match was found.
    - Matches: List of all matches found.
    """
    version = "2.1.0"

    def __init__(self, node_id, name, bridge):
        super().__init__(node_id, name, bridge)
        self.is_native = True
        self.properties["Text"] = ""
        self.properties["Pattern"] = ""
        self.define_schema()
        self.register_handlers()

    def define_schema(self):
        self.input_schema = {
            "Flow": DataType.FLOW,
            "Text": DataType.STRING,
            "Pattern": DataType.STRING
        }
        self.output_schema = {
            "Flow": DataType.FLOW,
            "Found": DataType.BOOLEAN,
            "Matches": DataType.LIST
        }

    def register_handlers(self):
        self.register_handler("Flow", self.handle_regex)

    def handle_regex(self, Text=None, Pattern=None, **kwargs):
        text = Text if Text is not None else kwargs.get("Text") or self.properties.get("Text", "")
        pattern = Pattern if Pattern is not None else kwargs.get("Pattern") or self.properties.get("Pattern", "")
        
        matches = []
        found = False
        
        try:
            if pattern and text:
                matches = re.findall(pattern, str(text))
                found = len(matches) > 0
        except Exception as e:
            self.logger.error(f"Regex Error: {e}")
            
        self.bridge.set(f"{self.node_id}_Found", found, self.name)
        self.bridge.set(f"{self.node_id}_Matches", matches, self.name)
        self.bridge.set(f"{self.node_id}_ActivePorts", ["Flow"], self.name)
        
        return True
