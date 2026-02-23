from synapse.core.super_node import SuperNode
from synapse.core.types import DataType
from synapse.nodes.registry import NodeRegistry
from synapse.utils.logger import main_logger as logger

class BaseFileOpNode(SuperNode):
    """
    Base class for file operations requiring an active FILE provider.
    Handles provider lookup and hijack invocation.
    """
    required_providers = ["FILE"]
    
    def get_file_provider(self):
        # Use standardized provider lookup
        provider_id = self.get_provider_id("FILE")
        
        if not provider_id:
             # Fallback to direct Property if user linked it manually
             provider_id = self.properties.get("FileProvider")
        return provider_id

    def invoke(self, func, data):
        provider_id = self.get_file_provider()
        if not provider_id:
             raise RuntimeError(f"[{self.name}] No active File Provider found in context.")
             
        return self.bridge.invoke_hijack(provider_id, func, data)

@NodeRegistry.register("File Read", "File System/Operations")
class FileReadNode(BaseFileOpNode):
    """
    Reads data from an open file using an active FILE provider.
    
    This node retrieves content from the file associated with the current provider 
    session. It progresses the file pointer by the number of bytes read.
    
    Inputs:
    - Flow: Trigger the read operation.
    - Size: Number of bytes/characters to read (-1 for until EOF).
    
    Outputs:
    - Flow: Pulse triggered on successful read.
    - Error Flow: Pulse triggered if the read fails or no provider is active.
    - Data: The resulting content (String or Bytes).
    """
    version = "2.1.0"
    
    def define_schema(self):
        self.input_schema = {
            "Flow": DataType.FLOW,
            "Size": DataType.INT
        }
        self.output_schema = {
            "Flow": DataType.FLOW,
            "Error Flow": DataType.FLOW,
            "Data": DataType.ANY
        }

    def register_handlers(self):
        self.register_handler("Flow", self.handle_read)

    def handle_read(self, Size=-1, **kwargs):
        try:
            result = self.invoke("read", {"n": Size})
            self.bridge.set(f"{self.node_id}_Data", result, self.name)
            self.bridge.set(f"{self.node_id}_ActivePorts", ["Flow"], self.name)
        except Exception as e:
            self.logger.error(f"Read Error: {e}")
            self.bridge.set(f"{self.node_id}_ActivePorts", ["Error Flow"], self.name)
        return True

@NodeRegistry.register("File Write", "File System/Operations")
class FileWriteNode(BaseFileOpNode):
    """
    Writes data to an open file via an active FILE provider.
    
    This node commits content to the file at the current pointer position. 
    It is designed to work within a File Provider scope to handle persistent 
    file handles across a logic sequence.
    
    Inputs:
    - Flow: Trigger the write operation.
    - Data: The content to write (String or Bytes).
    
    Outputs:
    - Flow: Pulse triggered on successful write.
    - Error Flow: Pulse triggered if the operation fails.
    """
    version = "2.1.0"
    
    def define_schema(self):
        self.input_schema = {
            "Flow": DataType.FLOW,
            "Data": DataType.ANY
        }
        self.output_schema = {
            "Flow": DataType.FLOW,
            "Error Flow": DataType.FLOW
        }

    def register_handlers(self):
        self.register_handler("Flow", self.handle_write)

    def handle_write(self, Data="", **kwargs):
        try:
            self.invoke("write", {"content": Data})
            self.bridge.set(f"{self.node_id}_ActivePorts", ["Flow"], self.name)
        except Exception as e:
            self.logger.error(f"Write Error: {e}")
            self.bridge.set(f"{self.node_id}_ActivePorts", ["Error Flow"], self.name)
        return True

