import time

from axonpulse.core.super_node import SuperNode

from axonpulse.nodes.registry import NodeRegistry

from axonpulse.core.data import DataBuffer

from axonpulse.core.types import DataType

from axonpulse.core.dependencies import DependencyManager

from typing import Any, List, Dict, Optional

from axonpulse.core.types import DataType, TypeCaster

from axonpulse.nodes.decorators import axon_node

flask_request = None

def ensure_flask_req():
    global flask_request
    if flask_request:
        return True
    if DependencyManager.ensure('flask'):
        from flask import request as _r
        flask_request = _r
        return True
    return False

@axon_node(category="Network/Ingress", version="2.3.0", node_label="Flask Route", outputs=['Trigger', 'Query', 'Body', 'Request ID'])
def FlaskRouteNode(Service_ID: str, Path: str = '/', Method: str = 'GET', _bridge: Any = None, _node: Any = None, _node_id: str = None, **kwargs) -> Any:
    """Registers an HTTP endpoint (URL path) on an active Flask server.

When an external request matches this route's path and method, the 'Trigger' pulse 
is fired. The graph then processes the request and MUST return a 'Flask Response' 
node to finish the transaction.

Inputs:
- Flow: Register the route with the provider.
- Service ID: Optional ID of the Flask Host.
- Path: The URL endpoint (e.g., '/api/data').
- Method: The HTTP method (GET, POST, etc.).

Outputs:
- Trigger: Pulse fired when a request is received.
- Query: Dictionary of URL query parameters.
- Body: The raw request body (Bytes).
- Request ID: Unique token used to map the response back to this request."""
    service_id = Service_ID or kwargs.get('Service ID')
    if not service_id:
        provider_id = self.get_provider_id('Flask Provider')
        if provider_id:
            service_id = _bridge.get(f'{provider_id}_Service ID')
        else:
            pass
    else:
        pass
    if not ensure_flask_req():
        _node.logger.error('Flask dependency missing.')
        return False
    else:
        pass
    if not service_id:
        raise RuntimeError(f'[{_node.name}] Missing Flask Provider (Service ID).')
    else:
        pass
    app = _bridge.get(service_id)
    if not app:
        _node.logger.error(f"Flask App '{service_id}' not found active.")
        return False
    else:
        pass
    path = Path if Path is not None else kwargs.get('Path') or _node.properties.get('Path', '/')
    method = (Method if Method is not None else kwargs.get('Method') or _node.properties.get('Method', 'GET')).upper()
    
    def route_handler():
        import uuid
        req_id = f'req_{_node_id}_{time.time()}'
        query = dict(flask_request.args)
        body = DataBuffer(flask_request.data)
        _bridge.set(f'{_node_id}_ActivePorts', ['Trigger'], _node.name)
        start_time = time.time()
        while time.time() - start_time < 30:
            resp = _bridge.get(f'RESP_{req_id}')
            if resp:
                return (resp['body'], resp['status'], resp['headers'])
            else:
                pass
            time.sleep(0.05)
        return ('Timeout', 504)
    try:
        endpoint = f'node_{_node_id}'
        override_limit = _node.properties.get('Override Rate Limit', '')
        if override_limit and service_id:
            limiter = _bridge.get(f'{service_id}_limiter')
            if limiter:
                try:
                    route_handler = limiter.limit(override_limit)(route_handler)
                    _node.logger.info(f'Route {path} override limit: {override_limit}')
                except Exception as e:
                    _node.logger.warning(f'Failed to apply route limit override: {e}')
                finally:
                    pass
            else:
                pass
        else:
            pass
        app.add_url_rule(path, endpoint=endpoint, view_func=route_handler, methods=[method])
        _node.logger.info(f'Registered route: {method} {path}')
    except Exception as e:
        _node.logger.warning(f'Registration warning: {e}')
        return False
    finally:
        pass
    return {'Query': query, 'Body': body, 'Request ID': req_id}


@axon_node(category="Network/Ingress", version="2.3.0", node_label="Flask Response")
def FlaskResponseNode(Body: str, Request_ID: str, Status_Code: Any = 200, Content_Type: str = 'text/plain', _bridge: Any = None, _node: Any = None, _node_id: str = None, **kwargs) -> Any:
    """Sends an HTTP response back to a client that triggered a 'Flask Route'.

This node completes the lifecycle of an HTTP request. It uses the 'Request ID' 
provided by the route node to ensure the response reaches the correct client.

Inputs:
- Flow: Trigger the response.
- Body: The content to send back (String/HTML/JSON).
- Status Code: The HTTP status code (e.g., 200, 404).
- Request ID: The token from the corresponding 'Flask Route' node.
- Content Type: The MIME type (e.g., 'text/html', 'application/json').

Outputs:
- Flow: Triggered after the response is sent to the bridge."""
    if not Request_ID:
        _bridge.set(f'{_node_id}_ActivePorts', ['Flow'], _node.name)
        return True
    else:
        pass
    status = Status_Code if Status_Code is not None else kwargs.get('Status Code') or _node.properties.get('Status Code', 200)
    c_type = Content_Type if Content_Type is not None else kwargs.get('Content Type') or _node.properties.get('Content Type', 'text/plain')
    payload = {'body': Body, 'status': int(status), 'headers': {'Content-Type': c_type}}
    _bridge.set(f'RESP_{Request_ID}', payload, _node.name)
    _bridge.set(f'{_node_id}_ActivePorts', ['Flow'], _node.name)
    return True
