from synapse.core.super_node import SuperNode
from synapse.nodes.registry import NodeRegistry
from synapse.core.types import DataType
import time

@NodeRegistry.register("Wait", "Flow/Wait")
class WaitNode(SuperNode):
    """
    Suspends the execution of the current branch for a specified duration.
    
    This node is non-blocking to other parallel branches. It returns a signal 
    tells the Execution Engine to resume this specific branch after the 
    'Milliseconds' have elapsed.
    
    Inputs:
    - Flow: Trigger to begin the waiting period.
    - Milliseconds: The duration to wait (1000ms = 1 second).
    
    Outputs:
    - Flow: Pulse triggered after the timer expires.
    """
    version = "2.1.0"

    def __init__(self, node_id, name, bridge):
        super().__init__(node_id, name, bridge)
        self.is_native = True
        self.properties["Milliseconds"] = 1000
        
        self.define_schema()
        self.register_handlers()

    def register_handlers(self):
        self.register_handler("Flow", self.do_work)

    def define_schema(self):
        self.input_schema = {
            "Flow": DataType.FLOW,
            "Milliseconds": DataType.INTEGER
        }
        self.output_schema = {
            "Flow": DataType.FLOW
        }

    def do_work(self, **kwargs):
        Milliseconds = kwargs.get("Milliseconds")
        
        # Fallback to properties
        ms = int(Milliseconds) if Milliseconds is not None else int(self.properties.get("Milliseconds", 1000))
        
        # Return special signal to the Flow Controller to handle non-blocking delay
        return ("_YSWAIT", ms, True)

@NodeRegistry.register("Throttle", "Flow/Wait")
class ThrottleNode(SuperNode):
    """
    Delays execution of the flow to prevent rapid repeated triggers.
    
    Similar to a wait, but specifically used to 'throttle' processes that 
    might otherwise run too fast or too often. It accepts a delay in milliseconds.
    
    Inputs:
    - Flow: execution trigger.
    - Delay MS: Duration of the delay in milliseconds.
    
    Outputs:
    - Flow: Triggered after the delay is complete.
    """
    version = "2.1.0"

    def __init__(self, node_id, name, bridge):
        super().__init__(node_id, name, bridge)
        self.is_native = True
        self.properties["Delay MS"] = 0
        
        self.define_schema()
        self.register_handlers()

    def register_handlers(self):
        self.register_handler("Flow", self.do_work)

    def define_schema(self):
        self.input_schema = {
            "Flow": DataType.FLOW,
            "Delay MS": DataType.INTEGER
        }
        self.output_schema = {
            "Flow": DataType.FLOW
        }

    def do_work(self, **kwargs):
        delay_ms_arg = kwargs.get("Delay MS")
        if delay_ms_arg is None:
            delay_ms = int(self.properties.get("Delay MS", 0))
        else:
            try:
                 delay_ms = abs(int(delay_ms_arg))
            except:
                 delay_ms = 0

        if delay_ms > 0:
            return ("_YSWAIT", delay_ms)
            
        self.bridge.set(f"{self.node_id}_ActivePorts", ["Flow"], self.name)
        return True


@NodeRegistry.register("Yield", "Flow/Wait")
class YieldNode(SuperNode):
    """
    Pauses execution of the 'Flow' branch until a separate 'Trigger' pulse is received.
    
    This is useful for synchronization between asynchronous branches. If the 'Trigger' 
    arrives before the 'Flow' reaches this node, the pulse will pass through 
    instantly when it arrives.
    
    Inputs:
    - Flow: The primary execution branch to be paused.
    - Trigger: The signal required to release the paused 'Flow'.
    
    Outputs:
    - Flow: The original 'Flow' pulse, released once 'Trigger' is received.
    """
    version = "2.1.0"

    def __init__(self, node_id, name, bridge):
        super().__init__(node_id, name, bridge)
        self.is_native = True
        self.define_schema()
        self.register_handlers()

    def register_handlers(self):
        self.register_handler("Flow", self.on_flow)
        self.register_handler("Trigger", self.on_trigger)

    def define_schema(self):
        self.input_schema = {
            "Flow": DataType.FLOW,
            "Trigger": DataType.FLOW
        }
        self.output_schema = {
            "Flow": DataType.FLOW
        }

    def on_flow(self, **kwargs):
        # Check if we were already triggered early by another branch
        early_trigger = self.bridge.get(f"{self.node_id}_early_trigger")
        if early_trigger:
            self.bridge.set(f"{self.node_id}_early_trigger", False, self.name)
            self.bridge.set(f"{self.node_id}_ActivePorts", ["Flow"], self.name)
            return True

        # Otherwise, we wait. By not setting _ActivePorts, the Engine halts this branch's pulse.
        self.bridge.set(f"{self.node_id}_is_yielding", True, self.name)
        return True

    def on_trigger(self, **kwargs):
        # Check if the Flow is currently parked and waiting
        is_yielding = self.bridge.get(f"{self.node_id}_is_yielding")
        if is_yielding:
            self.bridge.set(f"{self.node_id}_is_yielding", False, self.name)
            
            # Release the hold by activating the output port
            self.bridge.set(f"{self.node_id}_ActivePorts", ["Flow"], self.name)
            return True
        else:
            # The trigger arrived before the Flow. Arm it to pass through instantly.
            self.bridge.set(f"{self.node_id}_early_trigger", True, self.name)
            return True