from synapse.core.super_node import SuperNode
from synapse.nodes.registry import NodeRegistry
from synapse.core.types import DataType

@NodeRegistry.register("Boolean", "Data")
class BooleanNode(SuperNode):
    """
    Standard data node for boolean values (True/False).
    Allows manual entry or dynamic conversion of various inputs to boolean.
    
    Inputs:
    - Flow: Trigger execution to update the output result.
    - Value: The value to be converted/set (supports strings like 'True', '1', 'Yes').
    
    Outputs:
    - Flow: Triggered after processing.
    - Result: The resulting boolean value (True or False).
    """
    version = "2.1.0"

    def __init__(self, node_id, name, bridge):
        super().__init__(node_id, name, bridge)
        self.is_native = True
        self.properties["Value"] = "False"
        self.define_schema()
        self.register_handlers()

    def register_handlers(self):
        self.register_handler("Flow", self.process_boolean)

    def define_schema(self):
        self.input_schema = {
            "Flow": DataType.FLOW,
            "Value": DataType.BOOLEAN
        }
        self.output_schema = {
            "Flow": DataType.FLOW,
            "Result": DataType.BOOLEAN
        }

    def process_boolean(self, Value=None, **kwargs):
        # 1. Resolve raw value
        is_val_provided = Value is not None or "Value" in kwargs
        raw = Value if Value is not None else kwargs.get("Value") or self.properties.get("Value", "False")
        
        # 2. Sanitize/Normalize
        is_true = str(raw).lower() in ("true", "1", "yes")
        val = 1 if is_true else 0
        
        # 3. Update internal property if set via Flow
        if is_val_provided:
             self.properties["Value"] = "True" if is_true else "False"

        self.bridge.set(f"{self.node_id}_Result", val, self.name)
        self.bridge.set(f"{self.node_id}_ActivePorts", ["Flow"], self.name)
        return True
