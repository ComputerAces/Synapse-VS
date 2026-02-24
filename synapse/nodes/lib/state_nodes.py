from synapse.core.super_node import SuperNode
from synapse.nodes.registry import NodeRegistry
from synapse.core.types import DataType

@NodeRegistry.register("User Activity", "System/State")
class UserActivityNode(SuperNode):
    """
    Outputs mouse and keyboard idle counters from the engine's ActivityTracker.
    
    The engine runs a background thread that increments idle counters every 250ms.
    When the mouse moves, its counter resets to 0. When a key is pressed, its 
    counter resets to 0. Each counter is independent.
    
    Inputs:
    - Flow: Trigger a read of current idle counters.
    
    Outputs:
    - Flow: Always triggered after read.
    - User Activity: Boolean — True if either counter is 0 (recent activity).
    - Mouse Idle Time: Milliseconds since last mouse movement (resets to 0 on move).
    - Keyboard Idle Time: Milliseconds since last key press (resets to 0 on press).
    """
    version = "2.4.0"

    def __init__(self, node_id, name, bridge):
        super().__init__(node_id, name, bridge)
        
        # Migration: Remove dead properties and ports from prior versions
        dead_properties = ["Timeout_MS", "Timeout MS", "Last Data"]
        dead_ports = ["Active Flow", "Idle Flow", "Idle Time", "Activity Data"]
        migrated = False

        for dp in dead_properties:
            if dp in self.properties:
                del self.properties[dp]
                migrated = True

        for port_name in dead_ports:
            for port in list(getattr(self, 'outputs', [])):
                if port.name == port_name:
                    self.outputs.remove(port)
                    migrated = True

        if migrated:
            self.logger.info(f"[Migration] User Activity node '{name}' updated to v{self.version}.")

        self.define_schema()
        self.register_handler("Flow", self.do_work)

    def define_schema(self):
        self.input_schema = {
            "Flow": DataType.FLOW,
        }
        self.output_schema = {
            "Flow": DataType.FLOW,
            "User Activity": DataType.BOOLEAN,
            "Mouse Idle Time": DataType.NUMBER,
            "Keyboard Idle Time": DataType.NUMBER
        }

    def do_work(self, **kwargs):
        # Global singleton — works in any process, reads OS APIs directly
        from synapse.core.activity_tracker import get_tracker
        tracker = get_tracker()
        
        mouse_idle = tracker.mouse_idle_ms
        keyboard_idle = tracker.keyboard_idle_ms
        
        # Active if either counter is at zero (just had input)
        is_active = mouse_idle == 0.0 or keyboard_idle == 0.0
        
        self.bridge.set(f"{self.node_id}_User Activity", 1 if is_active else 0, self.name)
        self.bridge.set(f"{self.node_id}_Mouse Idle Time", mouse_idle, self.name)
        self.bridge.set(f"{self.node_id}_Keyboard Idle Time", keyboard_idle, self.name)
        self.bridge.set(f"{self.node_id}_ActivePorts", ["Flow"], self.name)
        return True
