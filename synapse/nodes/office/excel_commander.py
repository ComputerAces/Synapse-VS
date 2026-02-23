from synapse.core.super_node import SuperNode
from synapse.nodes.registry import NodeRegistry
from synapse.core.types import DataType

@NodeRegistry.register("Excel Commander", "IO/Documents")
class ExcelCommanderNode(SuperNode):
    """
    Executes automated commands or macros within an Excel workbook.
    
    This node interacts with an active Excel Provider scope. If no provider 
    is active, it can optionally open a file directly if 'File Path' is provided.
    
    Inputs:
    - Flow: Trigger command execution.
    - File Path: The absolute path to the workbook (optional if using a Provider).
    - Command: The instruction or macro name to execute.
    
    Outputs:
    - Flow: Pulse triggered after the command completes.
    - Result: The return value or status from Excel.
    """
    version = "2.1.0"

    required_providers = ["Excel Provider"]
    
    def __init__(self, node_id, name, bridge):
        super().__init__(node_id, name, bridge)
        self.is_native = True
        self.properties["File Path"] = ""
        self.properties["Command"] = ""
        self.define_schema()
        self.register_handlers()

    def define_schema(self):
        self.input_schema = {
            "Flow": DataType.FLOW,
            "File Path": DataType.STRING,
            "Command": DataType.STRING
        }
        self.output_schema = {
            "Flow": DataType.FLOW,
            "Result": DataType.ANY
        }

    def register_handlers(self):
        self.register_handler("Flow", self.run_command)

    def run_command(self, File_Path=None, Command=None, **kwargs):
        path = File_Path if File_Path is not None else kwargs.get("File Path") or self.properties.get("File Path", "")
        if not path:
            provider_id = self.get_provider_id("Excel Provider")
            if provider_id:
                path = self.bridge.get(f"{provider_id}_File Path")
        
        cmd = Command or kwargs.get("Command") or self.properties.get("Command")
        
        # logic... (Placeholder for actual automation logic)
        result = f"Executed: {cmd} on {path}"
        self.logger.info(result)
        self.bridge.set(f"{self.node_id}_Result", result, self.name)
        
        self.bridge.set(f"{self.node_id}_ActivePorts", ["Flow"], self.name)
        return True
