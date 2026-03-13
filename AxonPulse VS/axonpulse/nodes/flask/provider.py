import threading
import time
from axonpulse.core.node import BaseNode
from axonpulse.nodes.registry import NodeRegistry
from axonpulse.core.types import DataType
from axonpulse.core.dependencies import DependencyManager
from axonpulse.nodes.lib.provider_node import ProviderNode

# Lazy Global
Flask = None

def ensure_flask():
    global Flask
    if Flask: return True
    if DependencyManager.ensure("flask") and DependencyManager.ensure("flask-limiter"):
        from flask import Flask as _F; Flask = _F; return True
    return False

@NodeRegistry.register("Flask Host", "Network/Ingress")
class FlaskNode(ProviderNode):
    """
    HTTP Server Provider (Flask). Launches a local web server to handle incoming network requests.
    
    This node acts as a service provider, allowing other 'Flask Route' nodes to register endpoints 
    within its scope. It is the foundation for creating local REST APIs, webhooks, or simple 
    web interfaces directly within a AxonPulse graph.
    
    Inputs:
    - Flow: Trigger to start the server.
    - Provider End: Signal to stop the server (Cleanup).
    - Host: The address to bind to (e.g., '127.0.0.1' for local, '0.0.0.0' for all interfaces).
    - Port: The TCP port to listen on (Default: 5000).
    
    Outputs:
    - Provider Flow: Active pulse while the server is running.
    - Service ID: Unique identifier for this Flask service.
    - Flow: Triggered after the server scope is closed.
    """
    version = "2.3.0"

    def __init__(self, node_id, name, bridge):
        super().__init__(node_id, name, bridge)
        self.is_service = True
        self.provider_type = "Flask Provider"
        self.properties["Port"] = 5000
        self.properties["Host"] = "127.0.0.1"
        self.properties["Enable DDOS Protection"] = True
        self.properties["Rate Limit"] = "100 per minute"

    def define_schema(self):
        super().define_schema()
        # Add Flask Specific
        self.input_schema["Host"] = DataType.STRING
        self.input_schema["Port"] = DataType.INT
        
        self.output_schema["Service ID"] = DataType.STRING

    def start_scope(self, **kwargs):
        if not ensure_flask(): 
            self.logger.error("Flask not installed.")
            return
        
        # Fallback to properties
        host = kwargs.get("Host") or self.properties.get("Host", "127.0.0.1")
        port = int(kwargs.get("Port") or self.properties.get("Port", 5000))
        
        app = Flask(self.name)
        service_id = f"flask_{self.node_id}"
        
        # Register Provider context
        self.bridge.set(service_id, app, self.name)
        self.bridge.set(f"{self.node_id}_Service ID", service_id, self.name)
        
        # We also set the generic context for any child nodes to find us
        self.bridge.set(f"{self.node_id}_Provider", app, self.name)
        
        # [DDOS Protection]
        enable_ddos = self.properties.get("Enable DDOS Protection", True)
        rate_limit = self.properties.get("Rate Limit", "100 per minute")
        
        if enable_ddos and rate_limit:
             try:
                 from flask_limiter import Limiter
                 from flask_limiter.util import get_remote_address
                 
                 # Initialize limiter attached to this app
                 limiter = Limiter(
                     get_remote_address,
                     app=app,
                     default_limits=[rate_limit],
                     storage_uri="memory://"
                 )
                 
                 # We store the limiter on the bridge so Route nodes can access it for overrides
                 self.bridge.set(f"{service_id}_limiter", limiter, self.name)
                 self.logger.info(f"DDOS Protection Enabled: {rate_limit}")
             except Exception as e:
                 self.logger.error(f"Failed to initialize DDOS Protection: {e}")
                 
        def run_server():
            try:
                self.logger.info(f"Starting Flask on {host}:{port}")
                app.run(host=host, port=port, debug=False, use_reloader=False)
            except Exception as e:
                self.logger.error(f"Flask Error: {e}")

        self._server_thread = threading.Thread(target=run_server, daemon=True)
        self._server_thread.start()
        
        # Call super to handle standard provider output flow
        super().start_scope(**kwargs)

    def register_provider_context(self):
        service_id = f"flask_{self.node_id}"
        app = self.bridge.get(service_id)
        if app:
            self.bridge.set(f"{self.node_id}_Provider", app, self.name)
        return self.provider_type

