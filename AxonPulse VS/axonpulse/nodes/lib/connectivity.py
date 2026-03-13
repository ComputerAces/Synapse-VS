import uuid

import json

from axonpulse.core.super_node import SuperNode

from axonpulse.nodes.registry import NodeRegistry

from axonpulse.core.types import DataType

from axonpulse.utils.logger import main_logger as logger

from axonpulse.nodes.lib.provider_node import ProviderNode

from typing import Any, List, Dict, Optional

from axonpulse.core.types import DataType, TypeCaster

from axonpulse.nodes.decorators import axon_node

class ConnectionHandle:
    """
    Protocol-agnostic handle containing connection configuration.
    Passed between Provider nodes and Action nodes.
    """

    def __init__(self, protocol, config):
        self.id = f'conn_{uuid.uuid4().hex[:8]}'
        self.protocol = protocol
        self.config = config

    def __str__(self):
        return f'[{self.protocol} Handle: {self.id}]'

    def __repr__(self):
        return self.__str__()

@NodeRegistry.register('REST Provider', 'Connectivity/Providers')
class RESTProviderNode(ProviderNode):
    """
    Initializes a REST-based connection handle for communicating with web APIs.
    Acts as a configuration provider for Net Request and other connectivity nodes.
    
    Inputs:
    - Flow: Trigger the creation of the connection handle.
    - Base URL: The root URL for the target API (e.g., 'https://api.example.com').
    - Port: The destination port for the connection.
    - Timeout: Request timeout in seconds.
    - AuthStrategy: The authentication method to use (e.g., 'Bearer').
    
    Outputs:
    - Flow: Triggered after handle creation.
    - Handle: A ConnectionHandle object containing the REST configuration.
    """
    version = '2.1.0'
    provider_type = 'REST'

    def __init__(self, node_id, name, bridge):
        super().__init__(node_id, name, bridge)
        self.is_native = True
        self.properties['Base URL'] = ''
        self.properties['Port'] = 80
        self.properties['Timeout'] = 30
        self.properties['AuthStrategy'] = 'Bearer'

    def register_handlers(self):
        super().register_handlers()

    def define_schema(self):
        super().define_schema()
        self.input_schema.update({'Base URL': DataType.STRING, 'Port': DataType.NUMBER, 'Timeout': DataType.NUMBER, 'AuthStrategy': DataType.STRING})
        self.output_schema.update({'Handle': DataType.ANY})

    def start_scope(self, **kwargs):
        base_url = kwargs.get('Base URL') or self.properties.get('Base URL')
        port = kwargs.get('Port') or self.properties.get('Port', 80)
        timeout = kwargs.get('Timeout') or self.properties.get('Timeout', 30)
        auth = kwargs.get('AuthStrategy') or self.properties.get('AuthStrategy', 'None')
        handle = ConnectionHandle('REST', {'base_url': base_url, 'port': port, 'timeout': timeout, 'auth_strategy': auth})
        self.bridge.set(f'{self.node_id}_Handle', handle, self.name)
        return super().start_scope(**kwargs)

@NodeRegistry.register('WebSocket Provider', 'Connectivity/Providers')
class WebSocketProviderNode(ProviderNode):
    """
    Initializes a WebSocket connection handle for real-time bi-directional communication.
    Supports automatic reconnection settings and standard WSS protocols.
    
    Inputs:
    - Flow: Trigger the creation of the connection handle.
    - URL: The full WSS endpoint URL (e.g., 'wss://echo.websocket.org').
    - Reconnect: Toggles automatic reconnection on connection loss.
    
    Outputs:
    - Flow: Triggered after handle creation.
    - Handle: A ConnectionHandle object containing the WebSocket configuration.
    """
    version = '2.1.0'
    provider_type = 'SOCKET'

    def __init__(self, node_id, name, bridge):
        super().__init__(node_id, name, bridge)
        self.is_native = True
        self.properties['URL'] = ''
        self.properties['Reconnect'] = True

    def register_handlers(self):
        super().register_handlers()

    def define_schema(self):
        super().define_schema()
        self.input_schema.update({'URL': DataType.STRING, 'Reconnect': DataType.BOOLEAN})
        self.output_schema.update({'Handle': DataType.ANY})

    def start_scope(self, **kwargs):
        url = kwargs.get('URL') or self.properties.get('URL')
        reconnect = kwargs.get('Reconnect') if kwargs.get('Reconnect') is not None else self.properties.get('Reconnect', True)
        handle = ConnectionHandle('WSS', {'url': url, 'reconnect': reconnect})
        self.bridge.set(f'{self.node_id}_Handle', handle, self.name)
        return super().start_scope(**kwargs)

@NodeRegistry.register('GRPC Provider', 'Connectivity/Providers')
class GRPCProviderNode(ProviderNode):
    """
    Initializes a gRPC connection handle for high-performance RPC communication.
    Sets up the target server address for protocol buffer-based requests.
    
    Inputs:
    - Flow: Trigger the creation of the connection handle.
    - Server: The target host and port (e.g., 'localhost:50051').
    
    Outputs:
    - Flow: Triggered after handle creation.
    - Handle: A ConnectionHandle object containing the gRPC configuration.
    """
    version = '2.1.0'
    provider_type = 'GRPC'

    def __init__(self, node_id, name, bridge):
        super().__init__(node_id, name, bridge)
        self.is_native = True
        self.properties['Server'] = 'localhost:50051'

    def register_handlers(self):
        super().register_handlers()

    def define_schema(self):
        super().define_schema()
        self.input_schema.update({'Server': DataType.STRING})
        self.output_schema.update({'Handle': DataType.ANY})

    def start_scope(self, **kwargs):
        target = kwargs.get('Server') or self.properties.get('Server')
        handle = ConnectionHandle('gRPC', {'target': target})
        self.bridge.set(f'{self.node_id}_Handle', handle, self.name)
        return super().start_scope(**kwargs)

