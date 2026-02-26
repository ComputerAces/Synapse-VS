import uuid
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
    - End: Forcefully terminates the loop and all its active parallel branches.
    
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
        self.register_handler("End", self.do_work)

    def define_schema(self):
        self.input_schema = {
            "Flow": DataType.FLOW,
            "Continue": DataType.FLOW,
            "Break": DataType.FLOW,
            "End": DataType.FLOW
        }
        self.output_schema = {
            "Flow": DataType.FLOW,
            "Body": DataType.FLOW,
            "Index": DataType.INTEGER
        }

    def do_work(self, **kwargs):
        _trigger = kwargs.get("_trigger", "Flow")
        # [FIX] Use passed-in context for thread safety
        curr_context = kwargs.get("_context_stack", getattr(self, "context_stack", []))
        
        # State Keys
        active_key = f"{self.node_id}_loop_active"
        index_key = f"{self.node_id}_internal_index"
        scope_key = f"{self.node_id}_instance_scope"
        base_stack_key = f"{self.node_id}_base_stack"

        # 1. Handle Break / End
        if _trigger == "Break" or _trigger == "End":
            self.logger.info(f"Loop {'Ended' if _trigger == 'End' else 'Broken'}.")
            
            # Kill split flows for this specific loop instance if 'End'
            if _trigger == "End":
                active_scope = self.bridge.get(scope_key)
                if active_scope:
                    self.bridge.set(f"SYNAPSE_CANCEL_SCOPE_{active_scope}", True, self.name)
            
            self.finish_loop()
            return True

        # 2. Determine if starting or continuing
        current_index = 0
        if _trigger == "Flow":
            self.logger.info("Loop starting.")
            
            # Create a unique instance scope for THIS loop run
            instance_id = f"LO_{self.node_id[:8]}_{uuid.uuid4().hex[:6]}"
            self.bridge.set(scope_key, instance_id, self.name)
            
            # Store STABLE base stack for iteration pulses
            self.bridge.set(base_stack_key, curr_context, self.name)
            
            self.bridge.set(active_key, True, self.name)
            self.bridge.set(index_key, 0, self.name)
            self._on_loop_start(**kwargs)
            current_index = 0
        else:
            # Continue path
            if not self.bridge.get(active_key):
                return True
            # Atomic increment for "multi-while" processing
            current_index = self.bridge.increment(index_key, 1, scope_id=None)

        # 3. Check condition (implemented by subclasses)
        should_continue, item = self._check_condition(current_index, **kwargs)

        # Retrieve base stack for cleanup and body pulses
        base_stack = self.bridge.get(base_stack_key) or curr_context

        if should_continue:
            # Set iteration data
            self.bridge.set(f"{self.node_id}_Index", current_index, self.name)
            if item is not None:
                self.bridge.set(f"{self.node_id}_Item", item, self.name)
            
            # [FIX] Use STABLE base_stack to avoid recursive nesting
            active_scope = self.bridge.get(scope_key)
            if active_scope:
                overrides = { "Body": base_stack + [active_scope] }
                self.bridge.set(f"{self.node_id}_StackOverrides", overrides, self.name)
            
            # Pulse Body
            self.bridge.set(f"{self.node_id}_ActivePorts", ["Body"], self.name)
        else:
            self.finish_loop(base_stack)
            
        return True

    def finish_loop(self, base_stack=None):
        active_key = f"{self.node_id}_loop_active"
        index_key = f"{self.node_id}_internal_index"
        scope_key = f"{self.node_id}_instance_scope"
        base_stack_key = f"{self.node_id}_base_stack"
        
        self.bridge.set(active_key, False, self.name)
        self.bridge.set(index_key, None, self.name)
        self.bridge.set(scope_key, None, self.name)
        self.bridge.set(base_stack_key, None, self.name)
        
        # Clear triggers for engine
        self.bridge.set(f"{self.node_id}_StackOverrides", None, self.name)
        
        # [FIX] Completion pulse should return to PARENT context levels
        if base_stack:
            overrides = { "Flow": base_stack }
            self.bridge.set(f"{self.node_id}_StackOverrides", overrides, self.name)

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
