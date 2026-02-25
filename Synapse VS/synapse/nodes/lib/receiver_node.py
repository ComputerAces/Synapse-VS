from synapse.core.super_node import SuperNode
from synapse.nodes.registry import NodeRegistry
from synapse.core.types import DataType

@NodeRegistry.register("Receiver", "Logic")
class ReceiverNode(SuperNode):
    """
    Listens for data broadcasted across the graph using a specific 'Tag'.
    
    Acts as a wireless receiver for values sent by 'Sender' nodes. When 
    triggered, it retrieves the payload associated with the 'Tag' from 
    the engine's global memory.
    
    Inputs:
    - Flow: Trigger the retrieval.
    - Tag: The unique identifier for the communication channel.
    
    Outputs:
    - Flow: Triggered after data is retrieved.
    - Data: The primary payload (if single value) or the full dictionary.
    """
    version = "2.1.0"
    allow_dynamic_outputs = True

    def __init__(self, node_id, name, bridge):
        super().__init__(node_id, name, bridge)
        self.is_native = True
        self.properties["Tag"] = "channel_1"
        self.define_schema()
        self.register_handlers()

    def register_handlers(self):
        self.register_handler("trigger", self.receive_data)

    def define_schema(self):
        self.input_schema = {
            "Flow": DataType.FLOW,
            "Tag": DataType.STRING
        }
        self.output_schema = {
            "Flow": DataType.FLOW,
            "Data": DataType.ANY
        }

    def receive_data(self, Tag=None, **kwargs):
        tag = Tag or self.properties.get("Tag", "channel_1")
        
        # Retrieve data
        key = f"__WIRELESS_{tag}__"
        payload = self.bridge.get(key)
        
        if not isinstance(payload, dict):
            payload = {"Data": payload}
            
        if payload:
            for k, v in payload.items():
                self.bridge.set(f"{self.node_id}_{k}", v, self.name)
        
        self.bridge.set(f"{self.node_id}_ActivePorts", ["Flow"], self.name)
        return True
