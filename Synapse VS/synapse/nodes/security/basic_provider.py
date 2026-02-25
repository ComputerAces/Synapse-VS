import time
from synapse.nodes.registry import NodeRegistry
from synapse.core.types import DataType
from synapse.nodes.security.base import SecurityProviderNode

@NodeRegistry.register("Basic Security Provider", "Security/Providers")
class BasicSecurityProvider(SecurityProviderNode):
    """
    Provides standard database-backed security services including authentication and authorization.
    Connects to a Database Provider to store and retrieve user, group, and role information.
    
    Inputs:
    - Flow: Trigger to enter the security scope.
    - Table Name: The database table used for storing user data (default: 'Users').
    - Use Verify: If True, enables stricter session verification.
    
    Outputs:
    - Done: Triggered upon exiting the security scope.
    - Provider Flow: Active while inside the security context.
    """
    version = "2.1.0"

    def __init__(self, node_id, name, bridge):
        super().__init__(node_id, name, bridge)
        self.required_providers = ["Database Provider"]
        self.properties["Table Name"] = "Users"
        self.properties["Use Verify"] = False
        
        self.define_schema()
        # ProviderNode handles handlers, but we need to register context

    def define_schema(self):
        super().define_schema()

        # Inputs
        self.input_schema.update({
            "Table Name": DataType.STRING,
            "Use Verify": DataType.BOOLEAN
        })

        # No extra outputs (Authenticated/Token moved to Gateway)
        pass

        # Handlers
        self.register_handler("Flow", self.execute_flow)

    def register_provider_context(self):
        # AUTO DISCOVERY of DB Connection from parent Database Provider
        db_pid = self.get_provider_id("Database Provider")
        Connection = None
        if db_pid:
            Connection = self.bridge.get(f"{db_pid}_Connection")

        table = self.properties.get("Table Name", "Users")
        use_verify = self.properties.get("Use Verify", False)

        if Connection:
            self.logger.info(f"DB Connection active ({db_pid}). Prepared for Table: {table}")
        else:
            self.logger.warning("No Database Connection found in context flow.")
        
        self.bridge.set(f"{self.node_id}_Provider ID", self.node_id, self.name)
        self.bridge.set(f"{self.node_id}_Provider Type", self.provider_type, self.name)
        self.bridge.set(f"{self.node_id}_Use Verify", use_verify, self.name)
        
        # [RELAY] Store Connection and Table Name for Security Actions
        self.bridge.set(f"{self.node_id}_Connection", Connection, self.name)
        self.bridge.set(f"{self.node_id}_Table Name", table, self.name)

    def execute_flow(self, **kwargs):
        # Update properties from inputs if provided
        if "Table Name" in kwargs:
            self.properties["Table Name"] = kwargs["Table Name"]
        if "Use Verify" in kwargs:
            self.properties["Use Verify"] = kwargs["Use Verify"]

        # [REGISTRY] Register identity and trigger Provider Flow
        self.register_provider_context()
        self.bridge.set(f"{self.node_id}_ActivePorts", ["Provider Flow"], self.name)
        return True

    def execute(self, **kwargs):
        # The execute method is now primarily handled by registered handlers.
        # This method can be kept for backward compatibility or removed if not needed.
        # For this refactor, we'll delegate to the handler if 'Flow' is the trigger.
        trigger = kwargs.get("_trigger", "Flow")
        if trigger == "Flow":
            return self.execute_flow(**kwargs)
        return super().execute(**kwargs)
