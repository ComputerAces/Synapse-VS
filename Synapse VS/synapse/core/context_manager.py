from synapse.utils.logger import setup_logger

class ContextManager:
    """
    Manages the Execution Stack and Error Handling (Try/Catch scopes).
    """
    def __init__(self, bridge, initial_stack=None):
        self.logger = setup_logger("ContextManager")
        self.bridge = bridge
        self.initial_stack = initial_stack or []
        self.error_mapping = {
            "ZeroDivisionError": 1,
            "ValueError": 2,
            "TypeError": 3,
            "KeyError": 4,
            "IndexError": 5,
            "FileNotFoundError": 6,
            "PermissionError": 7,
            "RuntimeError": 8
        }

    def update_stack(self, node, current_stack, trigger_port="Flow"):
        """
        Returns the new stack based on node type.
        """
        node_type = type(node).__name__
        next_stack = list(current_stack)
        
        # 1. Error Handling (Try/Catch)
        if "TryNode" in node_type:
            next_stack.append(node.node_id)
        elif "EndTryNode" in node_type:
            if next_stack:
                next_stack.pop()
        
        # 2. Provider Scopes
        # We check both class name and inheritance/method presence
        is_provider = "ProviderNode" in node_type or hasattr(node, "register_provider_context")
        
        if is_provider:
            # Special Case: Start Node (Flow Provider)
            # Get Provider Type
            provider_type = node.register_provider_context() if hasattr(node, "register_provider_context") else "Generic"
            
            # 1. Flow Provider (Start Node) - Root Scope
            if provider_type == "Flow Provider" and trigger_port == "Flow":
                 if node.node_id not in next_stack:
                     next_stack.append(node.node_id)
            
            # 2. Standard Provider Scopes
            elif trigger_port == "Provider Flow":
                # Enter Scope
                if node.node_id not in next_stack:
                    next_stack.append(node.node_id)
            elif trigger_port == "Provider End":
                # Exit Scope
                if next_stack and next_stack[-1] == node.node_id:
                    next_stack.pop()
        
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

        # Find handler
        handler_id = context_stack[-1]
        self.logger.warning(f"Caught by TryNode {handler_id}")
        
        # Set Error Data
        error_name = type(error).__name__
        error_code = self.error_mapping.get(error_name, 999)
        
        self.bridge.set(f"{handler_id}_FailedNode", failing_node.name, "Engine")
        self.bridge.set(f"{handler_id}_ErrorCode", error_code, "Engine")
        
        # Determine wires from Handler.Catch
        catch_wires = [
            w for w in wires 
            if w["from_node"] == handler_id and w["from_port"] == "Catch"
        ]
        
        # Catch runs in parent context
        parent_stack = context_stack[:-1]
        
        return handler_id, parent_stack, catch_wires
