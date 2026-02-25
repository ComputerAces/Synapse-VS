from synapse.core.super_node import SuperNode
from synapse.nodes.registry import NodeRegistry
from synapse.core.types import DataType

@NodeRegistry.register("String", "Data")
class StringNode(SuperNode):
    """
    Manages a text string value. Supports dynamic updates via the Flow input.
    
    Inputs:
    - Flow: Trigger the string retrieval/update.
    - Value: Optional text string to set.
    
    Outputs:
    - Flow: Triggered after the string is processed.
    - Result: The current text string.
    """
    version = "2.1.0"

    def __init__(self, node_id, name, bridge):
        super().__init__(node_id, name, bridge)
        self.is_native = True
        self.properties["Value"] = ""
        self.define_schema()
        self.register_handlers()

    def register_handlers(self):
        self.register_handler("Flow", self.process_string)

    def define_schema(self):
        self.input_schema = {
            "Flow": DataType.FLOW,
            "Value": DataType.STRING
        }
        self.output_schema = {
            "Flow": DataType.FLOW,
            "Result": DataType.STRING
        }

    def process_string(self, Value=None, **kwargs):
        # 1. Update internal property if Value is provided via Flow (Set)
        val_input = Value if Value is not None else kwargs.get("Value")
        if val_input is not None:
            self.properties["Value"] = str(val_input)
            
        # 2. Return current Value property
        val = self.properties.get("Value", "")
        
        self.bridge.set(f"{self.node_id}_Result", val, self.name)
        self.bridge.set(f"{self.node_id}_ActivePorts", ["Flow"], self.name)
        return True
