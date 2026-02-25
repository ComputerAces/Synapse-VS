import os
import threading
import time
from synapse.core.types import DataType
from synapse.nodes.registry import NodeRegistry
from synapse.nodes.lib.provider_node import ProviderNode
from synapse.utils.logger import main_logger as logger

@NodeRegistry.register("File System Provider", "File System/File Editing")
class FileProviderNode(ProviderNode):
    """
    Managed service provider for low-level file system I/O.
    Opens a persistent file handle and provides hijackable operations (read, write, seek, etc.)
    for downstream nodes within its execution scope.
    
    Inputs:
    - Flow: Start the file provider scope.
    - Provider End: Close the file handle and end the scope.
    - File Path: The absolute path to the file.
    - Mode: The file open mode (r, w, a, rb, wb, etc.).
    
    Outputs:
    - Provider Flow: Active while the file handle is open.
    - Provider ID: Unique identifier for this provider.
    - Flow: Triggered when the file is closed.
    """
    version = "2.1.0"

    def __init__(self, node_id, name, bridge):
        super().__init__(node_id, name, bridge)
        self.provider_type = "FILE"
        self._file_handle = None
        self._stop_event = None
        self._listener_thread = None
        self.properties["File Path"] = ""
        self.properties["Mode"] = "r"

    def define_schema(self):
        # Call super to get base provider ports
        super().define_schema()
        # Add File Provider specific inputs
        self.input_schema["File Path"] = DataType.STRING
        self.input_schema["Mode"] = DataType.STRING

    def start_scope(self, **kwargs):
        # Fallback with legacy support
        file_path = kwargs.get("File Path") or self.properties.get("File Path")
        mode = kwargs.get("Mode") or self.properties.get("Mode", self.properties.get("Mode", "r"))
        
        if not file_path:
            logger.error(f"[{self.name}] No File Path provided.")
            return
            
        try:
            # Ensure directory exists for write modes
            if 'w' in mode or 'a' in mode:
                os.makedirs(os.path.dirname(os.path.abspath(file_path)), exist_ok=True)
            
            self._file_handle = open(file_path, mode)
            logger.info(f"[{self.name}] Opened '{file_path}' in mode '{mode}'.")
            
            # Start Background Listener
            import threading
            self._stop_event = threading.Event()
            self._stop_event.clear()
            self._listener_thread = threading.Thread(target=self._hijack_listener, daemon=True)
            self._listener_thread.start()
            
            # Call super to handle registration and flow trigger
            return super().start_scope(**kwargs)
            
        except Exception as e:
            logger.error(f"[{self.name}] Failed to open file: {e}")
            return

    def end_scope(self, **kwargs):
        if self._stop_event:
            self._stop_event.set()
        if self._listener_thread:
            self._listener_thread.join(timeout=1.0)
        
        # 2. Close Handle
        if self._file_handle:
            try:
                self._file_handle.close()
                logger.info(f"[{self.name}] File handle closed.")
            except: pass
            self._file_handle = None

        return super().end_scope(**kwargs)

    def register_provider_context(self):
        """Registers the I/O hijack handlers."""
        self.bridge.register_super_function(self.node_id, "read", self.node_id)
        self.bridge.register_super_function(self.node_id, "write", self.node_id)
        self.bridge.register_super_function(self.node_id, "seek", self.node_id)
        self.bridge.register_super_function(self.node_id, "peek", self.node_id)
        self.bridge.register_super_function(self.node_id, "tell", self.node_id)

    def _hijack_listener(self):
        """Background loop to process hijacking requests from other nodes."""
        logger.info(f"[{self.name}] Hijack Listener Started.")
        while self._stop_event and not self._stop_event.is_set():
            req = self.bridge.get(f"{self.node_id}_HijackRequest")
            if req:
                # Consume immediately to prevent double-processing
                self.bridge.set(f"{self.node_id}_HijackRequest", None, self.name)
                
                func = req.get("func")
                data = req.get("data", {})
                req_id = req.get("id")
                
                result = self.handle_hijack(func, data)
                
                # Respond
                self.bridge.set(f"{self.node_id}_HijackResponse", {"id": req_id, "result": result}, self.name)
            
            time.sleep(0.01) # Low latency polling
        logger.info(f"[{self.name}] Hijack Listener Stopped.")

    def handle_hijack(self, func, data):
        """Process local file operations based on hijack requests."""
        if not self._file_handle:
            return None
            
        # Keepalive pulse
        # print(f"[PROVIDER_PULSE] {self.node_id}", flush=True) 
            
        try:
            if func == "read":
                n = int(data.get("n", -1))
                return self._file_handle.read(n)
            
            elif func == "write":
                content = data.get("content", "")
                if 'b' in self._file_handle.mode and isinstance(content, str):
                    content = content.encode('utf-8')
                self._file_handle.write(content)
                return len(content)
            
            elif func == "seek":
                offset = int(data.get("offset", 0))
                whence = int(data.get("whence", 0))
                self._file_handle.seek(offset, whence)
                return self._file_handle.tell()
            
            elif func == "peek":
                n = int(data.get("n", 1))
                pos = self._file_handle.tell()
                res = self._file_handle.read(n)
                self._file_handle.seek(pos)
                return res
            
            elif func == "tell":
                return self._file_handle.tell()
                
        except Exception as e:
            logger.error(f"[{self.name}] Hijack Implementation Error ({func}): {e}")
            return None
        return None

