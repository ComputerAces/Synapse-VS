from synapse.core.super_node import SuperNode
from synapse.nodes.registry import NodeRegistry
from synapse.core.types import DataType

@NodeRegistry.register("Write Mode", "Enums")
class WriteModeEnum(SuperNode):
    """
    Standardizes file writing behaviors such as 'Overwrite' or 'Append'.
    
    This node provides a UI dropdown for selecting how file operations should 
    interact with existing files. 'Overwrite' replaces the entire file content, 
    while 'Append' adds new data to the end of the file.
    
    Inputs:
    - Value: The selected write mode (Overwrite/Append).
    - Value Options: The list of toggleable modes.
    - Header Color: The UI accent color for this node.
    
    Outputs:
    - Result: The selected mode string (compatible with Write nodes).
    """
    version = "2.1.0"

    def __init__(self, node_id, name, bridge):
        super().__init__(node_id, name, bridge)
        self.is_native = True
        self.properties["Value"] = "Overwrite"
        self.properties["Value Options"] = ["Overwrite", "Append"]
        self.properties["Header Color"] = "#32CD32" # LimeGreen
        self.define_schema()
        self.update_state()

    def define_schema(self):
        self.input_schema = {
            "Value": DataType.STRING,
            "Value Options": DataType.LIST,
            "Header Color": DataType.COLOR
        }
        self.output_schema = {
            "Result": DataType.WriteType
        }

    def update_state(self):
        val = self.properties.get("Value", "Overwrite")
        self.bridge.set(f"{self.node_id}_Result", val, self.name)

    def set_property(self, name, value):
        super().set_property(name, value)
        if name == "value":
            self.update_state()
