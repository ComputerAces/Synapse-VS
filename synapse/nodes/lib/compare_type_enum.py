from synapse.core.super_node import SuperNode
from synapse.nodes.registry import NodeRegistry
from synapse.core.types import DataType
from enum import Enum

class CompareType(Enum):
    """Enumeration of standard comparison operators."""
    EQUALS = "=="
    NOT_EQUALS = "!="
    GREATER_THAN = ">"
    LESS_THAN = "<"
    GREATER_EQUAL = ">="
    LESS_EQUAL = "<="

@NodeRegistry.register("Compare Type", "Enums")
class CompareTypeEnum(SuperNode):
    """
    Provides a selectable comparison operator (e.g., ==, !=, >, <) as a pulse-triggered output.
    Essential for configuring conditional logic in nodes that require a comparison operator.
    
    Inputs:
    - Flow: Trigger the output of the selected comparison type.
    - Value: Optionally set the comparison operator via a logic pulse.
    
    Outputs:
    - Flow: Pulse triggered after the value is processed.
    - Result: The selected comparison operator string.
    """
    version = "2.1.0"

    def __init__(self, node_id, name, bridge):
        super().__init__(node_id, name, bridge)
        self.is_native = True
        self.properties["Value"] = "==" # Default
        self.define_schema()
        self.register_handlers()
        self.update_state()

    def define_schema(self):
        self.input_schema = {
            "Flow": DataType.FLOW,
            "Value": DataType.COMPARE
        }
        self.output_schema = {
            "Flow": DataType.FLOW,
            "Result": DataType.COMPARE
        }

    def register_handlers(self):
        self.register_handler("Flow", self.handle_flow)

    def handle_flow(self, Value=None, **kwargs):
        if Value is not None:
            self.properties["Value"] = Value
        self.update_state()
        self.bridge.set(f"{self.node_id}_ActivePorts", ["Flow"], self.name)
        return True

    def update_state(self):
        val = self.properties.get("Value", "==")
        self.bridge.set(f"{self.node_id}_Result", val, self.name)
        
    def set_property(self, name, value):
        super().set_property(name, value)
        if name.lower() == "value":
            self.update_state()
