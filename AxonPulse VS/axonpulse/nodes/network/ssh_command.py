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

@axon_node(category="Network/SSH", version="2.3.0", node_label="SSH Command", outputs=['Stdout', 'Stderr', 'Exit Code'])
def SSHCommandNode(Host: str, User: str, Password: str, Key_Path: str, Command: str, Port: float = 22, _bridge: Any = None, _node: Any = None, _node_id: str = None, **kwargs) -> Any:
    """Executes a shell command on a remote server via SSH.
Supports authentication via password or private key files.

Inputs:
- Flow: Trigger the command execution.
- Host: Remote server address.
- User: SSH username.
- Password: SSH password.
- Key Path: Path to an optional RSA private key file.
- Command: The shell command to execute.

Outputs:
- Flow: Triggered after command execution.
- Stdout: Standard output from the command.
- Stderr: Standard error from the command.
- Exit Code: The process return code."""
    Host = Host if Host is not None else kwargs.get('Host') or _node.properties.get('Host', _node.properties.get('Host'))
    User = User if User is not None else kwargs.get('User') or _node.properties.get('User', _node.properties.get('User'))
    Command = Command if Command is not None else kwargs.get('Command') or _node.properties.get('Command', _node.properties.get('Command', ''))
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
        _bridge.set(f'{_node_id}_ActivePorts', ['Flow'], _node.name)
    else:
        pass
    key_path = kwargs.get('Key Path', '')
    port_val = kwargs.get('Port') or _node.properties.get('Port', 22)
    port = int(port_val)
    if not Host or not User or (not Command):
        _node.logger.error('Missing Host, User, or Command.')
        _bridge.set(f'{_node_id}_ActivePorts', ['Flow'], _node.name)
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
        (stdin, stdout, stderr) = client.exec_command(Command)
        exit_code = stdout.channel.recv_exit_status()
        out_str = stdout.read().decode().strip()
        err_str = stderr.read().decode().strip()
    except Exception as e:
        _node.logger.error(f'SSH Error: {e}')
        self._active_manager = None
    finally:
        pass
    _bridge.set(f'{_node_id}_ActivePorts', ['Flow'], _node.name)
    return {'Stdout': out_str, 'Stderr': err_str, 'Exit Code': exit_code, 'Stderr': str(e), 'Exit Code': -1}
