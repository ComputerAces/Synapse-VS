from synapse.core.super_node import SuperNode
from synapse.nodes.registry import NodeRegistry
from synapse.core.types import DataType

@NodeRegistry.register("Split Text", "Data")
class SplitTextNode(SuperNode):
    """
    Divides a text string into a list of substrings based on a specified delimiter.
    
    Inputs:
    - Flow: Trigger the split operation.
    - Text: The source string to be divided.
    - Delimiter: The character or substring used to split the text.
    
    Outputs:
    - Flow: Triggered after the text is split.
    - List: The resulting list of substrings.
    """
    version = "2.1.0"

    def __init__(self, node_id, name, bridge):
        super().__init__(node_id, name, bridge)
        self.is_native = True
        self.properties["Text"] = ""
        self.properties["Delimiter"] = " "
        self.define_schema()
        self.register_handlers()

    def register_handlers(self):
        self.register_handler("Flow", self.process_split)

    def define_schema(self):
        self.input_schema = {
            "Flow": DataType.FLOW,
            "Text": DataType.STRING,
            "Delimiter": DataType.STRING
        }
        self.output_schema = {
            "Flow": DataType.FLOW,
            "List": DataType.LIST
        }

    def process_split(self, Text=None, Delimiter=None, **kwargs):
        # 1. Resolve Inputs
        text_val = Text if Text is not None else kwargs.get("Text") or self.properties.get("Text", "")
        delim_val = Delimiter if Delimiter is not None else kwargs.get("Delimiter") or self.properties.get("Delimiter", " ")
        
        # 2. Logic
        text_str = str(text_val)
        delim_str = str(delim_val)
        
        if not delim_str:
            # Fallback: List of characters if delimiter is empty
            result = list(text_str)
        else:
            result = text_str.split(delim_str)
            
        print(f"[{self.name}] Split Text: '{text_str}' by '{delim_str}' -> {result}")
        
        # 3. Set Outputs to Bridge
        self.bridge.set(f"{self.node_id}_List", result, self.name)
        self.bridge.set(f"{self.node_id}_ActivePorts", ["Flow"], self.name)
        return True
