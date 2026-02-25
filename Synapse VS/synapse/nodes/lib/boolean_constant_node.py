from synapse.core.super_node import SuperNode
from synapse.nodes.registry import NodeRegistry
from synapse.core.types import DataType

@NodeRegistry.register("Boolean Type", "Logic")
class BooleanTypeNode(SuperNode):
    """
    A constant boolean node that outputs a fixed True or False value.
    Useful for setting toggles or flags within a graph.
    
    Inputs:
    - Flow: Triggered upon execution.
    - Value: The constant boolean value to output.

    Outputs:
    - Flow: Triggered upon execution.
    - Result: The constant boolean value.
    """
    version = "2.1.0"

    def __init__(self, node_id, name, bridge):
        super().__init__(node_id, name, bridge)
        self.is_native = True
        self.properties["Value"] = "True"
        self.define_schema()
        self.register_handlers()

    def define_schema(self):
        self.input_schema = {
            "Flow": DataType.FLOW,
            "Value": DataType.BOOLEAN
        }
        self.output_schema = {
            "Flow": DataType.FLOW,
            "Result": DataType.BOOLEAN
        }

    def register_handlers(self):
        self.register_handler("Flow", self.process_boolean)

    def process_boolean(self, **kwargs):
        # This node just returns its property.
        prop_val = self.properties.get("Value", "True")
        val = (str(prop_val).lower() == "true")
            
        self.bridge.set(f"{self.node_id}_Result", val, self.name)
        self.bridge.set(f"{self.node_id}_ActivePorts", ["Flow"], self.name)
        return True
