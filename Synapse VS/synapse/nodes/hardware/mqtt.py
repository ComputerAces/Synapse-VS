from synapse.core.super_node import SuperNode
from synapse.nodes.registry import NodeRegistry
from synapse.core.types import DataType
from synapse.core.dependencies import DependencyManager
from synapse.nodes.lib.provider_node import ProviderNode

# Lazy Globals
mqtt = None

def ensure_mqtt():
    global mqtt
    if mqtt: return True
    if DependencyManager.ensure("paho-mqtt", "paho.mqtt.client"):
        import paho.mqtt.client as _m; mqtt = _m; return True
    return False

@NodeRegistry.register("MQTT Provider", "System/Hardware")
class MQTTProviderNode(ProviderNode):
    """
    Registers the MQTT broker connection for the graph session.
    
    Initializes a provider context with broker address and port, allowing 
    'MQTT Client' nodes to communicate with the broker without manual 
    configuration for each node.
    
    Inputs:
    - Flow: Trigger the provider initialization.
    - Broker: The MQTT broker hostname or IP address.
    - Port: The broker's connection port (default 1883).
    
    Outputs:
    - Done: Pulse triggered once the provider settings are registered.
    """
    version = "2.1.0"

    def __init__(self, node_id, name, bridge):
        super().__init__(node_id, name, bridge)
        self.provider_type = "MQTT Provider"
        self.properties["Broker"] = "localhost"
        self.properties["Port"] = 1883

    def define_schema(self):
        super().define_schema()
        self.input_schema["Broker"] = DataType.STRING
        self.input_schema["Port"] = DataType.INTEGER

    def start_scope(self, **kwargs):
        broker = kwargs.get("Broker") or self.properties.get("Broker")
        port = kwargs.get("Port") or self.properties.get("Port")
        
        self.bridge.set(f"{self.node_id}_Broker", broker, self.name)
        self.bridge.set(f"{self.node_id}_Port", port, self.name)
        
        return super().start_scope(**kwargs)


@NodeRegistry.register("MQTT Client", "System/Hardware")
class MQTTClientNode(SuperNode):
    """
    Publishes or subscribes to MQTT topics.
    
    Communicates with an MQTT broker registered by an 'MQTT Provider'. 
    Supports publishing text payloads to specific topics.
    
    Inputs:
    - Flow: Trigger the action.
    - Broker: Optional override for the broker address.
    - Topic: The target topic to interact with.
    - Message: The payload to publish.
    - Port: Connection port (if not using provider defaults).
    - Action: The operation to perform ('Publish', 'Subscribe').
    
    Outputs:
    - Flow: Pulse triggered after action completion.
    """
    version = "2.1.0"

    def __init__(self, node_id, name, bridge):
        super().__init__(node_id, name, bridge)
        self.is_native = True
        self.is_service = True 
        self.properties["Action"] = "Publish" 
        self.properties["Port"] = 1883
        self._client = None
        self.define_schema()
        self.register_handlers()

    def register_handlers(self):
        self.register_handler("Flow", self.do_work)

    def define_schema(self):
        self.input_schema = {
            "Flow": DataType.FLOW,
            "Broker": DataType.STRING,
            "Topic": DataType.STRING,
            "Message": DataType.STRING,
            "Port": DataType.INTEGER,
            "Action": DataType.STRING
        }
        self.output_schema = {
            "Flow": DataType.FLOW
        }

    def do_work(self, **kwargs):
        broker_input = kwargs.get("Broker")
        topic_input = kwargs.get("Topic")
        message = str(kwargs.get("Message") or "")
        port_input = kwargs.get("Port")

        broker = broker_input or kwargs.get("Broker") or self.properties.get("Broker") or self.properties.get("Broker")
        topic = topic_input or kwargs.get("Topic") or self.properties.get("Topic") or self.properties.get("Topic")

        if not broker:
            provider_id = self.get_provider_id("MQTT Provider")
            if provider_id: broker = self.bridge.get(f"{provider_id}_Broker")
        
        if not ensure_mqtt():
             self.logger.error("paho-mqtt dependency missing.")
             return False

        if not broker:
             raise RuntimeError(f"[{self.name}] Missing MQTT Broker address.")
             
        if not topic:
             self.logger.error("Missing MQTT Topic.")
             self.bridge.set(f"{self.node_id}_ActivePorts", ["Flow"], self.name)
             return True
        
        action = (kwargs.get("Action") or self.properties.get("Action", "Publish")).lower()
        port = int(port_input or self.properties.get("Port", 1883))

        if "publish" in action:
            try:
                client = mqtt.Client()
                client.connect(broker, port, 60)
                client.publish(topic, message)
                client.disconnect()
                self.logger.info(f"Published to {topic}: {message}")
            except Exception as e:
                self.logger.error(f"MQTT Error: {e}")
        elif "subscribe" in action:
            pass
            
        self.bridge.set(f"{self.node_id}_ActivePorts", ["Flow"], self.name)
        return True