@axon_node(category="Connectivity/Actions", version="2.3.0", node_label="Net Request", outputs=['Error Flow', 'Response', 'Status'])
def NetRequestNode(Method: str, Endpoint: str, Payload: Any, App_ID: str = 'Global', _bridge: Any = None, _node: Any = None, _node_id: str = None, **kwargs) -> Any:
    """Executes a high-level network request using the active Network Provider context.
Supports RESTful APIs and basic gRPC stub calls with identity-based authentication.

Inputs:
- Flow: Trigger the network request.
- Method: The HTTP method to use (GET, POST, etc.).
- Endpoint: The specific API path relative to the Base URL.
- Payload: The data to send (Dictionary for JSON, or raw string/bytes).
- App ID: Optional identifier for retrieving authentication credentials.

Outputs:
- Flow: Triggered after the request completes.
- Error Flow: Triggered if the request fails (network error, timeout).
- Response: The raw text or data returned by the server.
- Status: The numeric HTTP status code (e.g., 200, 404)."""
    method = str(Method or kwargs.get('Method', 'GET')).upper()
    endpoint = str(Endpoint or kwargs.get('Endpoint', ''))
    payload = Payload if Payload is not None else kwargs.get('Payload')
    app_id = kwargs.get('App ID') or _node.properties.get('App ID', 'Global')
    provider_id = self.get_provider_id('Network Provider')
    if not provider_id:
        msg = 'No Network Provider found in scope.'
        _node.logger.error(msg)
        _bridge.set(f'{_node_id}_ActivePorts', ['Error Flow', 'Flow'], _node.name)
    else:
        pass
    base_url = _bridge.get(f'{provider_id}_Base URL')
    proxy = _bridge.get(f'{provider_id}_Proxy')
    headers = _bridge.get(f'{provider_id}_Headers') or {}
    if not base_url:
        msg = 'Network Provider has no Base URL.'
        _node.logger.error(msg)
        _bridge.set(f'{_node_id}_ActivePorts', ['Error Flow', 'Flow'], _node.name)
    else:
        pass
    identity = _bridge.get_identity(app_id)
    auth_headers = headers.copy()
    if identity and identity.auth_payload:
        auth = identity.auth_payload
        if 'bearer_token' in auth:
            auth_headers['Authorization'] = f"Bearer {auth['bearer_token']}"
        elif 'basic_auth' in auth:
            auth_headers['Authorization'] = f"Basic {auth['basic_auth']}"
        else:
            pass
    else:
        pass
    import requests
    url = f"{base_url.rstrip('/')}/{endpoint.lstrip('/')}"
    proxies = {'http': proxy, 'https': proxy} if proxy else None
    try:
        resp = requests.request(method=method, url=url, json=payload if isinstance(payload, dict) else None, data=payload if not isinstance(payload, dict) else None, headers=auth_headers, proxies=proxies, timeout=30)
        _bridge.set(f'{_node_id}_ActivePorts', ['Flow'], _node.name)
    except Exception as e:
        msg = f'Network Request Failed: {e}'
        _node.logger.error(msg)
        _bridge.set(f'{_node_id}_ActivePorts', ['Error Flow', 'Flow'], _node.name)
    finally:
        pass
    return {'Response': msg, 'Response': msg, 'Response': resp.text, 'Status': resp.status_code, 'Response': msg, 'Status': 0}


@axon_node(category="Connectivity/Actions", version="2.3.0", node_label="Net Stream", outputs=['Error Flow'])
def NetStreamNode(Message: Any, App_ID: str, _bridge: Any = None, _node: Any = None, _node_id: str = None, **kwargs) -> Any:
    """Pushes data messages through an established streaming connection in the active Network Provider context.

Inputs:
- Flow: Trigger the message push.
- Message: The data or object to transmit through the stream.

Outputs:
- Flow: Triggered after the message is sent.
- Error Flow: Triggered if the transmission fails."""
    msg = Message if Message is not None else kwargs.get('Message')
    app_id = kwargs.get('App ID') or _node.properties.get('App ID', 'Global')
    provider_id = self.get_provider_id('Network Provider')
    if not provider_id:
        _node.logger.error('No Network Provider found.')
        _bridge.set(f'{_node_id}_ActivePorts', ['Error Flow', 'Flow'], _node.name)
        return True
    else:
        pass
    _node.logger.info(f'Pushing message to stream...')
    _bridge.set(f'{_node_id}_ActivePorts', ['Flow'], _node.name)
    return True


@axon_node(category="Connectivity/Actions", version="2.3.0", node_label="Net Listener", outputs=['Message'])
def NetListenerNode(App_ID: str = 'Global', _bridge: Any = None, _node: Any = None, _node_id: str = None, **kwargs) -> Any:
    """Establishes an event listener on the active Network Provider to capture incoming messages.
Triggers the graph sequence whenever new data is received.

Inputs:
- Flow: Initialize the listener.
- App ID: Optional identifier for isolation/authentication.

Outputs:
- Flow: Triggered every time a new message is received.
- Message: The incoming data payload."""
    _bridge.set(f'{_node_id}_ActivePorts', ['Flow'], _node.name)
    return True
