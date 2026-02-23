from synapse.nodes.lib.loop_node import LoopNode
from synapse.nodes.registry import NodeRegistry
from synapse.core.types import DataType

@NodeRegistry.register("For Node", "Logic/Control Flow")
class ForNode(LoopNode):
    """
    Executes a block of code a specific number of times based on a numeric range.
    
    Inputs:
    - Flow: Initialize the loop and start the first iteration.
    - Continue: Trigger the next iteration of the loop.
    - Break: Immediately terminate the loop.
    - Start: The numeric value to begin counting from.
    - Step: The amount to increment/decrement per iteration.
    - Stop: The target value to compare the index against.
    - CompareType: The operator used to check the stop condition (e.g., <, <=, ==).
    
    Outputs:
    - Flow: Pulse triggered once the loop completes or breaks.
    - Body: Pulse triggered for each iteration while the condition is true.
    - Index: The current numeric value of the counter.
    """
    version = "2.1.0"

    def __init__(self, node_id, name, bridge):
        super().__init__(node_id, name, bridge)
        self.is_native = True
        self.properties["Start"] = 0
        self.properties["Step"] = 1
        self.properties["Stop"] = 10
        self.properties["CompareType"] = "<"

    def define_schema(self):
        super().define_schema()
        self.input_schema["Start"] = DataType.INTEGER
        self.input_schema["Step"] = DataType.INTEGER
        self.input_schema["Stop"] = DataType.INTEGER
        self.input_schema["CompareType"] = DataType.COMPARE

    def _check_condition(self, index, **kwargs):
        # On first iteration (index 0), we use Start.
        # But LoopNode increments index for us.
        # Actually, LoopNode's index is just 0, 1, 2...
        # We need to calculate the REAL numeric index.
        
        def get_val(val, key):
            try:
                if val is not None: return int(float(val))
                return int(float(self.properties.get(key, 0)))
            except: return 0

        start = get_val(kwargs.get("Start"), "Start")
        step = get_val(kwargs.get("Step"), "Step")
        stop = get_val(kwargs.get("Stop"), "Stop")
        op = kwargs.get("CompareType") or self.properties.get("CompareType", "<")

        # Calculate logical value
        logical_value = start + (index * step)
        
        def compare(current, stop_v, operator):
            if operator == "<": return current < stop_v
            if operator == "<=": return current <= stop_v
            if operator == ">": return current > stop_v
            if operator == ">=": return current >= stop_v
            if operator == "==": return current == stop_v
            if operator == "!=": return current != stop_v
            return False

        if compare(logical_value, stop, op):
            return True, logical_value # Return logical_value as the "item" (Index output)
            
        return False, None
