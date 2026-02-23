import time
from synapse.core.super_node import SuperNode
from synapse.nodes.registry import NodeRegistry
from synapse.core.data import DataBuffer
from synapse.core.types import DataType
from synapse.core.dependencies import DependencyManager

# Lazy Global
flask_request = None

def ensure_flask_req():
    global flask_request
    if flask_request: return True
    if DependencyManager.ensure("flask"):
        from flask import request as _r; flask_request = _r; return True
    return False

@NodeRegistry.register("Flask Route", "Network/Ingress")
class FlaskRouteNode(SuperNode):
    """
    Registers an HTTP endpoint (URL path) on an active Flask server.
    
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
    - Request ID: Unique token used to map the response back to this request.
    """
    version = "2.1.0"

    def __init__(self, node_id, name, bridge):
        super().__init__(node_id, name, bridge)
        self.is_native = True 
        self.properties["Path"] = "/"
        self.properties["Method"] = "GET"
        self.define_schema()
        self.register_handlers()

    def define_schema(self):
        self.input_schema = {
            "Flow": DataType.FLOW,
            "Service ID": DataType.STRING,
            "Path": DataType.STRING,
            "Method": DataType.STRING
        }
        self.output_schema = {
            "Trigger": DataType.FLOW,
            "Query": DataType.DICT,
            "Body": DataType.BYTES,
            "Request ID": DataType.STRING
        }

    def register_handlers(self):
        self.register_handler("Flow", self.handle_registration)

    def handle_registration(self, Service_ID=None, Path=None, Method=None, **kwargs):
        service_id = Service_ID or kwargs.get("Service ID")
        if not service_id:
            provider_id = self.get_provider_id("Flask Provider")
            if provider_id: 
                service_id = self.bridge.get(f"{provider_id}_Service ID")
        
        if not ensure_flask_req():
            self.logger.error("Flask dependency missing.")
            return False

        if not service_id:
            raise RuntimeError(f"[{self.name}] Missing Flask Provider (Service ID).")
        
        app = self.bridge.get(service_id)
        if not app:
             self.logger.error(f"Flask App '{service_id}' not found active.")
             return False
        
        path = Path if Path is not None else kwargs.get("Path") or self.properties.get("Path", "/")
        method = (Method if Method is not None else kwargs.get("Method") or self.properties.get("Method", "GET")).upper()

        def route_handler():
            import uuid
            req_id = f"req_{self.node_id}_{time.time()}"
            
            # Pack request data
            query = dict(flask_request.args)
            body = DataBuffer(flask_request.data)
            
            self.bridge.set(f"{self.node_id}_Query", query, self.name)
            self.bridge.set(f"{self.node_id}_Body", body, self.name)
            self.bridge.set(f"{self.node_id}_Request ID", req_id, self.name)
            self.bridge.set(f"{self.node_id}_ActivePorts", ["Trigger"], self.name)
            
            # Blocking loop for response
            start_time = time.time()
            while time.time() - start_time < 30:
                resp = self.bridge.get(f"RESP_{req_id}")
                if resp:
                    return resp["body"], resp["status"], resp["headers"]
                time.sleep(0.05)
            return "Timeout", 504
        
        try:
            endpoint = f"node_{self.node_id}"
            app.add_url_rule(path, endpoint=endpoint, view_func=route_handler, methods=[method])
            self.logger.info(f"Registered route: {method} {path}")
            return True
        except Exception as e:
            self.logger.warning(f"Registration warning: {e}")
            return False

@NodeRegistry.register("Flask Response", "Network/Ingress")
class FlaskResponseNode(SuperNode):
    """
    Sends an HTTP response back to a client that triggered a 'Flask Route'.
    
    This node completes the lifecycle of an HTTP request. It uses the 'Request ID' 
    provided by the route node to ensure the response reaches the correct client.
    
    Inputs:
    - Flow: Trigger the response.
    - Body: The content to send back (String/HTML/JSON).
    - Status Code: The HTTP status code (e.g., 200, 404).
    - Request ID: The token from the corresponding 'Flask Route' node.
    - Content Type: The MIME type (e.g., 'text/html', 'application/json').
    
    Outputs:
    - Flow: Triggered after the response is sent to the bridge.
    """
    version = "2.1.0"

    def __init__(self, node_id, name, bridge):
        super().__init__(node_id, name, bridge)
        self.properties["Status Code"] = 200
        self.properties["Content Type"] = "text/plain"
        self.define_schema()
        self.register_handlers()

    def define_schema(self):
        self.input_schema = {
            "Flow": DataType.FLOW,
            "Body": DataType.STRING,
            "Status Code": DataType.INT,
            "Request ID": DataType.STRING,
            "Content Type": DataType.STRING
        }
        self.output_schema = {
            "Flow": DataType.FLOW
        }

    def register_handlers(self):
        self.register_handler("Flow", self.handle_response)

    def handle_response(self, Body="", Status_Code=None, Request_ID=None, Content_Type=None, **kwargs):
        if not Request_ID: 
            self.bridge.set(f"{self.node_id}_ActivePorts", ["Flow"], self.name)
            return True
            
        status = Status_Code if Status_Code is not None else kwargs.get("Status Code") or self.properties.get("Status Code", 200)
        c_type = Content_Type if Content_Type is not None else kwargs.get("Content Type") or self.properties.get("Content Type", "text/plain")
        
        payload = {
            "body": Body, 
            "status": int(status),
            "headers": {"Content-Type": c_type}
        }
        
        self.bridge.set(f"RESP_{Request_ID}", payload, self.name)
        self.bridge.set(f"{self.node_id}_ActivePorts", ["Flow"], self.name)
        return True
