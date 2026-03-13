import socket

import threading

import time

from axonpulse.core.super_node import SuperNode

from axonpulse.nodes.registry import NodeRegistry

from axonpulse.core.types import DataType

from axonpulse.nodes.lib.provider_node import ProviderNode

from typing import Any, List, Dict, Optional

from axonpulse.core.types import DataType, TypeCaster

from axonpulse.nodes.decorators import axon_node

_TCP_INSTANCES = {}

def get_tcp(provider_id):
    return _TCP_INSTANCES.get(provider_id)

@NodeRegistry.register('TCP Server Provider', 'Network/TCP')
class TCPServerProvider(ProviderNode):
    """
    Hosts a TCP server and provides connection handles to child nodes.
    
    Inputs:
    - Flow: Start the server and enter scope.
    - Provider End: Pulse to close scope.
    - Host: Interface to bind to (Default: 127.0.0.1).
    - Port: Port to listen on (Default: 6000).
    
    Outputs:
    - Provider Flow: Active while the server is running.
    - Provider ID: Unique ID for this provider.
    - On Connection: Pulse triggered for each new client connection.
    - Client Info: Address of the connected client.
    """
    version = '2.1.0'

    def __init__(self, node_id, name, bridge):
        self.provider_type = 'TCP Provider'
        super().__init__(node_id, name, bridge)
        self.is_native = True
        self.properties['Host'] = '127.0.0.1'
        self.properties['Port'] = 6000
        self._socket = None
        self._running = False

    def define_schema(self):
        super().define_schema()
        self.input_schema['Host'] = DataType.STRING
        self.input_schema['Port'] = DataType.NUMBER
        self.output_schema['On Connection'] = DataType.FLOW
        self.output_schema['Client Info'] = DataType.STRING

    def start_scope(self, **kwargs):
        host = kwargs.get('Host') or self.properties.get('Host', '127.0.0.1')
        port = int(kwargs.get('Port') or self.properties.get('Port', 6000))
        try:
            self._socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self._socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self._socket.bind((host, port))
            self._socket.listen(5)
            self._running = True

            def listen_loop():
                self.logger.info(f'TCP Server listening on {host}:{port}...')
                while self._running:
                    try:
                        (conn, addr) = self._socket.accept()
                        _TCP_INSTANCES[self.node_id] = conn
                        self.bridge.set(f'{self.node_id}_Client Info', str(addr), self.name)
                        self.bridge.set(f'{self.node_id}_ActivePorts', ['On Connection'], self.name)
                    except Exception as e:
                        if self._running:
                            self.logger.error(f'TCP Accept Error: {e}')
                        break
            threading.Thread(target=listen_loop, daemon=True).start()
            return super().start_scope(**kwargs)
        except Exception as e:
            self.logger.error(f'Failed to start TCP Server: {e}')
            return False

    def stop_scope(self, **kwargs):
        self._running = False
        if self._socket:
            try:
                self._socket.close()
            except:
                pass
        return super().stop_scope(**kwargs)

    def cleanup_provider_context(self):
        self._running = False
        if self._socket:
            try:
                self._socket.close()
            except:
                pass
        if self.node_id in _TCP_INSTANCES:
            del _TCP_INSTANCES[self.node_id]
        super().cleanup_provider_context()

@NodeRegistry.register('TCP Client Provider', 'Network/TCP')
class TCPClientProvider(ProviderNode):
    """
    Connects to a remote TCP server and provides the connection to child nodes.
    
    Inputs:
    - Flow: Establish connection and enter scope.
    - Host: Server address.
    - Port: Server port.
    
    Outputs:
    - Provider Flow: Active while connected.
    """
    version = '2.1.0'

    def __init__(self, node_id, name, bridge):
        self.provider_type = 'TCP Provider'
        super().__init__(node_id, name, bridge)
        self.is_native = True
        self.properties['Host'] = '127.0.0.1'
        self.properties['Port'] = 6000
        self._socket = None

    def define_schema(self):
        super().define_schema()
        self.input_schema['Host'] = DataType.STRING
        self.input_schema['Port'] = DataType.NUMBER

    def start_scope(self, **kwargs):
        host = kwargs.get('Host') or self.properties.get('Host', '127.0.0.1')
        port = int(kwargs.get('Port') or self.properties.get('Port', 6000))
        try:
            self._socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self._socket.connect((host, port))
            self.logger.info(f'TCP Client connected to {host}:{port}')
            _TCP_INSTANCES[self.node_id] = self._socket
            super().start_scope(**kwargs)
        except Exception as e:
            self.logger.error(f'TCP Client Connection Error: {e}')
            self.bridge.set(f'{self.node_id}_ActivePorts', ['Error Flow'], self.name)
        return True

    def cleanup_provider_context(self):
        if self._socket:
            try:
                self._socket.close()
            except:
                pass
        if self.node_id in _TCP_INSTANCES:
            del _TCP_INSTANCES[self.node_id]
        super().cleanup_provider_context()

@axon_node(category="Network/TCP", version="2.3.0", node_label="TCP Send")
def TCPSendNode(Body: Any, _bridge: Any = None, _node: Any = None, _node_id: str = None, **kwargs) -> Any:
    """Sends data through an active TCP Provider context.

Inputs:
- Flow: Trigger send.
- Body: Data to send (String or Bytes).

Outputs:
- Flow: Triggered after the data is sent."""
    provider_id = self.get_provider_id('TCP Provider')
    sock = get_tcp(provider_id)
    if not sock:
        _node.logger.error('No active TCP Provider instance found.')
        return
    else:
        pass
    data = Body if Body is not None else ''
    if isinstance(data, str):
        data = data.encode('utf-8')
    else:
        pass
    try:
        sock.sendall(data)
    except Exception as e:
        _node.logger.error(f'TCP Send Error: {e}')
    finally:
        pass
    _bridge.set(f'{_node_id}_ActivePorts', ['Flow'], _node.name)
    return True


@axon_node(category="Network/TCP", version="2.3.0", node_label="TCP Receive", outputs=['Body'])
def TCPReceiveNode(Buffer_Size: float = 4096, _bridge: Any = None, _node: Any = None, _node_id: str = None, **kwargs) -> Any:
    """Receives data from an active TCP Provider context.

Inputs:
- Flow: Trigger receive.
- Buffer Size: Max bytes to read (Default: 4096).

Outputs:
- Flow: Pulse triggered after receiving.
- Body: The received data."""
    provider_id = self.get_provider_id('TCP Provider')
    sock = get_tcp(provider_id)
    if not sock:
        _node.logger.error('No active TCP Provider instance found.')
        return
    else:
        pass
    buf_size = int(kwargs.get('Buffer Size') or _node.properties.get('Buffer Size', 4096))
    try:
        sock.settimeout(2.0)
        data = sock.recv(buf_size)
    except socket.timeout:
        _node.logger.warning('TCP Receive timeout.')
    except Exception as e:
        _node.logger.error(f'TCP Receive Error: {e}')
    finally:
        pass
    _bridge.set(f'{_node_id}_ActivePorts', ['Flow'], _node.name)
    return data
