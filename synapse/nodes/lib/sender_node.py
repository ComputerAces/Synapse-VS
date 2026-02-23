from synapse.core.super_node import SuperNode
from synapse.nodes.registry import NodeRegistry
from synapse.core.types import DataType

@NodeRegistry.register("Sender", "Logic")
class SenderNode(SuperNode):
    """
    Broadcasts data across the graph using a specific 'Tag'.
    
    Acts as a wireless transmitter. Data sent to this node can be 
    retrieved by 'Receiver' nodes using the same 'Tag'. Supports 
    dynamic inputs which are bundled into the broadcast payload.
    
    Inputs:
    - Flow: Trigger the broadcast.
    - Tag: The unique identifier for the communication channel.
    - Data: The primary payload to send.
    
    Outputs:
    - None (Ends execution branch or sinks pulse).
    """
    version = "2.1.0"
    allow_dynamic_inputs = True

    def __init__(self, node_id, name, bridge):
        super().__init__(node_id, name, bridge)
        self.is_native = True
        self.properties["Tag"] = "channel_1"
        self.define_schema()
        self.register_handler("Flow", self.broadcast)

    def define_schema(self):
        self.input_schema = {
            "Flow": DataType.FLOW,
            "Tag": DataType.STRING,
            "Data": DataType.ANY
        }
        self.output_schema = {}

    def broadcast(self, Tag=None, Data=None, **kwargs):
        tag = Tag or self.properties.get("Tag", "channel_1")
        
        # Bundle ALL inputs
        # kwargs contains dynamic inputs (e.g. "MyVar"=123)
        # Data is the default optional one.
        payload = {}
        if Data is not None: payload["Data"] = Data
        payload.update(kwargs)
        
        # Remove "Flow" if present (engine usually filters it, but just in case)
        payload.pop("Flow", None)
        
        key = f"__WIRELESS_{tag}__"
        self.bridge.set(key, payload, self.name)
        
        print(f"[{self.name}] Broadcasting on '{tag}': {payload}")
        
        # No ActivePorts to set for flow continuation? 
        # Sender usually ends the branch or continues? 
        # Original didn't output Flow. It returned "True" which usually means success.
        # But if it has no output flow port, the execution stops here.
