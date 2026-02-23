from synapse.core.super_node import SuperNode
from synapse.nodes.registry import NodeRegistry
from synapse.core.types import DataType
import json

@NodeRegistry.register("String To Data", "Data")
class StringToDataNode(SuperNode):
    """
    Parses a JSON-formatted string into a structured Data object (Dictionary or List).
    
    Inputs:
    - Flow: Trigger the conversion.
    - String: The JSON string to parse.
    
    Outputs:
    - Flow: Triggered if parsing is successful.
    - Error Flow: Triggered if the string is not valid JSON.
    - Data: The resulting Dictionary or List.
    """
    version = "2.1.0"

    def __init__(self, node_id, name, bridge):
        super().__init__(node_id, name, bridge)
        self.is_native = True
        self.properties["String"] = ""
        self.define_schema()
        self.register_handlers()

    def define_schema(self):
        self.input_schema = {
            "Flow": DataType.FLOW,
            "String": DataType.STRING
        }
        self.output_schema = {
            "Flow": DataType.FLOW,
            "Error Flow": DataType.FLOW,
            "Data": DataType.ANY
        }

    def register_handlers(self):
        self.register_handler("Flow", self.convert)

    def convert(self, String=None, **kwargs):
        val = String if String is not None else kwargs.get("String") or self.properties.get("String", "")
        
        if not val:
            self.bridge.set(f"{self.node_id}_Data", {}, self.name)
            self.bridge.set(f"{self.node_id}_ActivePorts", ["Flow"], self.name)
            return True
            
        try:
            result = json.loads(val)
            self.bridge.set(f"{self.node_id}_Data", result, self.name)
            self.bridge.set(f"{self.node_id}_ActivePorts", ["Flow"], self.name)
        except Exception as e:
            self.logger.error(f"String To Data Error: {e}")
            self.bridge.set(f"{self.node_id}_ActivePorts", ["Error Flow"], self.name)
            
        return True
