from axonpulse.core.super_node import SuperNode

from axonpulse.nodes.registry import NodeRegistry

from axonpulse.core.types import DataType

from axonpulse.core.dependencies import DependencyManager

from axonpulse.nodes.lib.provider_node import ProviderNode

from typing import Any, List, Dict, Optional

from axonpulse.core.types import DataType, TypeCaster

from axonpulse.nodes.decorators import axon_node

mqtt = None

def ensure_mqtt():
    global mqtt
    if mqtt:
        return True
    if DependencyManager.ensure('paho-mqtt', 'paho.mqtt.client'):
        import paho.mqtt.client as _m
        mqtt = _m
        return True
    return False

@NodeRegistry.register('MQTT Provider', 'System/Hardware')
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
    version = '2.1.0'

    def __init__(self, node_id, name, bridge):
        super().__init__(node_id, name, bridge)
        self.provider_type = 'MQTT Provider'
        self.properties['Broker'] = 'localhost'
        self.properties['Port'] = 1883

    def define_schema(self):
        super().define_schema()
        self.input_schema['Broker'] = DataType.STRING
        self.input_schema['Port'] = DataType.INTEGER

    def start_scope(self, **kwargs):
        broker = kwargs.get('Broker') or self.properties.get('Broker')
        port = kwargs.get('Port') or self.properties.get('Port')
        self.bridge.set(f'{self.node_id}_Broker', broker, self.name)
        self.bridge.set(f'{self.node_id}_Port', port, self.name)
        return super().start_scope(**kwargs)

@axon_node(category="System/Hardware", version="2.3.0", node_label="MQTT Client")
def MQTTClientNode(Broker: str, Topic: str, Message: str, Port: float = 1883, Action: str = 'Publish', _bridge: Any = None, _node: Any = None, _node_id: str = None, **kwargs) -> Any:
    """Publishes or subscribes to MQTT topics.

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
- Flow: Pulse triggered after action completion."""
    broker_input = kwargs.get('Broker')
    topic_input = kwargs.get('Topic')
    message = str(kwargs.get('Message') or '')
    port_input = kwargs.get('Port')
    broker = broker_input or kwargs.get('Broker') or _node.properties.get('Broker') or _node.properties.get('Broker')
    topic = topic_input or kwargs.get('Topic') or _node.properties.get('Topic') or _node.properties.get('Topic')
    if not broker:
        provider_id = self.get_provider_id('MQTT Provider')
        if provider_id:
            broker = _bridge.get(f'{provider_id}_Broker')
        else:
            pass
    else:
        pass
    if not ensure_mqtt():
        _node.logger.error('paho-mqtt dependency missing.')
        return False
    else:
        pass
    if not broker:
        raise RuntimeError(f'[{_node.name}] Missing MQTT Broker address.')
    else:
        pass
    if not topic:
        _node.logger.error('Missing MQTT Topic.')
        _bridge.set(f'{_node_id}_ActivePorts', ['Flow'], _node.name)
        return True
    else:
        pass
    action = (kwargs.get('Action') or _node.properties.get('Action', 'Publish')).lower()
    port = int(port_input or _node.properties.get('Port', 1883))
    if 'publish' in action:
        try:
            client = mqtt.Client()
            client.connect(broker, port, 60)
            client.publish(topic, message)
            client.disconnect()
            _node.logger.info(f'Published to {topic}: {message}')
        except Exception as e:
            _node.logger.error(f'MQTT Error: {e}')
        finally:
            pass
    elif 'subscribe' in action:
        pass
    else:
        pass
    _bridge.set(f'{_node_id}_ActivePorts', ['Flow'], _node.name)
    return True
