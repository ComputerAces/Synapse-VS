from synapse.core.super_node import SuperNode
from synapse.nodes.registry import NodeRegistry
from datetime import datetime
from synapse.core.types import DataType

@NodeRegistry.register("Time", "System/Time")
class TimeNode(SuperNode):
    """
    Captures the current system date and time.
    Returns the timestamp in a standardized format inside Synapse tags.
    
    Inputs:
    - Flow: Trigger the time capture.
    
    Outputs:
    - Flow: Pulse triggered after time is captured.
    - Time: The current timestamp string (e.g., #[2024-05-20 12:00:00]#).
    """
    version = "2.1.0"

    def __init__(self, node_id, name, bridge):
        super().__init__(node_id, name, bridge)
        self.is_native = True
        self.define_schema()
        self.register_handlers()

    def define_schema(self):
        self.input_schema = {"Flow": DataType.FLOW}
        self.output_schema = {"Flow": DataType.FLOW, "Time": DataType.STRING}

    def register_handlers(self):
        self.register_handler("Flow", self.capture_time)

    def capture_time(self, **kwargs):
        now_raw = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        now = f"#[{now_raw}]#"
        self.bridge.set(f"{self.node_id}_Time", now, self.name)
        self.bridge.set(f"{self.node_id}_ActivePorts", ["Flow"], self.name)
        return True
