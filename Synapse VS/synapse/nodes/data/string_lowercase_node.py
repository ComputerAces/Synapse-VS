from synapse.core.super_node import SuperNode
from synapse.nodes.registry import NodeRegistry
from synapse.core.types import DataType

@NodeRegistry.register("String Lowercase", "Data")
class StringLowercaseNode(SuperNode):
    """
    Converts all characters in a text string to lowercase.
    
    Inputs:
    - Flow: Trigger the conversion.
    - Value: The source text string.
    
    Outputs:
    - Flow: Triggered after conversion.
    - Result: The lowercase version of the string.
    """
    version = "2.1.0"

    def __init__(self, node_id, name, bridge):
        super().__init__(node_id, name, bridge)
        self.is_native = True
        self.properties["Value"] = ""
        self.define_schema()
        self.register_handlers()

    def register_handlers(self):
        self.register_handler("Flow", self.process_lowercase)

    def define_schema(self):
        self.input_schema = {
            "Flow": DataType.FLOW,
            "Value": DataType.STRING
        }
        self.output_schema = {
            "Flow": DataType.FLOW,
            "Result": DataType.STRING
        }

    def process_lowercase(self, Value=None, **kwargs):
        val = Value if Value is not None else kwargs.get("Value") or self.properties.get("Value", "")
        if val is None:
            val = ""
        
        result = str(val).lower()
        
        self.bridge.set(f"{self.node_id}_Result", result, self.name)
        self.bridge.set(f"{self.node_id}_ActivePorts", ["Flow"], self.name)
        return True
