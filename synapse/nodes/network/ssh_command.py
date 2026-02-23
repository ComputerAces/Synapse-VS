import os
from synapse.core.super_node import SuperNode
from synapse.nodes.registry import NodeRegistry
from synapse.core.types import DataType
from synapse.core.dependencies import DependencyManager

# Lazy Global
paramiko = None

def ensure_paramiko():
    global paramiko
    if paramiko: return True
    if DependencyManager.ensure("paramiko"):
        import paramiko as _p; paramiko = _p; return True
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
        if not ensure_paramiko(): raise ImportError("paramiko not installed")
        
        self.client = paramiko.SSHClient()
        self.client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        
        pkey = None
        if self.key_path and os.path.exists(self.key_path):
            pkey = paramiko.RSAKey.from_private_key_file(self.key_path)
            
        self.client.connect(
            hostname=self.host,
            port=self.port,
            username=self.user,
            password=self.password,
            pkey=pkey,
            timeout=10
        )
        return self.client

    def close(self):
        if self.client:
            self.client.close()

@NodeRegistry.register("SSH Command", "Network/SSH")
class SSHCommandNode(SuperNode):
    """
    Executes a shell command on a remote server via SSH.
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
    - Exit Code: The process return code.
    """
    version = "2.1.0"

    def __init__(self, node_id, name, bridge):
        super().__init__(node_id, name, bridge)
        self.is_native = True
        self.properties["Port"] = 22
        self._active_manager = None
        self._active_config_hash = None
        
        self.define_schema()
        self.register_handler("Flow", self.execute_command)

    def define_schema(self):
        self.input_schema = {
            "Flow": DataType.FLOW,
            "Port": DataType.NUMBER,
            "Host": DataType.STRING,
            "User": DataType.STRING,
            "Password": DataType.STRING,
            "Key Path": DataType.STRING,
            "Command": DataType.STRING
        }
        self.output_schema = {
            "Flow": DataType.FLOW,
            "Stdout": DataType.STRING,
            "Stderr": DataType.STRING,
            "Exit Code": DataType.NUMBER
        }

    def execute_command(self, Host=None, User=None, Password=None, Command=None, **kwargs):
        Host = Host if Host is not None else kwargs.get("Host") or self.properties.get("Host", self.properties.get("Host"))
        User = User if User is not None else kwargs.get("User") or self.properties.get("User", self.properties.get("User"))
        Command = Command if Command is not None else kwargs.get("Command") or self.properties.get("Command", self.properties.get("Command", ""))
        
        # 1. OPTIMIZED AUTO DISCOVERY - Only if still missing info
        if not Host:
            provider_id = self.get_provider_id("SSH Provider")
            if provider_id:
                Host = Host or self.bridge.get(f"{provider_id}_Host")
                User = User or self.bridge.get(f"{provider_id}_User")
                Password = Password or self.bridge.get(f"{provider_id}_Password")
                kwargs["Key Path"] = kwargs.get("Key Path") or self.bridge.get(f"{provider_id}_Key Path")

        if not ensure_paramiko():
            self.logger.error("paramiko not installed.")
            self.bridge.set(f"{self.node_id}_ActivePorts", ["Flow"], self.name)
            return True

        key_path = kwargs.get("Key Path", "")
        
        port_val = kwargs.get("Port") or self.properties.get("Port", 22)
        port = int(port_val)
        
        if not Host or not User or not Command:
            self.logger.error("Missing Host, User, or Command.")
            self.bridge.set(f"{self.node_id}_ActivePorts", ["Flow"], self.name)
            return True

        # 2. Connection Persistence
        config_hash = hash((Host, port, User, Password, key_path))
        if self._active_manager and self._active_config_hash == config_hash:
            manager = self._active_manager
        else:
            if self._active_manager: self._active_manager.close()
            manager = _SSHManager(Host, port, User, Password, key_path)
            self._active_manager = manager
            self._active_config_hash = config_hash

        try:
            client = manager.connect()
            stdin, stdout, stderr = client.exec_command(Command)
            
            exit_code = stdout.channel.recv_exit_status()
            out_str = stdout.read().decode().strip()
            err_str = stderr.read().decode().strip()
            
            self.bridge.set(f"{self.node_id}_Stdout", out_str, self.name)
            self.bridge.set(f"{self.node_id}_Stderr", err_str, self.name)
            self.bridge.set(f"{self.node_id}_Exit Code", exit_code, self.name)
            
        except Exception as e:
            self.logger.error(f"SSH Error: {e}")
            self.bridge.set(f"{self.node_id}_Stderr", str(e), self.name)
            self.bridge.set(f"{self.node_id}_Exit Code", -1, self.name)
            self._active_manager = None # Reset on error

        self.bridge.set(f"{self.node_id}_ActivePorts", ["Flow"], self.name)
        return True
