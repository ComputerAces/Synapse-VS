from synapse.core.super_node import SuperNode
from synapse.nodes.registry import NodeRegistry
from synapse.core.types import DataType
import re

@NodeRegistry.register("Search (Regex)", "Data")
class SearchNode(SuperNode):
    """
    Searches for a regular expression pattern within a provided text string.
    Returns the first match found, its position, and a success flag.
    
    Inputs:
    - Flow: Trigger the search.
    - Text: The source string to search within.
    - Pattern: The RegEx pattern to look for.
    - Start Index: The character position to begin the search from.
    
    Outputs:
    - Flow: Triggered after the search is complete.
    - Match: The text content of the first match found.
    - Position: The character index where the match begins.
    - Found: True if a match was successfully identified.
    """
    version = "2.1.0"

    def __init__(self, node_id, name, bridge):
        super().__init__(node_id, name, bridge)
        self.is_native = True
        self.properties["Text"] = ""
        self.properties["Pattern"] = ""
        self.define_schema()
        self.register_handlers()

    def register_handlers(self):
        self.register_handler("Flow", self.process_search)

    def define_schema(self):
        self.input_schema = {
            "Flow": DataType.FLOW,
            "Text": DataType.STRING,
            "Pattern": DataType.STRING,
            "Start Index": DataType.INT
        }
        self.output_schema = {
            "Flow": DataType.FLOW,
            "Match": DataType.STRING,
            "Position": DataType.INT,
            "Found": DataType.BOOLEAN
        }

    def process_search(self, Text=None, Pattern=None, Start_Index=None, **kwargs):
        text = str(Text) if Text is not None else kwargs.get("Text") or self.properties.get("Text", "")
        pattern = str(Pattern) if Pattern is not None else kwargs.get("Pattern") or self.properties.get("Pattern", "")
        start_idx = Start_Index if Start_Index is not None else kwargs.get("Start Index") or 0
        
        try:
             start_idx = int(start_idx)
        except:
             start_idx = 0
        
        try:
            regex = re.compile(pattern)
            match = regex.search(text, pos=start_idx)
            
            if match:
                found = True
                result = match.group(0)
                position = match.start()
            else:
                found = False
                result = ""
                position = -1
                
            self.bridge.set(f"{self.node_id}_Match", result, self.name)
            self.bridge.set(f"{self.node_id}_Position", position, self.name)
            self.bridge.set(f"{self.node_id}_Found", found, self.name)
            self.bridge.set(f"{self.node_id}_ActivePorts", ["Flow"], self.name)
            return True
            
        except re.error as e:
            self.logger.error(f"Regex Error: {e}")
            self.bridge.set(f"{self.node_id}_Match", "Error", self.name)
            self.bridge.set(f"{self.node_id}_Found", False, self.name)
            self.bridge.set(f"{self.node_id}_ActivePorts", ["Flow"], self.name)
            return True
