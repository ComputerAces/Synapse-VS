from synapse.core.super_node import SuperNode
from synapse.nodes.registry import NodeRegistry
from synapse.core.types import DataType
from synapse.core.dependencies import DependencyManager
from synapse.nodes.lib.provider_node import ProviderNode
import threading
import time

# Lazy Globals
socketio_mod = None

# Local instance registry to bypass Bridge pickling issues for native nodes
_SOCKETIO_INSTANCES = {}

def ensure_socketio():
    global socketio_mod
    if socketio_mod: return True
    if DependencyManager.ensure("python-socketio", "socketio"):
        import socketio as _s; socketio_mod = _s; return True
    return False

def ensure_flask_socketio():
    return DependencyManager.ensure("flask-socketio")

def get_sio(provider_id):
    return _SOCKETIO_INSTANCES.get(provider_id)

@NodeRegistry.register("SocketIO Server Provider", "Network/Sockets")
class SocketIOServerProvider(ProviderNode):
    """
    Hosts a SocketIO server. Can attach to an existing Flask Host.
    
    Inputs:
    - Flow: Start the server and enter scope.
    - Provider End: Pulse to close scope.
    - Host: (Optional) The address to bind to if standalone.
    - Port: (Optional) The port to bind to if standalone (Default: 5000).
    
    Outputs:
    - Provider Flow: Active while the server is running.
    - Provider ID: Unique ID for this provider.
    """
    version = "2.1.0"

    def __init__(self, node_id, name, bridge):
        self.provider_type = "SocketIO Provider"
        super().__init__(node_id, name, bridge)
        self.is_native = True 
        self.properties["Port"] = 5000
        self.properties["Host"] = "127.0.0.1"
        self._sio = None

    def define_schema(self):
        super().define_schema()
        self.input_schema["Host"] = DataType.STRING
        self.input_schema["Port"] = DataType.NUMBER

    def start_scope(self, **kwargs):
        if not ensure_socketio():
            self.logger.error("python-socketio not installed.")
            return

        # Attempt to attach to Flask
        provider_id = self.get_provider_id("Flask Provider")
        app = self.bridge.get(f"{provider_id}_Provider") if provider_id else None

        if app:
            if ensure_flask_socketio():
                try:
                    from flask_socketio import SocketIO
                    self._sio = SocketIO(app, cors_allowed_origins="*")
                    self.logger.info("SocketIO Server attached to Flask App.")
                except Exception as e:
                    self.logger.error(f"Failed to attach SocketIO to Flask: {e}")
            else:
                self.logger.error("flask-socketio not installed.")
        else:
            # Standalone Server
            try:
                host = kwargs.get("Host") or self.properties.get("Host", "127.0.0.1")
                port = int(kwargs.get("Port") or self.properties.get("Port", 5000))
                
                self._sio = socketio_mod.Server(cors_allowed_origins="*")
                self.logger.info(f"SocketIO Standalone Server initialized on {host}:{port}")
            except Exception as e:
                self.logger.error(f"Failed to start standalone SocketIO: {e}")

        if self._sio:
            _SOCKETIO_INSTANCES[self.node_id] = self._sio
            super().start_scope(**kwargs)
        else:
            self.bridge.set(f"{self.node_id}_ActivePorts", ["Error Flow"], self.name)
        return True

    def cleanup_provider_context(self):
        if self.node_id in _SOCKETIO_INSTANCES:
            del _SOCKETIO_INSTANCES[self.node_id]
        super().cleanup_provider_context()

@NodeRegistry.register("SocketIO Client Provider", "Network/Sockets")
class SocketIOClientProvider(ProviderNode):
    """
    Connects to a remote SocketIO server.
    
    Inputs:
    - Flow: Establish connection and enter scope.
    - URL: The server URL (Default: http://127.0.0.1:5000).
    
    Outputs:
    - Provider Flow: Active while connected.
    """
    version = "2.1.0"

    def __init__(self, node_id, name, bridge):
        self.provider_type = "SocketIO Provider"
        super().__init__(node_id, name, bridge)
        self.is_native = True
        self.properties["URL"] = "http://127.0.0.1:5000"
        self._sio = None

    def define_schema(self):
        super().define_schema()
        self.input_schema["URL"] = DataType.STRING

    def start_scope(self, **kwargs):
        if not ensure_socketio():
            self.logger.error("python-socketio not installed.")
            return

        url = kwargs.get("URL") or self.properties.get("URL", "http://127.0.0.1:5000")
        
        try:
            self._sio = socketio_mod.Client()
            self._sio.connect(url)
            self.logger.info(f"SocketIO Client connected to {url}")
            
            _SOCKETIO_INSTANCES[self.node_id] = self._sio
            super().start_scope(**kwargs)
        except Exception as e:
            self.logger.error(f"SocketIO Client Connection Error: {e}")
            self.bridge.set(f"{self.node_id}_ActivePorts", ["Error Flow"], self.name)
        return True

    def cleanup_provider_context(self):
        if self._sio and hasattr(self._sio, 'connected') and self._sio.connected:
            self._sio.disconnect()
        if self.node_id in _SOCKETIO_INSTANCES:
            del _SOCKETIO_INSTANCES[self.node_id]
        super().cleanup_provider_context()

