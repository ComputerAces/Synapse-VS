from synapse.core.super_node import SuperNode
from synapse.nodes.registry import NodeRegistry
from synapse.core.types import DataType

@NodeRegistry.register("Data Type", "Data")
class DataTypeNode(SuperNode):
    """
    Checks the underlying type of the provided Data and routes execution
    flow accordingly.
    
    Inputs:
    - Flow: Trigger type check.
    - Data: Any data to check.
    
    Outputs:
    - String Flow: Triggered if Data is a string.
    - Number Flow: Triggered if Data is an integer or float.
    - Boolean Flow: Triggered if Data is True or False.
    - List Flow: Triggered if Data is a List, Tuple, or Set.
    - Dict Flow: Triggered if Data is a Dictionary / JSON object.
    - None Flow: Triggered if Data is None or Empty.
    - Unknown Flow: Triggered if the type is unrecognized (e.g., custom object or binary).
    """
    version = "2.1.0"

    def __init__(self, node_id, name, bridge):
        super().__init__(node_id, name, bridge)
        self.is_native = True
        self.define_schema()
        self.register_handlers()

    def define_schema(self):
        self.input_schema = {
            "Flow": DataType.FLOW,
            "Data": DataType.ANY
        }
        self.output_schema = {
            "String Flow": DataType.FLOW,
            "Number Flow": DataType.FLOW,
            "Boolean Flow": DataType.FLOW,
            "List Flow": DataType.FLOW,
            "Dict Flow": DataType.FLOW,
            "None Flow": DataType.FLOW,
            "Unknown Flow": DataType.FLOW
        }

    def register_handlers(self):
        self.register_handler("Flow", self.check_type)

    def check_type(self, Data=None, **kwargs):
        data_obj = Data if Data is not None else self.properties.get("Data")

        active_port = "Unknown Flow"

        if data_obj is None:
            active_port = "None Flow"
        elif isinstance(data_obj, str):
            active_port = "String Flow"
        elif isinstance(data_obj, bool):  # Note: bool inherits from int in Python, check bool first!
            active_port = "Boolean Flow"
        elif isinstance(data_obj, (int, float)):
            active_port = "Number Flow"
        elif isinstance(data_obj, (list, tuple, set)):
            active_port = "List Flow"
        elif isinstance(data_obj, dict):
            active_port = "Dict Flow"

        self.bridge.set(f"{self.node_id}_ActivePorts", [active_port], self.name)
        return True
