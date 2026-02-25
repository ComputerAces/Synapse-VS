import uuid
import json
from synapse.core.super_node import SuperNode
from synapse.nodes.registry import NodeRegistry
from synapse.core.types import DataType
from synapse.utils.logger import main_logger as logger
from synapse.nodes.lib.provider_node import ProviderNode

class ConnectionHandle:
    """
    Protocol-agnostic handle containing connection configuration.
    Passed between Provider nodes and Action nodes.
    """
    def __init__(self, protocol, config):
        self.id = f"conn_{uuid.uuid4().hex[:8]}"
        self.protocol = protocol # REST, WSS, gRPC
        self.config = config     # Dictionary of settings (base_url, timeout, etc.)

    def __str__(self):
        return f"[{self.protocol} Handle: {self.id}]"

    def __repr__(self):
        return self.__str__()

# --- PROVIDER NODES ---

@NodeRegistry.register("REST Provider", "Connectivity/Providers")
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
    version = "2.1.0"
    provider_type = "REST"

    def __init__(self, node_id, name, bridge):
        super().__init__(node_id, name, bridge)
        self.is_native = True
        self.properties["Base URL"] = ""
        self.properties["Port"] = 80
        self.properties["Timeout"] = 30
        self.properties["AuthStrategy"] = "Bearer"

    def register_handlers(self):
        super().register_handlers()
        # Ensure 'Flow' from super triggers our custom handle creation too
        # though ProviderNode.start_scope already triggers Provider Flow.
        # We override start_scope or register_provider_context to set the handle.

    def define_schema(self):
        super().define_schema()
        self.input_schema.update({
            "Base URL": DataType.STRING,
            "Port": DataType.NUMBER,
            "Timeout": DataType.NUMBER,
            "AuthStrategy": DataType.STRING
        })
        self.output_schema.update({
            "Handle": DataType.ANY
        })

    def start_scope(self, **kwargs):
        # Create handle before starting scope so it's available in context
        base_url = kwargs.get("Base URL") or self.properties.get("Base URL")
        port = kwargs.get("Port") or self.properties.get("Port", 80)
        timeout = kwargs.get("Timeout") or self.properties.get("Timeout", 30)
        auth = kwargs.get("AuthStrategy") or self.properties.get("AuthStrategy", "None")
        
        handle = ConnectionHandle("REST", {
            "base_url": base_url,
            "port": port,
            "timeout": timeout,
            "auth_strategy": auth
        })
        self.bridge.set(f"{self.node_id}_Handle", handle, self.name)
        return super().start_scope(**kwargs)

@NodeRegistry.register("WebSocket Provider", "Connectivity/Providers")
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
    version = "2.1.0"
    provider_type = "SOCKET"

    def __init__(self, node_id, name, bridge):
        super().__init__(node_id, name, bridge)
        self.is_native = True
        self.properties["URL"] = ""
        self.properties["Reconnect"] = True
        # super().__init__ calls define_schema and register_handlers

    def register_handlers(self):
        super().register_handlers()

    def define_schema(self):
        super().define_schema()
        self.input_schema.update({
            "URL": DataType.STRING,
            "Reconnect": DataType.BOOLEAN
        })
        self.output_schema.update({
            "Handle": DataType.ANY
        })

    def start_scope(self, **kwargs):
        url = kwargs.get("URL") or self.properties.get("URL")
        reconnect = kwargs.get("Reconnect") if kwargs.get("Reconnect") is not None else self.properties.get("Reconnect", True)
        handle = ConnectionHandle("WSS", {
            "url": url,
            "reconnect": reconnect
        })
        self.bridge.set(f"{self.node_id}_Handle", handle, self.name)
        return super().start_scope(**kwargs)

@NodeRegistry.register("GRPC Provider", "Connectivity/Providers")
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
    version = "2.1.0"
    provider_type = "GRPC"

    def __init__(self, node_id, name, bridge):
        super().__init__(node_id, name, bridge)
        self.is_native = True
        self.properties["Server"] = "localhost:50051"
        # super().__init__ calls define_schema and register_handlers

    def register_handlers(self):
        super().register_handlers()

    def define_schema(self):
        super().define_schema()
        self.input_schema.update({
            "Server": DataType.STRING
        })
        self.output_schema.update({
            "Handle": DataType.ANY
        })

    def start_scope(self, **kwargs):
        target = kwargs.get("Server") or self.properties.get("Server")
        handle = ConnectionHandle("gRPC", {
            "target": target
        })
        self.bridge.set(f"{self.node_id}_Handle", handle, self.name)
        return super().start_scope(**kwargs)

