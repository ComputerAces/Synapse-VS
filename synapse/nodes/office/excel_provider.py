from synapse.nodes.registry import NodeRegistry
from synapse.core.types import DataType
from synapse.nodes.lib.provider_node import ProviderNode

@NodeRegistry.register("Excel Provider", "IO/Documents")
class ExcelProviderNode(ProviderNode):
    """
    Establishes an automation environment for Microsoft Excel workbooks.
    
    This provider manages the lifecycle of an Excel application instance, 
    allowing downstream 'Excel Commander' nodes to execute within a shared context.
    
    Inputs:
    - Flow: Open Excel and load the specified workbook.
    - Provider End: Close the workbook and shut down Excel.
    - File Path: The absolute path to the workbook (.xlsx, .xls).
    
    Outputs:
    - Provider Flow: Active while the spreadsheet is open.
    - Provider ID: Identifier for automation node targeting.
    - Flow: Pulse triggered after the scope is closed.
    """
    version = "2.1.0"

    def __init__(self, node_id, name, bridge):
        self.provider_type = "Excel Provider"
        super().__init__(node_id, name, bridge)
        self.properties["File Path"] = ""

    def define_schema(self):
        super().define_schema()
        self.input_schema["File Path"] = DataType.STRING

    def register_handlers(self):
        super().register_handlers()
        self.register_handler("Flow", self.start_scope)

    def start_scope(self, File_Path=None, **kwargs):
        path = File_Path if File_Path is not None else kwargs.get("File Path") or self.properties.get("File Path", "")
        self.bridge.set(f"{self.node_id}_File Path", path, self.name)
        return super().start_scope(**kwargs)
