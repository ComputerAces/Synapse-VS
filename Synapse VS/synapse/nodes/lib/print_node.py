from synapse.core.super_node import SuperNode
from synapse.nodes.registry import NodeRegistry
from synapse.core.types import DataType

@NodeRegistry.register("Print", "System/Terminal")
class PrintNode(SuperNode):
    """
    Outputs a message to the system terminal or console.
    Useful for debugging and tracking graph execution flow.
    
    Inputs:
    - Flow: Trigger the print operation.
    - Message: The string message to display.
    
    Outputs:
    - Flow: Pulse triggered after the message is printed.
    """
    version = "2.1.0"

    def __init__(self, node_id, name, bridge):
        super().__init__(node_id, name, bridge)
        self.is_native = True # Run in main process for faster console output
        self.define_schema()
        self.register_handlers()

    def register_handlers(self):
        self.register_handler("Flow", self.do_print)

    def define_schema(self):
        self.input_schema = {
            "Flow": DataType.FLOW,
            "Message": DataType.STRING
        }
        self.output_schema = {
            "Flow": DataType.FLOW
        }

    def do_print(self, Message=None, **kwargs):
        # inputs are passed by port name (e.g. "Message")
        message = Message if Message is not None else kwargs.get("Message") or "Hello Synapse!"
        print(f"[{self.name}] OUTPUT: {message}")
        self.bridge.set(f"last_msg_{self.name}", message, self.name)
        self.bridge.set(f"{self.node_id}_ActivePorts", ["Flow"], self.name)
        return True
