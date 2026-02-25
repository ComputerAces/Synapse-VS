from synapse.core.super_node import SuperNode
from synapse.nodes.registry import NodeRegistry
from synapse.core.types import DataType
import os

@NodeRegistry.register("Breakpoint", "Flow/Debug")
class BreakpointNode(SuperNode):
    """
    Temporarily pauses graph execution at this point, allowing manual inspection of state.
    Execution can be resumed by the user through the UI or by deleting the pause signal file.
    Skipped automatically in Headless mode.
    
    Inputs:
    - Flow: Trigger execution to pause here.
    
    Outputs:
    - Flow: Triggered immediately (Engine handles the pause step contextually).
    """
    version = "2.1.0"

    def __init__(self, node_id, name, bridge):
        super().__init__(node_id, name, bridge)
        self.is_native = True
        self.define_schema()
        self.register_handlers()

    def register_handlers(self):
        self.register_handler("Flow", self.pause)
    
    def define_schema(self):
        self.input_schema = {
            "Flow": DataType.FLOW
        }
        self.output_schema = {
            "Flow": DataType.FLOW
        }

    def pause(self, **kwargs):
        # 1. Check Headless
        headless = self.bridge.get("_SYSTEM_HEADLESS")
        if headless:
            self.logger.info("Breakpoint skipped (Headless Mode).")
            self.bridge.set(f"{self.node_id}_ActivePorts", ["Flow"], self.name)
            return True
            
        # 2. Trigger Pause
        pause_file = self.bridge.get("_SYSTEM_PAUSE_FILE")
        if pause_file:
            try:
                # Create the pause file to signal Engine
                with open(pause_file, 'w') as f:
                    f.write(f"BREAKPOINT: {self.name}")
                
                self.logger.warning(f"Breakpoint hit. Engine will pause before next node. Delete '{pause_file}' to resume.")
                
            except Exception as e:
                self.logger.error(f"Failed to set pause file: {e}")
        
        # Continue Flow (Engine handles the pause check before executing next node)
        self.bridge.set(f"{self.node_id}_ActivePorts", ["Flow"], self.name)
        return True
