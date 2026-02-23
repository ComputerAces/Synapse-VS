from synapse.nodes.registry import NodeRegistry
from synapse.nodes.lib.provider_node import ProviderNode
from synapse.core.types import DataType

@NodeRegistry.register("Logging Provider", "System/Debug")
class LoggingProviderNode(ProviderNode):
    """
    Registers the primary logging service for the graph session.
    
    Initializes a provider context that allows other 'Log' nodes to 
    record messages to a centralized file or stream. It sets up 
    rotations and file handles used throughout the execution.
    
    Inputs:
    - Flow: Trigger the provider initialization.
    - File Path: The target log file for the session.
    
    Outputs:
    - Done: Pulse triggered once the service is ready.
    """
    version = "2.1.0"

    def __init__(self, node_id, name, bridge):
        super().__init__(node_id, name, bridge)
        self.provider_type = "Logging Provider"
        self.properties["FilePath"] = "scoped_session.log"

    def define_schema(self):
        super().define_schema()
        self.input_schema["File Path"] = DataType.STRING

    def start_scope(self, **kwargs):
        file_path = kwargs.get("File Path") or self.properties.get("FilePath")
        self.bridge.set(f"{self.node_id}_File Path", file_path, self.name)
        self.bridge.set(f"{self.node_id}_Provider Type", self.provider_type, self.name)
        
        return super().start_scope(**kwargs)

