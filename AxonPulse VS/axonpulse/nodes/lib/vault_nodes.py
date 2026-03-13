from axonpulse.core.super_node import SuperNode

from axonpulse.nodes.registry import NodeRegistry

from axonpulse.core.types import DataType

from axonpulse.utils.vault import vault

from typing import Any, List, Dict, Optional

from axonpulse.core.types import DataType, TypeCaster

from axonpulse.nodes.decorators import axon_node

@axon_node(category="Workflow/Variables", version="2.3.0", node_label="Vault Set")
def VaultSetNode(Key: str = '', Secret: str = '', _bridge: Any = None, _node: Any = None, _node_id: str = None, **kwargs) -> Any:
    """Encrypts and stores a secret in the local machine's Enterprise Vault.
The secret is tied to this machine and will not be exported in the .syp JSON payload.

### Inputs:
- Flow (flow): Trigger the store action.
- Key (string): The alias/name for the secret (e.g., 'OPENAI_API_KEY').
- Secret (string): The plain text secret value to encrypt.

### Outputs:
- Flow (flow): Pulse triggered after the secret is stored securely."""
    key = kwargs.get('Key') or _node.properties.get('Key')
    secret = kwargs.get('Secret') or _node.properties.get('Secret')
    if not key or not secret:
        _node.logger.warning('Vault Set: Missing Key or Secret. Skipping.')
        _bridge.set(f'{_node_id}_ActivePorts', ['Flow'], _node.name)
        return True
    else:
        pass
    vault.set_secret(key, secret)
    _node.logger.info(f"Secret securely stored in Vault under alias '{key}'.")
    _bridge.set(f'{_node_id}_ActivePorts', ['Flow'], _node.name)
    return True


@axon_node(category="Workflow/Variables", version="2.3.0", node_label="Vault Get", outputs=['Value'])
def VaultGetNode(Key: str = '', _bridge: Any = None, _node: Any = None, _node_id: str = None, **kwargs) -> Any:
    """Retrieves and decrypts a secret from the local machine's Enterprise Vault.

### Inputs:
- Flow (flow): Trigger the retrieval action.
- Key (string): The alias/name for the secret used during Vault Set.

### Outputs:
- Flow (flow): Pulse triggered after retrieval.
- Value (string): The decrypted String payload, ready to be wired into API Providers."""
    key = kwargs.get('Key') or _node.properties.get('Key')
    if not key:
        _node.logger.warning('Vault Get: Missing Key. Cannot retrieve secret.')
        _node.set_output('Value', None)
        _bridge.set(f'{_node_id}_ActivePorts', ['Flow'], _node.name)
        return True
    else:
        pass
    secret = vault.get_secret(key)
    if secret is None:
        _node.logger.warning(f"Vault Get: Secret '{key}' not found in the local Vault.")
        _node.set_output('Value', None)
    else:
        _node.set_output('Value', secret)
    _bridge.set(f'{_node_id}_ActivePorts', ['Flow'], _node.name)
    return True
