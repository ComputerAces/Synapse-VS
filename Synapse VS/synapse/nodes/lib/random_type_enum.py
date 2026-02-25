from synapse.core.super_node import SuperNode
from synapse.nodes.registry import NodeRegistry
from synapse.core.types import DataType
from enum import Enum

@NodeRegistry.register("Random Type", "Enums")
class RandomTypeEnumNode(SuperNode):
    """
    Standardizes the selection of random generation algorithms.
    
    Provides a consistent label for common random types like 'Number' (float), 
    'Integer', or 'Unique ID' (UUID). This node is typically linked to a 
    'Random' node to define its behavior.
    
    Inputs:
    - Value: The random type selection (Number, Integer, UID).
    
    Outputs:
    - Result: The selected type string.
    """
    version = "2.1.0"

    def __init__(self, node_id, name, bridge):
        super().__init__(node_id, name, bridge)
        self.is_native = True
        self.properties["Value"] = "Number"
        self.define_schema()
        # Initial value set
        self.set_value()

    def define_schema(self):
        self.input_schema = {
            "Value": DataType.NUMBER
        }
        self.output_schema = {
            "Result": DataType.COMPARE # Using COMPARE or something that works as ENUM source? Actually DataType.ENUM doesn't exist? Wait I checked types.py.
        }

    def set_value(self):
        val = self.properties.get("Value", "Number")
        self.bridge.set(f"{self.node_id}_Result", val, self.name)
