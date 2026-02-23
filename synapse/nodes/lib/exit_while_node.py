from synapse.core.super_node import SuperNode
from synapse.nodes.registry import NodeRegistry
from synapse.core.types import DataType

@NodeRegistry.register("Exit While", "Flow")
class ExitWhileNode(SuperNode):
    """
    Terminates an active While loop early.
    
    Acts as a 'break' statement. When triggered, it signals the 'While Loop' 
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
        # Simply fire the Flow output
        # The user wires Flow Out -> Loop Exit In
        self.logger.info("EXIT WHILE triggered")
        self.bridge.set(f"{self.node_id}_ActivePorts", ["Flow"], self.name)
        return True
