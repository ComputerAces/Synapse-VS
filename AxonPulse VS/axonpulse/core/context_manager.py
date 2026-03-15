from axonpulse.utils.logger import setup_logger
from axonpulse.core.error_registry import ErrorRegistry

class ContextManager:
    """
    Manages the Execution Stack and Error Handling (Try/Catch scopes).
    """
    def __init__(self, bridge, initial_stack=None):
        self.logger = setup_logger("ContextManager")
        self.bridge = bridge
        self.error_registry = ErrorRegistry()
        
        # [BOOTSTRAP] Ensure initial stack is in the immutable linked-list format
        # We assume initial_stack is already in the correct format (None or tuple).
        # But if it's a list, we provide a quick fallback (Outer-to-Inner list to Inner-to-Outer tuple).
        if isinstance(initial_stack, list):
             stack = None
             for s_id in initial_stack:
                 stack = (s_id, stack)
             initial_stack = stack
        
        self.initial_stack = initial_stack

    def stack_push(self, stack, node_id):
        """Pushes a node_id onto the immutable stack (linked-list tuple)."""
        return (node_id, stack)

    def stack_pop(self, stack):
        """Pops the top item from the stack. Returns the parent stack."""
        if not stack: return None
        return stack[1]

    def stack_peek(self, stack):
        """Returns the top item (node_id) of the stack."""
        if not stack: return None
        return stack[0]

    def stack_to_list(self, stack):
        """Converts the linked-list tuple back to a Python list (Ordered Outer-to-Inner)."""
        result = []
        curr = stack
        while curr:
            result.append(curr[0])
            curr = curr[1]
        return result[::-1] # Reverse because linked list is Inner-to-Outer

    def stack_from_list(self, items):
        """Converts a Python list to an immutable linked-list tuple."""
        stack = None
        for item in items:
            stack = (item, stack)
        return stack

    def get_stack_depth(self, stack):
        """Returns the number of items in the immutable stack."""
        count = 0
        curr = stack
        while curr:
            count += 1
            curr = curr[1]
        return count

    def update_stack(self, node, current_stack, trigger_port="Flow"):
        """
        Returns the new stack based on node type.
        Stack format: (top_node_id, parent_tuple) or None.
        """
        node_type = type(node).__name__
        next_stack = current_stack
        
        # 1. Error Handling (Try/Catch)
        if "TryNode" in node_type:
            next_stack = self.stack_push(next_stack, node.node_id)
        elif "EndTryNode" in node_type:
            next_stack = self.stack_pop(next_stack)
        
        # 2. Provider Scopes
        is_provider = "ProviderNode" in node_type or hasattr(node, "register_provider_context")
        
        if is_provider:
            provider_type = node.register_provider_context() if hasattr(node, "register_provider_context") else "Generic"
            
            # 1. Flow Provider (Start Node) - Root Scope
            if provider_type == "Flow Provider" and trigger_port == "Flow":
                 # We only push if it's not already at the top (avoid duplicates in weird loopbacks)
                 if self.stack_peek(next_stack) != node.node_id:
                     next_stack = self.stack_push(next_stack, node.node_id)
            
            # 2. Standard Provider Scopes
            elif trigger_port == "Provider Flow":
                if self.stack_peek(next_stack) != node.node_id:
                    next_stack = self.stack_push(next_stack, node.node_id)
            elif trigger_port == "Provider End":
                if self.stack_peek(next_stack) == node.node_id:
                    next_stack = self.stack_pop(next_stack)
        
        return next_stack

    def handle_error(self, error, failing_node, context_stack, wires):
        """
        Bubbles error up the stack. Returns (handler_node_id, parent_stack, catch_port) if caught.
        Returns None if unhandled.
        """
        self.logger.error(f"Error in {failing_node.name}: {error}")
        
        if not context_stack:
            self.logger.critical("Unhandled Exception (No active Try block).")
            return None

        # Find handler (Innermost TryNode)
        handler_id = self.stack_peek(context_stack)
        self.logger.warning(f"Caught by TryNode {handler_id}")
        
        # Set Error Data
        error_name = type(error).__name__
        error_code = self.error_registry.get_code(error_name)
        
        self.bridge.set(f"{handler_id}_FailedNode", failing_node.name, "Engine")
        self.bridge.set(f"{handler_id}_ErrorCode", error_code, "Engine")
        
        # Determine wires from Handler.Catch
        catch_wires = [
            w for w in wires 
            if w["from_node"] == handler_id and w["from_port"] == "Catch"
        ]
        
        # Catch runs in parent context
        parent_stack = self.stack_pop(context_stack)
        
        return handler_id, parent_stack, catch_wires
