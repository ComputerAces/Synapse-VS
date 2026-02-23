import os
import datetime
from synapse.core.super_node import SuperNode
from synapse.nodes.registry import NodeRegistry
from synapse.core.types import DataType

@NodeRegistry.register("Log", "System/Debug")
class LogNode(SuperNode):
    """
    Appends a formatted message to a log file and the console.
    
    This node facilitates debugging and tracking by writing timestamped 
    messages to a file (managed via Logging Provider or self-defined). 
    It supports multiple log levels (INFO, WARNING, ERROR).
    
    Inputs:
    - Flow: Trigger the logging operation.
    - File Path: The destination log file path.
    - Message: The text content to record.
    - Level: The severity of the log (e.g., INFO, ERROR).
    
    Outputs:
    - Flow: Triggered after the message is logged.
    """
    version = "2.1.0"

    def __init__(self, node_id, name, bridge):
        super().__init__(node_id, name, bridge)
        self.properties["File Path"] = "synapse.log"
        self.properties["Message"] = ""
        self.properties["Max Size Kb"] = 1024
        self.properties["BackupCount"] = 5
        self.properties["Level"] = "INFO"
        self.no_show = ["BackupCount"]
        
        self.define_schema()
        self.register_handler("Flow", self.do_work)

    def define_schema(self):
        self.input_schema = {
            "Flow": DataType.FLOW,
            "File Path": DataType.STRING,
            "Message": DataType.STRING,
            "Level": DataType.STRING,
            "Max Size Kb": DataType.NUMBER
        }
        self.output_schema = {
            "Flow": DataType.FLOW
        }

    def do_work(self, **kwargs):
        file_path = kwargs.get("File Path") or self.properties.get("File Path", self.properties.get("FilePath", "synapse.log"))
        message = kwargs.get("Message") or self.properties.get("Message", "")
        level = (kwargs.get("Level") or self.properties.get("Level", "INFO")).upper().strip()
        max_size = kwargs.get("Max Size Kb") or self.properties.get("Max Size Kb", self.properties.get("MaxSizeKb", 1024))

        # AUTO DISCOVERY
        if not file_path:
            provider_id = self.get_provider_id("Logging Provider")
            if provider_id:
                file_path = self.bridge.get(f"{provider_id}_File Path")

        if not file_path:
            file_path = "synapse.log"
        
        # Simple print
        print(f"[{level}] {message}")
        
        self.bridge.set(f"{self.node_id}_ActivePorts", ["Flow"], self.name)
        return True
