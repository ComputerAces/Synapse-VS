from synapse.nodes.lib.provider_node import ProviderNode
from synapse.nodes.registry import NodeRegistry
from synapse.core.types import DataType

@NodeRegistry.register("User Provider", "Security/Providers")
class UserProviderNode(ProviderNode):
    """
    Service provider for user identity and permission management.
    Handles user state, roles, groups, and permission category checks.
    
    Inputs:
    - Flow: Start the user provider service.
    
    Outputs:
    - Provider Flow: Active while the provider service is running.
    - Flow: Triggered when the service is stopped.
    """
    version = "2.1.0"

    def __init__(self, node_id, name, bridge):
        super().__init__(node_id, name, bridge)
        self.provider_type = "User Provider"
        self.properties["Username"] = ""
        self.properties["Roles"] = []
        self.properties["Groups"] = []
        self.properties["Permissions"] = []
        self.no_show = ["Username", "Roles", "Groups", "Permissions"]
        self.define_schema()
        self.register_handlers()

    def define_schema(self):
        super().define_schema()

    def register_provider_context(self):
        pass # User setting is dynamic via actions, but state is maintained here

    def set_user(self, username, roles=None, groups=None, permissions=None):
        """Populates the session data."""
        self.properties["Username"] = username
        self.properties["Roles"] = roles or []
        self.properties["Groups"] = groups or []
        self.properties["Permissions"] = permissions or []
        
        # Sync to bridge for others to see
        self.bridge.set(f"{self.node_id}_Username", username, self.name)
        self.bridge.set(f"{self.node_id}_Active", True, self.name)

    def has_permission(self, category):
        """
        Checks if the current user has permission for a specific category.
        Expected format: Lowercase category name (e.g., 'file system')
        """
        tasks = self.properties.get("Permissions", []) # These are the lowercase categories
        
        # Simple string match
        if category.lower() in tasks or "*" in tasks or "Admin" in (self.properties.get("Roles") or []):
            return True
            
        return False
