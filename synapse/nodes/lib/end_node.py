from synapse.core.super_node import SuperNode
from synapse.nodes.registry import NodeRegistry
from synapse.core.types import DataType

@NodeRegistry.register("End Node", "Logic/Control Flow")
class EndNode(SuperNode):
    """
    Terminates the execution of the current branch.
    
    When flow reaches this node, the execution engine stops processing further nodes 
    in this specific sequence. It is used to mark the logical conclusion of a 
    workflow where no further output pulse is desired.
    
    Inputs:
    - Flow: Execution trigger.

    Outputs:
    - None: This node is a terminator and has no outputs.
    """
    version = "2.1.0"

    def __init__(self, node_id, name, bridge):
        super().__init__(node_id, name, bridge)
        self.is_native = True
        self.define_schema()
        self.register_handlers()
    
    def register_handlers(self):
        self.register_handler("Flow", self.end_execution)

    def define_schema(self):
        # Terminators are forbidden from having output ports
        self.input_schema = {
            "Flow": DataType.FLOW
        }
        self.output_schema = {}

    def end_execution(self, **kwargs):
        # We generally do NOT continue flow here if it's an "End" node,
        # but the original had output ports. If we want to allow pass-through:
        self.bridge.set(f"{self.node_id}_ActivePorts", [], self.name)
        return True
