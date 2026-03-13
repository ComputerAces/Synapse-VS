from axonpulse.core.super_node import SuperNode

from axonpulse.nodes.registry import NodeRegistry

from axonpulse.core.types import DataType

from axonpulse.utils.logger import main_logger as logger

from typing import Any, List, Dict, Optional

from axonpulse.core.types import DataType, TypeCaster

from axonpulse.nodes.decorators import axon_node

@axon_node(category="Security/RBAC", version="2.3.0", node_label="Gatekeeper", outputs=['Authorized', 'Access Denied', 'Identity'])
def GatekeeperNode(App_ID: str, User_Name: str, Password: str, Token: Any, _bridge: Any = None, _node: Any = None, _node_id: str = None, **kwargs) -> Any:
    """Validates user identity and session tokens within a scoped application context.

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
- Identity: The user profile data of the authorized identity."""
    app_id = kwargs.get('App ID') or _node.properties.get('App ID', 'Global')
    if app_id == 'Global':
        _node.logger.info(f'Gatekeeper passed for System Flow.')
        _bridge.set(f'{_node_id}_ActivePorts', ['Authorized'], _node.name)
        return
    else:
        pass
    identity = _bridge.get_identity(app_id)
    is_authorized = False
    if identity:
        is_authorized = True
    elif app_id == 'Global':
        is_authorized = True
    else:
        _node.logger.warning(f"Flow validation failed: No Identity found for App ID '{app_id}'")
    if is_authorized:
        _node.logger.info(f"Context '{app_id}' AUTHORIZED.")
        ident_data = identity.to_dict() if identity else {'username': 'System', 'roles': ['system']}
        _bridge.set(f'{_node_id}_ActivePorts', ['Authorized'], _node.name)
    else:
        _node.logger.warning(f"Context '{app_id}' ACCESS DENIED. (Missing roles: {required_roles})")
        _bridge.set(f'{_node_id}_ActivePorts', ['Access Denied'], _node.name)
    return {'Identity': {'username': 'System', 'roles': ['admin']}, 'Identity': ident_data}
