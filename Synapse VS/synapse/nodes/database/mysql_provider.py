from synapse.nodes.registry import NodeRegistry
from synapse.core.types import DataType
from synapse.nodes.lib.provider_node import ProviderNode

@NodeRegistry.register("MySQL Provider", "Database/Providers")
class MySQLProviderNode(ProviderNode):
    """
    Provides a connection to a MySQL database server.
    
    Inputs:
    - Flow: Execution trigger.
    - Host: Server hostname or IP address.
    - User: Username for authentication.
    - Password: Password for authentication.
    - Database: Name of the database to connect to.
    - Port: Connection port (default 3306).
    
    Outputs:
    - Flow: Triggered when the provider is initialized.
    """
    version = "2.1.0"

    def __init__(self, node_id, name, bridge):
        super().__init__(node_id, name, bridge)
        self.provider_type = "DATABASE"
        self.properties["Host"] = "localhost"
        self.properties["User"] = "root"
        self.properties["Password"] = ""
        self.properties["Database"] = ""
        self.properties["Port"] = 3306

    def define_schema(self):
        super().define_schema()
        self.input_schema.update({
            "Host": DataType.STRING,
            "User": DataType.STRING,
            "Password": DataType.STRING,
            "Database": DataType.STRING,
            "Port": DataType.INTEGER
        })

    def start_scope(self, **kwargs):
        # Fallback with legacy support
        host = kwargs.get("Host") or self.properties.get("Host", self.properties.get("Host"))
        user = kwargs.get("User") or self.properties.get("User", self.properties.get("User"))
        password = kwargs.get("Password") or self.properties.get("Password", self.properties.get("Password"))
        database = kwargs.get("Database") or self.properties.get("Database", self.properties.get("Database"))
        port = kwargs.get("Port") or self.properties.get("Port", self.properties.get("Port", 3306))
        
        config = {
            "type": "mysql",
            "host": host,
            "user": user,
            "password": password,
            "database": database,
            "port": int(port)
        }
        self.bridge.set(f"{self.node_id}_Connection", config, self.name)
        self.logger.info(f"MySQL connection configured for {user}@{host}/{database}")
        
        return super().start_scope(**kwargs)

