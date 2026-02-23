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

@NodeRegistry.register("SFTP Transfer", "Network/SFTP")
class SFTPTransferNode(SuperNode):
    """
    Performs file transfers using the SFTP protocol.
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
    - Progress: Pulse triggered during transfer updates.
    """
    version = "2.1.0"

    def __init__(self, node_id, name, bridge):
        super().__init__(node_id, name, bridge)
        self.is_native = True
        self.properties["Action"] = "Upload" # Upload, Download
        self.properties["Port"] = 22
        self._active_manager = None
        self._active_config_hash = None
        
        self.define_schema()
        self.register_handler("Flow", self.transfer_file)

    def define_schema(self):
        self.input_schema = {
            "Flow": DataType.FLOW,
            "Action": DataType.FTPACTIONS,
            "Port": DataType.NUMBER,
            "Host": DataType.STRING,
            "User": DataType.STRING,
            "Password": DataType.STRING,
            "Local Path": DataType.STRING,
            "Remote Path": DataType.STRING
        }
        self.output_schema = {
            "Complete": DataType.FLOW,
            "Progress": DataType.FLOW
        }

    def transfer_file(self, Host=None, User=None, Password=None, **kwargs):
        # Fallback to properties
        Host = Host if Host is not None else self.properties.get("Host", self.properties.get("Host"))
        User = User if User is not None else self.properties.get("User", self.properties.get("User"))
        local_path = kwargs.get("Local Path")
        local_path = local_path if local_path is not None else self.properties.get("Local Path", self.properties.get("LocalPath", ""))
        kwargs["Local Path"] = local_path
        
        remote_path = kwargs.get("Remote Path")
        remote_path = remote_path if remote_path is not None else self.properties.get("Remote Path", self.properties.get("RemotePath", ""))
        kwargs["Remote Path"] = remote_path

        # 1. OPTIMIZED AUTO DISCOVERY - Only if info missing
        if not Host:
            provider_id = self.get_provider_id("SSH Provider")
            if provider_id:
                Host = Host or self.bridge.get(f"{provider_id}_Host")
                User = User or self.bridge.get(f"{provider_id}_User")
                Password = Password or self.bridge.get(f"{provider_id}_Password")
                kwargs["Key Path"] = kwargs.get("Key Path") or self.bridge.get(f"{provider_id}_Key Path")

        if not ensure_paramiko():
            self.logger.error("paramiko not installed.")
            return

        local_path = kwargs.get("Local Path", "")
        remote_path = kwargs.get("Remote Path", "")
        key_path = kwargs.get("Key Path", "")
        
        action_val = kwargs.get("Action") or self.properties.get("Action", "Upload")
        action = str(action_val).lower()
        
        port_val = kwargs.get("Port") or self.properties.get("Port", 22)
        port = int(port_val)

        if not Host or not User or not local_path or not remote_path:
            return

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
            sftp = client.open_sftp()
            
            def progress_cb(transferred, total):
                self.bridge.set(f"{self.node_id}_ActivePorts", ["Progress"], self.name)

            if "upload" in action:
                sftp.put(local_path, remote_path, callback=progress_cb)
            else:
                sftp.get(remote_path, local_path, callback=progress_cb)
                
            sftp.close()
            
        except Exception as e:
            self.logger.error(f"SFTP Error: {e}")
            self._active_manager = None # Reset on error
        
        self.bridge.set(f"{self.node_id}_ActivePorts", ["Complete"], self.name)
