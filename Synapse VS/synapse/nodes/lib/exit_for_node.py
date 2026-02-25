from synapse.core.super_node import SuperNode
from synapse.nodes.registry import NodeRegistry
from synapse.core.types import DataType

@NodeRegistry.register("Exit For", "Flow")
class ExitForNode(SuperNode):
    """
    Terminates an active loop (For or Foreach) early.
    
    Acts as a 'break' statement. When triggered, it signals the parent loop 
    node to stop iterating and transition to its completion 'Flow' output.
    
    Inputs:
    - Flow: Trigger the break signal.
    
    Outputs:
    - Flow: Pulse triggered after the signal is sent.
    """
    version = "2.1.0"

    def __init__(self, node_id, name, bridge):
        super().__init__(node_id, name, bridge)
        self.is_native = True
        self.define_schema()
        self.register_handlers()

    def register_handlers(self):
        self.register_handler("Flow", self.do_work)

    def define_schema(self):
        self.input_schema = {
            "Flow": DataType.FLOW
        }
        self.output_schema = {
            "Flow": DataType.FLOW
        }

    def do_work(self, **kwargs):
        self.logger.info("EXIT FOR triggered")
        self.bridge.set(f"{self.node_id}_ActivePorts", ["Flow"], self.name)
        return True
