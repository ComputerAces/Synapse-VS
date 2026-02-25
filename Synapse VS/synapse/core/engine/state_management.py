from synapse.utils.logger import setup_logger

logger = setup_logger("SynapseEngine")

class StateMixin:
    """
    Handles Time-Travel (State Recording/Restoration) for the Execution Engine.
    """
    def _record_state(self):
        """Snapshots current state for Time-Travel."""
        if self._skip_record:
            self._skip_record = False
            return
            
        # [OPTIMIZATION] Only record if:
        # 1. This is the top-level graph (don't tax subgraphs)
        # 2. Back Trace is explicitly enabled in the bridge
        if self.parent_bridge:
            return
            
        if not self.bridge.get("_SYSTEM_BACK_TRACE_ENABLED"):
            # Clear history if disabled to free memory
            if self.history: self.history.clear()
            return

        # Limit history size (e.g. 50 steps)
        if len(self.history) > 50:
            self.history.pop(0)
            
        state = {
            "bridge": self.bridge.export_state(),
            "flow": self.flow.export_state()
        }
        self.history.append(state)

    def _step_back(self):
        """Reverts to previous state."""
        if len(self.history) < 2:
            logger.warning("Cannot Step Back: History empty or at start.")
            return
            
        # Pop current state (discard)
        self.history.pop()
        
        # Restore previous
        prev = self.history[-1]
        self.bridge.import_state(prev["bridge"])
        self.flow.import_state(prev["flow"])
        
        self._skip_record = True # Don't re-record the state we just restored
        logger.info("Stepped Back.")
