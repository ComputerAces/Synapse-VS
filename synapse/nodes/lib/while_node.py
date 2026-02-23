from synapse.nodes.lib.loop_node import LoopNode
from synapse.nodes.registry import NodeRegistry
from synapse.core.types import DataType

@NodeRegistry.register("While Node", "Logic/Control Flow")
class WhileNode(LoopNode):
    """
    Repeatedly executes a block of code as long as a boolean condition remains true.
    
    Inputs:
    - Flow: Start the while loop evaluation.
    - Continue: Trigger the next check of the loop.
    - Break: Immediately terminate the loop.
    - Condition: A boolean value determining if the loop should continue.
    
    Outputs:
    - Flow: Pulse triggered after the loop finishes.
    - Body: Pulse triggered for each iteration while the condition is met.
    - Index: The current iteration count (0-based).
    """
    version = "2.1.0"

    def __init__(self, node_id, name, bridge):
        super().__init__(node_id, name, bridge)
        self.is_native = True
        self.properties["Condition"] = True

    def define_schema(self):
        super().define_schema()
        self.input_schema["Condition"] = DataType.BOOLEAN

    def _check_condition(self, index, **kwargs):
        condition = kwargs.get("Condition")
        if condition is None:
            condition = self.properties.get("Condition", True)
            
        return bool(condition), None
