from synapse.nodes.registry import NodeRegistry
from synapse.core.types import DataType
from synapse.nodes.lib.provider_node import ProviderNode

@NodeRegistry.register("CSV Data Provider", "Database/Providers")
class CSVDataProviderNode(ProviderNode):
    """
    Exposes a directory of CSV files as a simple database.
    Allows other nodes to read from or write to CSV files within the specified folder.
    
    Inputs:
    - Flow: Trigger to enter the data provider scope.
    - Folder Path: The directory where CSV files are stored.
    
    Outputs:
    - Done: Triggered upon exiting the provider scope.
    - Provider Flow: Active while inside the CSV data context.
    """
    version = "2.1.0"

    def __init__(self, node_id, name, bridge):
        super().__init__(node_id, name, bridge)
        self.provider_type = "Database Provider"
        self.properties["Folder Path"] = "csv_db"

    def define_schema(self):
        super().define_schema()
        self.input_schema["Folder Path"] = DataType.STRING

    def start_scope(self, **kwargs):
        path = kwargs.get("Folder Path") or self.properties.get("Folder Path", "csv_db")
        
        # Call base to register identity and handle Provider Flow
        super().start_scope(**kwargs)
        
        self.logger.info(f"CSV Data Provider initialized at: {path}")
        return True
        

