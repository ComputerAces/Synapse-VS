from synapse.core.super_node import SuperNode
from synapse.nodes.registry import NodeRegistry
from synapse.core.types import DataType

@NodeRegistry.register("Trigger", "Flow/Triggers")
class TriggerNode(SuperNode):
    """
    Sets a persistent signal (Tag) that can be checked or used to release other branches.
    
    This node acts like a digital latch. When triggered via 'Flow', it sets the state 
    associated with 'Tag' to True. This state remains until manually deactivated via 
    the 'Stop' input or an 'Exit Trigger' node.
    
    Inputs:
    - Flow: Set the trigger state to True.
    - Stop: Deactivate the trigger (Set state to False).
    - Tag: Unique identifier for this trigger state.
    
    Outputs:
    - Flow: Pulse triggered after activation.
    """
    version = "2.1.0"

    def __init__(self, node_id, name, bridge):
        super().__init__(node_id, name, bridge)
        self.is_native = True
        self.properties["Tag"] = ""
        self.define_schema()
        self.register_handler("Flow", self.activate_trigger)
        self.register_handler("Stop", self.deactivate_trigger)

    def define_schema(self):
        self.input_schema = {
            "Flow": DataType.FLOW,
            "Stop": DataType.FLOW,
            "Tag": DataType.STRING
        }
        self.output_schema = {
            "Flow": DataType.FLOW
        }

    def activate_trigger(self, Tag=None, **kwargs):
        Tag = Tag if Tag is not None else kwargs.get("Tag") or self.properties.get("Tag", "")
        tag_key = f"TriggerState_{Tag}" if Tag else f"TriggerState_{self.node_id}"
        
        self.bridge.set(tag_key, True, self.name)
        self.bridge.set(f"{self.node_id}_Style", "PulsingYellow", self.name)
        self.logger.info(f"Trigger '{Tag or self.node_id}' activated.")
        self.bridge.set(f"{self.node_id}_ActivePorts", ["Flow"], self.name)
        return True

    def deactivate_trigger(self, Tag=None, **kwargs):
        Tag = Tag if Tag is not None else kwargs.get("Tag") or self.properties.get("Tag", "")
        tag_key = f"TriggerState_{Tag}" if Tag else f"TriggerState_{self.node_id}"
        
        self.bridge.set(tag_key, False, self.name)
        self.bridge.set(f"{self.node_id}_Style", "Normal", self.name)
        self.logger.info(f"Trigger '{Tag or self.node_id}' deactivated.")
        return True # Stop flow on stop? Or just return? The trigger node continues on Flow, not Stop.


@NodeRegistry.register("Exit Trigger", "Flow/Triggers")
class ExitTriggerNode(SuperNode):
    """
    Deactivates a persistent signal (Tag) set by a 'Trigger' node.
    
    When flow reaches this node, the state associated with the specified 'Tag' 
    is set to False. This can be used to stop execution branches or reset latches.
    
    Inputs:
    - Flow: Trigger the deactivation signal.
    - Tag: The unique identifier of the trigger to deactivate.
    
    Outputs:
    - Flow: Pulse triggered after the signal is dispatched.
    """
    version = "2.1.0"

    def __init__(self, node_id, name, bridge):
        super().__init__(node_id, name, bridge)
        self.is_native = True
        self.properties["Tag"] = ""
        self.define_schema()
        self.register_handler("Flow", self.signal_exit)

    def define_schema(self):
        self.input_schema = {
            "Flow": DataType.FLOW,
            "Tag": DataType.STRING
        }
        self.output_schema = {
            "Flow": DataType.FLOW
        }

    def signal_exit(self, Tag=None, **kwargs):
        # Fallback to properties
        Tag = Tag if Tag is not None else kwargs.get("Tag") or self.properties.get("Tag", "")
        if Tag:
             tag_key = f"TriggerState_{Tag}"
             self.bridge.set(tag_key, False, self.name)
             self.logger.info(f"Signaled exit for Trigger '{Tag}'.")
        
        self.bridge.set(f"{self.node_id}_ActivePorts", ["Flow"], self.name)
        return True
