from synapse.utils.logger import setup_logger
from synapse.core.data import ErrorObject

logger = setup_logger("SynapseEngine")

class DebugMixin:
    """
    Handles Debugging, Panics, and Error Routing.
    """
    def _handle_panic(self, error, failing_node, context_stack, start_node_id, inputs=None):
        """
        Routes unhandled exceptions to the Start Node's 'Panic' port if wired.
        Returns True if a Panic handler was found and invoked, False otherwise.
        """
        # Store error details on bridge for LastErrorNode to retrieve
        error_name = type(error).__name__
        error_code = self.context_manager.error_mapping.get(error_name, 999)
        
        # [panic] Create Complex Error Object
        # We try to get project name from bridge or node?
        project_name = self.bridge.get("_META_PROJECT_NAME") or "Unknown Project"
        
        error_obj = ErrorObject(
            project_name=project_name,
            node_name=failing_node.name,
            inputs=inputs,
            error_details=str(error)
        )
        
        self.bridge.bubble_set("_SYSTEM_LAST_ERROR_OBJECT", error_obj, "Engine")
        
        self.bridge.bubble_set("_SYSTEM_LAST_ERROR_CODE", error_code, "Engine")
        self.bridge.bubble_set("_SYSTEM_LAST_ERROR_MESSAGE", str(error), "Engine")
        self.bridge.bubble_set("_SYSTEM_LAST_ERROR_NODE", failing_node.node_id, "Engine")
        self.bridge.bubble_set("_SYSTEM_LAST_ERROR_NODE_NAME", failing_node.name, "Engine")
        
        # Explicit Console Error Output
        print("\n" + "="*60)
        print(f" [CRITICAL ERROR] {error_name} in '{failing_node.name}'")
        print(f" MESSAGE: {str(error)}")
        print("="*60 + "\n", flush=True)
        
        # Find wires from Start Node's Error Flow port (Case-Insensitive match)
        panic_wires = [
            w for w in self.wires
            if w["from_node"] == start_node_id and str(w.get("from_port", "")).lower() in ["error flow", "error", "panic"]
        ]
        
        if panic_wires:
            print(f"[DEBUG] [PANIC] Routing to Error Flow handler from Start Node (ID: {start_node_id})...", flush=True)
            self.bridge.set("_PANICKED", True, "Engine") # Signal that we entered panic mode
            for w in panic_wires:
                print(f"[DEBUG] [PANIC] -> {w['to_node']}:{w['to_port']}", flush=True)
                self.flow.push(w["to_node"], [], w["to_port"])
                # Panic pulses run in ROOT scope
                self._increment_scope_count([], 1)
            return True
        else:
            print(f"[DEBUG] [PANIC] No Error Flow wired from Start Node (ID: {start_node_id}). Raising error.", flush=True)
            logger.warning(f"UNHANDLED PANIC in {failing_node.name}: {error}")
            return False
