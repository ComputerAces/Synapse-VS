from synapse.core.super_node import SuperNode
from synapse.core.types import DataType

class LoopNode(SuperNode):
    """
    Base class for iteration nodes. Manages the execution flow for 
    repetitive tasks, providing Continue and Break functionality.
    
    Inputs:
    - Flow: Start the loop execution.
    - Continue: Trigger to proceed to the next iteration.
    - Break: Trigger to exit the loop immediately.
    
    Outputs:
    - Flow: Pulse triggered after the loop finishes.
    - Body: Pulse triggered for each iteration of the loop.
    - Index: The current iteration count (0-based).
    """
    
    def __init__(self, node_id, name, bridge):
        super().__init__(node_id, name, bridge)
        self.define_schema()
        self.register_handlers()

    def register_handlers(self):
        self.register_handler("Flow", self.do_work)
        self.register_handler("Continue", self.do_work)
        self.register_handler("Break", self.do_work)

    def define_schema(self):
        self.input_schema = {
            "Flow": DataType.FLOW,
            "Continue": DataType.FLOW,
            "Break": DataType.FLOW
        }
        self.output_schema = {
            "Flow": DataType.FLOW,
            "Body": DataType.FLOW,
            "Index": DataType.INTEGER
        }

    def do_work(self, **kwargs):
        _trigger = kwargs.get("_trigger", "Flow")
        
        # State Keys
        active_key = f"{self.node_id}_loop_active"
        index_key = f"{self.node_id}_internal_index"

        # 1. Handle Break
        if _trigger == "Break":
            self.logger.info("Loop broken.")
            self.finish_loop()
            return True

        # 2. Determine if starting or continuing
        current_index = 0
        if _trigger == "Flow":
            self.logger.info("Loop starting.")
            self.bridge.set(active_key, True, self.name)
            self.bridge.set(index_key, 0, self.name)
            self._on_loop_start(**kwargs)
        else:
            # Continue path
            if not self.bridge.get(active_key):
                return True
            current_index = (self.bridge.get(index_key) or 0) + 1
            self.bridge.set(index_key, current_index, self.name)

        # 3. Check condition (implemented by subclasses)
        should_continue, item = self._check_condition(current_index, **kwargs)

        if should_continue:
            # Set iteration data
            self.bridge.set(f"{self.node_id}_Index", current_index, self.name)
            if item is not None:
                self.bridge.set(f"{self.node_id}_Item", item, self.name)
            
            # Pulse Body
            self.bridge.set(f"{self.node_id}_ActivePorts", ["Body"], self.name)
        else:
            self.finish_loop()
            
        return True

    def finish_loop(self):
        active_key = f"{self.node_id}_loop_active"
        index_key = f"{self.node_id}_internal_index"
        self.bridge.set(active_key, False, self.name)
        self.bridge.set(index_key, None, self.name)
        self.bridge.set(f"{self.node_id}_ActivePorts", ["Flow"], self.name)
        self.logger.info("Loop finished.")

    # --- Hooks for Subclasses ---
    def _on_loop_start(self, **kwargs):
        """Called when Flow is triggered to perform setup."""
        pass

    def _check_condition(self, index, **kwargs):
        """
        Evaluate if another iteration should occur.
        Returns: (bool should_continue, Any current_item)
        """
        return False, None