@NodeRegistry.register("SocketIO Emit", "Network/Sockets")
class SocketIOEmitNode(SuperNode):
    """
    Emits an event to the active SocketIO Provider.
    
    Inputs:
    - Flow: Trigger emission.
    - Event: The event name.
    - Body: The data payload.

    Outputs:
    - Flow: Triggered after the event is emitted.
    """
    version = "2.1.0"

    def __init__(self, node_id, name, bridge):
        super().__init__(node_id, name, bridge)
        self.required_providers = ["SocketIO Provider"]
        self.is_native = True
        self.properties["Event"] = "message"
        self.define_schema()
        self.register_handlers()

    def define_schema(self):
        self.input_schema = {
            "Flow": DataType.FLOW,
            "Event": DataType.STRING,
            "Body": DataType.ANY
        }
        self.output_schema = {
            "Flow": DataType.FLOW
        }

    def register_handlers(self):
        self.register_handler("Flow", self.emit_event)

    def emit_event(self, Event=None, Body=None, **kwargs):
        provider_id = self.get_provider_id("SocketIO Provider")
        sio = get_sio(provider_id)

        if not sio:
            self.logger.error("No active SocketIO Provider instance found.")
            return

        event_name = Event if Event is not None else self.properties.get("Event", "message")
        
        try:
            sio.emit(event_name, Body)
        except Exception as e:
            self.logger.error(f"Emit Error: {e}")
            
        self.bridge.set(f"{self.node_id}_ActivePorts", ["Flow"], self.name)
        return True

@NodeRegistry.register("SocketIO On Event", "Network/Sockets")
class SocketIOOnEventNode(SuperNode):
    """
    Listens for a specific event on the active SocketIO Provider.
    
    Inputs:
    - Flow: Start the event watch.
    - Stop: Stop the event watch and finish.
    - Event: The event name to listen for.
    
    Outputs:
    - On Event: Pulse triggered when message received.
    - Received Data: The data payload.
    - Flow: Triggered when the service stops.
    """
    version = "2.1.0"

    def __init__(self, node_id, name, bridge):
        super().__init__(node_id, name, bridge)
        self.required_providers = ["SocketIO Provider"]
        self.is_native = True
        self.is_service = True
        self.properties["Event"] = "message"
        self._is_listening = False
        self._should_stop = False
        self.define_schema()
        self.register_handlers()

    def define_schema(self):
        self.input_schema = {
            "Flow": DataType.FLOW,
            "Stop": DataType.FLOW,
            "Event": DataType.STRING
        }
        self.output_schema = {
            "On Event": DataType.FLOW,
            "Received Data": DataType.ANY,
            "Flow": DataType.FLOW
        }

    def register_handlers(self):
        self.register_handler("Flow", self.start_service_trigger)
        self.register_handler("Stop", self.stop_service_trigger)

    def start_service_trigger(self, **kwargs):
        if not self._is_listening:
            self._should_stop = False
            return self.start_service(**kwargs)
        return True

    def stop_service_trigger(self, **kwargs):
        self._should_stop = True
        return True

    def do_work(self, **kwargs):
        if self._should_stop:
            self._is_listening = False
            self.bridge.set(f"{self.node_id}_ActivePorts", ["Flow"], self.name)
            return False

        if self._is_listening: 
            time.sleep(0.1)
            return True
        
        provider_id = self.get_provider_id("SocketIO Provider")
        sio = get_sio(provider_id)

        if sio:
            event_name = self.properties.get("Event", "message")
            
            @sio.on(event_name)
            def handle_event(*args):
                data = args[0] if args else None
                self.bridge.set(f"{self.node_id}_Received Data", data, self.name)
                self.bridge.set(f"{self.node_id}_ActivePorts", ["On Event"], self.name)

            self._is_listening = True
            self.logger.info(f"Listening for SocketIO event: {event_name}")
        
        time.sleep(0.5)
        return True

@NodeRegistry.register("SocketIO Room", "Network/Sockets")
class SocketIORoomNode(SuperNode):
    """
    Manages client participation in SocketIO rooms.
    Requires a SocketIO Server Provider.
    
    Inputs:
    - Flow: Trigger management.
    - SID: Client session ID.
    - Room: Room name.
    - Action: 'Join' or 'Leave' (Default: Join).

    Outputs:
    - Flow: Triggered after the room action is performed.
    """
    version = "2.1.0"

    def __init__(self, node_id, name, bridge):
        super().__init__(node_id, name, bridge)
        self.required_providers = ["SocketIO Provider"]
        self.is_native = True
        self.properties["Action"] = "Join"
        self.define_schema()
        self.register_handlers()

    def define_schema(self):
        self.input_schema = {
            "Flow": DataType.FLOW,
            "SID": DataType.STRING,
            "Room": DataType.STRING,
            "Action": DataType.STRING
        }
        self.output_schema = {
            "Flow": DataType.FLOW
        }

    def register_handlers(self):
        self.register_handler("Flow", self.manage_room)

    def manage_room(self, SID=None, Room=None, Action=None, **kwargs):
        if not ensure_flask_socketio():
             raise RuntimeError(f"[{self.name}] flask-socketio not installed.")

        from flask_socketio import join_room, leave_room
        
        action = Action if Action is not None else self.properties.get("Action", "Join")
        
        try:
            if action == "Join":
                join_room(Room, sid=SID)
            else:
                leave_room(Room, sid=SID)
        except Exception as e:
            self.logger.warning(f"Room Error: {e}")
            
        self.bridge.set(f"{self.node_id}_ActivePorts", ["Flow"], self.name)
        return True
