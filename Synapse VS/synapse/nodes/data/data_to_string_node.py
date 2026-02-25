from synapse.core.super_node import SuperNode
from synapse.nodes.registry import NodeRegistry
from synapse.core.types import DataType
import json

@NodeRegistry.register("Data To String", "Data")
class DataToStringNode(SuperNode):
    """
    Converts a structured Data object (Dictionary or List) into a JSON-formatted string.
    
    Inputs:
    - Flow: Trigger the conversion.
    - Data: The object (Dictionary or List) to serialize.
    - Indent: If True, uses 2-space indentation for readability.
    
    Outputs:
    - Flow: Triggered if serialization is successful.
    - Error Flow: Triggered if the item cannot be serialized.
    - String: The resulting JSON string.
    """
    version = "2.1.0"

    def __init__(self, node_id, name, bridge):
        super().__init__(node_id, name, bridge)
        self.is_native = True
        self.properties["Indent"] = True
        self.define_schema()
        self.register_handlers()

    def define_schema(self):
        self.input_schema = {
            "Flow": DataType.FLOW,
            "Data": DataType.ANY,
            "Indent": DataType.BOOLEAN
        }
        self.output_schema = {
            "Flow": DataType.FLOW,
            "Error Flow": DataType.FLOW,
            "String": DataType.STRING
        }

    def register_handlers(self):
        self.register_handler("Flow", self.convert)

    def convert(self, Data=None, Indent=None, **kwargs):
        val = Data if Data is not None else kwargs.get("Data")
        indent_val = Indent if Indent is not None else kwargs.get("Indent") if kwargs.get("Indent") is not None else self.properties.get("Indent", True)
        
        try:
            result = json.dumps(val, indent=2 if indent_val else None)
            self.bridge.set(f"{self.node_id}_String", result, self.name)
            self.bridge.set(f"{self.node_id}_ActivePorts", ["Flow"], self.name)
        except Exception as e:
            self.logger.error(f"Data To String Error: {e}")
            self.bridge.set(f"{self.node_id}_ActivePorts", ["Error Flow"], self.name)
            
        return True
