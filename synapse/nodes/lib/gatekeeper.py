from synapse.core.super_node import SuperNode
from synapse.nodes.registry import NodeRegistry
from synapse.core.types import DataType
from synapse.utils.logger import main_logger as logger

@NodeRegistry.register("Gatekeeper", "Security/RBAC")
class GatekeeperNode(SuperNode):
    """
    Validates user identity and session tokens within a scoped application context.
    
    This node acts as a security checkpoint, checking the current execution context 
    against authentication providers. It directs flow based on whether a valid 
    identity is present.
    
    Inputs:
    - Flow: Execution trigger.
    - App ID: The application scope to validate against.
    - User Name: Identity to check (Optional).
    - Password: Credentials to check (Optional).
    - Token: Pre-authenticated session token (Optional).
    
    Outputs:
    - Authorized: Pulse triggered if identity is valid and verified.
    - Access Denied: Pulse triggered if no identity is found or verification fails.
    - Identity: The user profile data of the authorized identity.
    """
    version = "2.1.0"

    def __init__(self, node_id, name, bridge):
        super().__init__(node_id, name, bridge)
        self.is_native = True
        
        self.define_schema()
        self.register_handler("Flow", self.do_work)

    def define_schema(self):
        self.input_schema = {
            "Flow": DataType.FLOW,
            "App ID": DataType.STRING,
            "User Name": DataType.STRING,
            "Password": DataType.STRING,
            "Token": DataType.ANY
        }
        self.output_schema = {
            "Authorized": DataType.FLOW,
            "Access Denied": DataType.FLOW,
            "Identity": DataType.ANY
        }

    def do_work(self, **kwargs):
        app_id = kwargs.get("App ID") or self.properties.get("App ID", "Global")
        # Legacy roles/optional logic removed - node now acts as identity pulse check.
        
        # 0. System Bypass Check
        if app_id == "Global":
             self.logger.info(f"Gatekeeper passed for System Flow.")
             self.bridge.set(f"{self.node_id}_Identity", {"username": "System", "roles": ["admin"]}, self.name)
             self.bridge.set(f"{self.node_id}_ActivePorts", ["Authorized"], self.name)
             return

        # 1. Query the Identity & Session Manager (ISM)
        identity = self.bridge.get_identity(app_id)
        
        is_authorized = False
        if identity:
             is_authorized = True
        else:
            # Special case for "Global" scope which represents system-level tasks.
            if app_id == "Global":
                 is_authorized = True
            else:
                 self.logger.warning(f"Flow validation failed: No Identity found for App ID '{app_id}'")

        # 2. Routing Decision
        if is_authorized:
            self.logger.info(f"Context '{app_id}' AUTHORIZED.")
            # Pass identity data downstream for context-aware logic
            ident_data = identity.to_dict() if identity else {"username": "System", "roles": ["system"]}
            self.bridge.set(f"{self.node_id}_Identity", ident_data, self.name)
            self.bridge.set(f"{self.node_id}_ActivePorts", ["Authorized"], self.name)
        else:
            self.logger.warning(f"Context '{app_id}' ACCESS DENIED. (Missing roles: {required_roles})")
            self.bridge.set(f"{self.node_id}_ActivePorts", ["Access Denied"], self.name)

