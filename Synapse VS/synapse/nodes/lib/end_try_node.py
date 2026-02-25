from synapse.core.super_node import SuperNode
from synapse.nodes.registry import NodeRegistry
from synapse.core.types import DataType

@NodeRegistry.register("End Try Node", "Flow/Error Handling")
class EndTryNode(SuperNode):
    """
    Closes an error-handling (Try/Catch) scope.
    
    This node serves as a marker for the Execution Engine to pop the current 
    error-handling context and continue normal flow. It ensures that subsequent 
    errors are handled by the next level up in the hierarchy.
    
    Inputs:
    - Flow: Execution trigger from the Try or Catch block.
    
    Outputs:
    - Flow: Pulse triggered after the scope is safely closed.
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
            "Flow": DataType.FLOW
        }

    def do_work(self, **kwargs):
        # Engine handles popping context via Class Name check.
        # This node just acts as a marker for the engine and continues flow.
        self.bridge.set(f"{self.node_id}_ActivePorts", ["Flow"], self.name)
        return True
