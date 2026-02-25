from synapse.core.super_node import SuperNode
from synapse.nodes.registry import NodeRegistry
from synapse.core.types import DataType
from datetime import datetime

@NodeRegistry.register("Date", "Data")
class DateNode(SuperNode):
    """
    Manages a date string value. Defaults to the current system date if not specified.
    
    Inputs:
    - Flow: Trigger the date retrieval/update.
    - Value: Optional date string (YYYY-MM-DD) to set.
    
    Outputs:
    - Flow: Triggered after the date is processed.
    - Result: The current date string.
    """
    version = "2.1.0"

    def __init__(self, node_id, name, bridge):
        super().__init__(node_id, name, bridge)
        self.is_native = True
        # Default to today
        self.properties["Value"] = datetime.now().strftime("%Y-%m-%d")
        self.define_schema()
        self.register_handlers()

    def register_handlers(self):
        self.register_handler("Flow", self.process_date)

    def define_schema(self):
        self.input_schema = {
            "Flow": DataType.FLOW,
            "Value": DataType.STRING
        }
        self.output_schema = {
            "Flow": DataType.FLOW,
            "Result": DataType.STRING
        }

    def process_date(self, Value=None, **kwargs):
        # 1. Update internal property if Value is provided via Flow (Set)
        val_input = Value if Value is not None else kwargs.get("Value")
        if val_input is not None:
            self.properties["Value"] = str(val_input)
            
        # 2. Return current Value property
        val = self.properties.get("Value")
        if not val:
             val = datetime.now().strftime("%Y-%m-%d")

        self.bridge.set(f"{self.node_id}_Result", val, self.name)
        self.bridge.set(f"{self.node_id}_ActivePorts", ["Flow"], self.name)
        return True