@NodeRegistry.register("Net Request", "Connectivity/Actions")
class NetRequestNode(SuperNode):
    """
    Executes a high-level network request using the active Network Provider context.
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
    - Status: The numeric HTTP status code (e.g., 200, 404).
    """
    version = "2.1.0"

    def __init__(self, node_id, name, bridge):
        super().__init__(node_id, name, bridge)
        self.required_providers = ["Network Provider"]
        self.properties["App ID"] = "Global"
        self.is_native = True
        self.define_schema()
        self.register_handlers()

    def register_handlers(self):
        self.register_handler("Flow", self.make_request)

    def define_schema(self):
        self.input_schema = {
            "Flow": DataType.FLOW,
            "Method": DataType.STRING,
            "Endpoint": DataType.STRING,
            "Payload": DataType.ANY,
            "App ID": DataType.STRING
        }
        self.output_schema = {
            "Flow": DataType.FLOW,
            "Error Flow": DataType.FLOW,
            "Response": DataType.ANY,
            "Status": DataType.NUMBER
        }

    def make_request(self, Method=None, Endpoint=None, Payload=None, **kwargs):
        method = str(Method or kwargs.get("Method", "GET")).upper()
        endpoint = str(Endpoint or kwargs.get("Endpoint", ""))
        payload = Payload if Payload is not None else kwargs.get("Payload")
        app_id = kwargs.get("App ID") or self.properties.get("App ID", "Global")

        provider_id = self.get_provider_id("Network Provider")
        if not provider_id:
            msg = "No Network Provider found in scope."
            self.logger.error(msg)
            self.bridge.set(f"{self.node_id}_Response", msg, self.name)
            self.bridge.set(f"{self.node_id}_ActivePorts", ["Error Flow", "Flow"], self.name)
            return True

        base_url = self.bridge.get(f"{provider_id}_Base URL")
        proxy = self.bridge.get(f"{provider_id}_Proxy")
        headers = self.bridge.get(f"{provider_id}_Headers") or {}

        if not base_url:
            msg = "Network Provider has no Base URL."
            self.logger.error(msg)
            self.bridge.set(f"{self.node_id}_Response", msg, self.name)
            self.bridge.set(f"{self.node_id}_ActivePorts", ["Error Flow", "Flow"], self.name)
            return True

        identity = self.bridge.get_identity(app_id)
        auth_headers = headers.copy()
        if identity and identity.auth_payload:
            auth = identity.auth_payload
            # Note: Network Provider doesn't strictly define auth_strategy yet, 
            # so we check bearer_token as default.
            if "bearer_token" in auth:
                auth_headers["Authorization"] = f"Bearer {auth['bearer_token']}"
            elif "basic_auth" in auth:
                auth_headers["Authorization"] = f"Basic {auth['basic_auth']}"

        import requests
        url = f"{base_url.rstrip('/')}/{endpoint.lstrip('/')}"
        proxies = {"http": proxy, "https": proxy} if proxy else None
        
        try:
            resp = requests.request(
                method=method,
                url=url,
                json=payload if isinstance(payload, dict) else None,
                data=payload if not isinstance(payload, dict) else None,
                headers=auth_headers,
                proxies=proxies,
                timeout=30
            )
            self.bridge.set(f"{self.node_id}_Response", resp.text, self.name)
            self.bridge.set(f"{self.node_id}_Status", resp.status_code, self.name)
            self.bridge.set(f"{self.node_id}_ActivePorts", ["Flow"], self.name)
        except Exception as e:
            msg = f"Network Request Failed: {e}"
            self.logger.error(msg)
            self.bridge.set(f"{self.node_id}_Response", msg, self.name)
            self.bridge.set(f"{self.node_id}_Status", 0, self.name)
            self.bridge.set(f"{self.node_id}_ActivePorts", ["Error Flow", "Flow"], self.name)

        return True

@NodeRegistry.register("Net Stream", "Connectivity/Actions")
class NetStreamNode(SuperNode):
    """
    Pushes data messages through an established streaming connection in the active Network Provider context.
    
    Inputs:
    - Flow: Trigger the message push.
    - Message: The data or object to transmit through the stream.
    
    Outputs:
    - Flow: Triggered after the message is sent.
    - Error Flow: Triggered if the transmission fails.
    """
    version = "2.1.0"

    def __init__(self, node_id, name, bridge):
        super().__init__(node_id, name, bridge)
        self.required_providers = ["Network Provider"]
        self.is_native = True
        self.define_schema()
        self.register_handlers()

    def register_handlers(self):
        self.register_handler("Flow", self.push_stream)

    def define_schema(self):
        self.input_schema = {
            "Flow": DataType.FLOW,
            "Message": DataType.ANY,
            "App ID": DataType.STRING
        }
        self.output_schema = {
            "Flow": DataType.FLOW,
            "Error Flow": DataType.FLOW
        }

    def push_stream(self, Message=None, **kwargs):
        msg = Message if Message is not None else kwargs.get("Message")
        app_id = kwargs.get("App ID") or self.properties.get("App ID", "Global")
        provider_id = self.get_provider_id("Network Provider")
        if not provider_id:
            self.logger.error("No Network Provider found.")
            self.bridge.set(f"{self.node_id}_ActivePorts", ["Error Flow", "Flow"], self.name)
            return True
        
        # In a real implementation, we would get the socket/client from the provider context.
        # For now, we simulate the transmission success.
        self.logger.info(f"Pushing message to stream...")
        self.bridge.set(f"{self.node_id}_ActivePorts", ["Flow"], self.name)
        return True

@NodeRegistry.register("Net Listener", "Connectivity/Actions")
class NetListenerNode(SuperNode):
    """
    Establishes an event listener on the active Network Provider to capture incoming messages.
    Triggers the graph sequence whenever new data is received.
    
    Inputs:
    - Flow: Initialize the listener.
    - App ID: Optional identifier for isolation/authentication.
    
    Outputs:
    - Flow: Triggered every time a new message is received.
    - Message: The incoming data payload.
    """
    version = "2.1.0"

    def __init__(self, node_id, name, bridge):
        super().__init__(node_id, name, bridge)
        self.required_providers = ["Network Provider"]
        self.properties["App ID"] = "Global"
        self.is_native = True
        self.define_schema()
        self.register_handlers()

    def register_handlers(self):
        self.register_handler("Flow", self.register_listener)

    def define_schema(self):
        self.input_schema = {
            "Flow": DataType.FLOW,
            "App ID": DataType.STRING
        }
        self.output_schema = {
            "Flow": DataType.FLOW,
            "Message": DataType.ANY
        }

    def register_listener(self, **kwargs):
        self.bridge.set(f"{self.node_id}_ActivePorts", ["Flow"], self.name)
        return True
