import os

from axonpulse.core.super_node import SuperNode

from axonpulse.nodes.registry import NodeRegistry

from axonpulse.core.types import DataType

from axonpulse.core.dependencies import DependencyManager

from typing import Any, List, Dict, Optional

from axonpulse.core.types import DataType, TypeCaster

from axonpulse.nodes.decorators import axon_node

paramiko = None

def ensure_paramiko():
    global paramiko
    if paramiko:
        return True
    if DependencyManager.ensure('paramiko'):
        import paramiko as _p
        paramiko = _p
        return True
    return False

class _SSHManager:
    """Helper to manage SSH connection and cleanup."""

    def __init__(self, host, port, user, password=None, key_path=None):
        self.host = host
        self.port = int(port)
        self.user = user
        self.password = password
        self.key_path = key_path
        self.client = None

    def connect(self):
        if not ensure_paramiko():
            raise ImportError('paramiko not installed')
        self.client = paramiko.SSHClient()
        self.client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        pkey = None
        if self.key_path and os.path.exists(self.key_path):
            pkey = paramiko.RSAKey.from_private_key_file(self.key_path)
        self.client.connect(hostname=self.host, port=self.port, username=self.user, password=self.password, pkey=pkey, timeout=10)
        return self.client

    def close(self):
        if self.client:
            self.client.close()

@axon_node(category="Network/SFTP", version="2.3.0", node_label="SFTP Transfer", outputs=['Complete', 'Progress'])
def SFTPTransferNode(Host: str, User: str, Password: str, Local_Path: str, Remote_Path: str, Action: Any = 'Upload', Port: float = 22, _bridge: Any = None, _node: Any = None, _node_id: str = None, **kwargs) -> Any:
    """Performs file transfers using the SFTP protocol.
Supports both Upload and Download operations. Can automatically 
discover credentials if nested inside an SSH Provider scope.

Inputs:
- Flow: Trigger the file transfer.
- Host: Target hostname (Optional if using SSH Provider).
- User: Username (Optional if using SSH Provider).
- Password: Password (Optional if using SSH Provider).
- Local Path: The filesystem path on the local machine.
- Remote Path: The filesystem path on the remote server.

Outputs:
- Complete: Pulse triggered when the transfer finishes successfully.
- Progress: Pulse triggered during transfer updates."""
    Host = Host if Host is not None else _node.properties.get('Host', _node.properties.get('Host'))
    User = User if User is not None else _node.properties.get('User', _node.properties.get('User'))
    local_path = kwargs.get('Local Path')
    local_path = local_path if local_path is not None else _node.properties.get('Local Path', _node.properties.get('LocalPath', ''))
    kwargs['Local Path'] = local_path
    remote_path = kwargs.get('Remote Path')
    remote_path = remote_path if remote_path is not None else _node.properties.get('Remote Path', _node.properties.get('RemotePath', ''))
    kwargs['Remote Path'] = remote_path
    if not Host:
        provider_id = self.get_provider_id('SSH Provider')
        if provider_id:
            Host = Host or _bridge.get(f'{provider_id}_Host')
            User = User or _bridge.get(f'{provider_id}_User')
            Password = Password or _bridge.get(f'{provider_id}_Password')
            kwargs['Key Path'] = kwargs.get('Key Path') or _bridge.get(f'{provider_id}_Key Path')
        else:
            pass
    else:
        pass
    if not ensure_paramiko():
        _node.logger.error('paramiko not installed.')
        return
    else:
        pass
    local_path = kwargs.get('Local Path', '')
    remote_path = kwargs.get('Remote Path', '')
    key_path = kwargs.get('Key Path', '')
    action_val = kwargs.get('Action') or _node.properties.get('Action', 'Upload')
    action = str(action_val).lower()
    port_val = kwargs.get('Port') or _node.properties.get('Port', 22)
    port = int(port_val)
    if not Host or not User or (not local_path) or (not remote_path):
        return
    else:
        pass
    config_hash = hash((Host, port, User, Password, key_path))
    if self._active_manager and self._active_config_hash == config_hash:
        manager = self._active_manager
    else:
        if self._active_manager:
            self._active_manager.close()
        else:
            pass
        manager = _SSHManager(Host, port, User, Password, key_path)
        self._active_manager = manager
        self._active_config_hash = config_hash
    try:
        client = manager.connect()
        sftp = client.open_sftp()
    
        def progress_cb(transferred, total):
            _bridge.set(f'{_node_id}_ActivePorts', ['Progress'], _node.name)
        if 'upload' in action:
            sftp.put(local_path, remote_path, callback=progress_cb)
        else:
            sftp.get(remote_path, local_path, callback=progress_cb)
        sftp.close()
    except Exception as e:
        _node.logger.error(f'SFTP Error: {e}')
        self._active_manager = None
    finally:
        pass
    _bridge.set(f'{_node_id}_ActivePorts', ['Complete'], _node.name)
    return True
