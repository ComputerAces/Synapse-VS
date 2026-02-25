from synapse.core.super_node import SuperNode
from synapse.nodes.registry import NodeRegistry
from synapse.core.types import DataType

@NodeRegistry.register("Try Node", "Logic/Control Flow")
class TryNode(SuperNode):
    """
    Initiates a protected execution block (Exception Handler).
    
    Wraps downstream flow in a try-catch pattern. If any node in the 
    'Flow' branch encounters an error, the engine will intercept it 
    and pulse the 'Catch' port of this node.
    
    Inputs:
    - Flow: Trigger the protected branch.
    
    Outputs:
    - Flow: The primary pulse to protect.
    - Catch: Pulse triggered only on execution failure.
    - FailedNode: Name or ID of the node that threw the error.
    - ErrorCode: Error message or status code.
    """
    version = "2.1.0"

    def __init__(self, node_id, name, bridge):
        super().__init__(node_id, name, bridge)
        self.define_schema()
        self.register_handlers()

    def register_handlers(self):
        self.register_handler("Flow", self.do_work)

    def define_schema(self):
        self.input_schema = {
            "Flow": DataType.FLOW
        }
        self.output_schema = {
            "Flow": DataType.FLOW,
            "Catch": DataType.FLOW,
            "FailedNode": DataType.STRING,
            "ErrorCode": DataType.ANY
        }

    def do_work(self, **kwargs):
        # Engine handles nesting via Class Name check.
        self.bridge.set(f"{self.node_id}_ActivePorts", ["Flow"], self.name)
        
        # Initialize Error Data
        self.bridge.set(f"{self.node_id}_FailedNode", "", self.name)
        self.bridge.set(f"{self.node_id}_ErrorCode", 0, self.name)
        
        return True