@NodeRegistry.register("File Seek", "File System/File Editing")
class FileSeekNode(BaseFileOpNode):
    """
    Adjusts the read/write pointer within an open file provider.
    
    Use this to move the pointer forward, backward, or to a specific offset 
    relative to the start, current position, or end of the file.
    
    Inputs:
    - Flow: Trigger the seek operation.
    - Offset: Number of bytes to move the pointer.
    - Whence: Reference point (0: Start, 1: Current, 2: End).
    
    Outputs:
    - Flow: Pulse triggered on successful movement.
    - Error Flow: Pulse triggered if the seek is invalid or fails.
    """
    version = "2.1.0"
    
    def define_schema(self):
        self.input_schema = {
            "Flow": DataType.FLOW,
            "Offset": DataType.INT,
            "Whence": DataType.INT
        }
        self.output_schema = {
            "Flow": DataType.FLOW,
            "Error Flow": DataType.FLOW
        }

    def register_handlers(self):
        self.register_handler("Flow", self.handle_seek)

    def handle_seek(self, Offset=0, Whence=0, **kwargs):
        try:
            self.invoke("seek", {"offset": Offset, "whence": Whence})
            self.bridge.set(f"{self.node_id}_ActivePorts", ["Flow"], self.name)
        except Exception as e:
            self.logger.error(f"Seek Error: {e}")
            self.bridge.set(f"{self.node_id}_ActivePorts", ["Error Flow"], self.name)
        return True

@NodeRegistry.register("File Peek", "File System/Operations")
class FilePeekNode(BaseFileOpNode):
    """
    Reads data from a file without moving the active pointer position.
    
    Peek allows investigating upcoming data in the stream without affecting 
    subsequent Read operations within the same provider session.
    
    Inputs:
    - Flow: Trigger the peek operation.
    - Size: Number of bytes/characters to peek.
    
    Outputs:
    - Flow: Pulse triggered on success.
    - Error Flow: Pulse triggered if the operation fails.
    - Data: The content read.
    """
    version = "2.1.0"
    
    def define_schema(self):
        self.input_schema = {
            "Flow": DataType.FLOW,
            "Size": DataType.INT
        }
        self.output_schema = {
            "Flow": DataType.FLOW,
            "Error Flow": DataType.FLOW,
            "Data": DataType.ANY
        }

    def register_handlers(self):
        self.register_handler("Flow", self.handle_peek)

    def handle_peek(self, Size=1, **kwargs):
        try:
            result = self.invoke("peek", {"n": Size})
            self.bridge.set(f"{self.node_id}_Data", result, self.name)
            self.bridge.set(f"{self.node_id}_ActivePorts", ["Flow"], self.name)
        except Exception as e:
            self.logger.error(f"Peek Error: {e}")
            self.bridge.set(f"{self.node_id}_ActivePorts", ["Error Flow"], self.name)
        return True

@NodeRegistry.register("File Position", "File System/Operations")
class FilePositionNode(BaseFileOpNode):
    """
    Retrieves the current byte offset of the file pointer.
    
    Useful for tracking progress or saving locations for future Seek operations 
    within a file provider scope.
    
    Inputs:
    - Flow: Trigger the position check.
    
    Outputs:
    - Flow: Pulse triggered on success.
    - Error Flow: Pulse triggered if retrieval fails.
    - Position: The current integer byte offset.
    """
    version = "2.1.0"
    
    def define_schema(self):
        self.input_schema = {"Flow": DataType.FLOW}
        self.output_schema = {
            "Flow": DataType.FLOW,
            "Error Flow": DataType.FLOW,
            "Position": DataType.INT
        }

    def register_handlers(self):
        self.register_handler("Flow", self.handle_tell)

    def handle_tell(self, **kwargs):
        try:
            pos = self.invoke("tell", {})
            self.bridge.set(f"{self.node_id}_Position", pos, self.name)
            self.bridge.set(f"{self.node_id}_ActivePorts", ["Flow"], self.name)
        except Exception as e:
            self.logger.error(f"Position Error: {e}")
            self.bridge.set(f"{self.node_id}_ActivePorts", ["Error Flow"], self.name)
        return True
