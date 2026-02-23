import threading
import time
from synapse.core.node import BaseNode
from synapse.nodes.registry import NodeRegistry
from synapse.core.types import DataType
from synapse.core.dependencies import DependencyManager
from synapse.nodes.lib.provider_node import ProviderNode

# Lazy Global
Flask = None

def ensure_flask():
    global Flask
    if Flask: return True
    if DependencyManager.ensure("flask"):
        from flask import Flask as _F; Flask = _F; return True
    return False

@NodeRegistry.register("Flask Host", "Network/Ingress")
class FlaskNode(ProviderNode):
    """
    HTTP Server Provider (Flask). Launches a local web server to handle incoming network requests.
    
    This node acts as a service provider, allowing other 'Flask Route' nodes to register endpoints 
    within its scope. It is the foundation for creating local REST APIs, webhooks, or simple 
    web interfaces directly within a Synapse graph.
    
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
    version = "2.1.0"

    def __init__(self, node_id, name, bridge):
        super().__init__(node_id, name, bridge)
        self.is_service = True
        self.provider_type = "Flask Provider"
        self.properties["Port"] = 5000
        self.properties["Host"] = "127.0.0.1"

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

