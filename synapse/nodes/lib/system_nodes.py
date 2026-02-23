import os
import shutil
import zipfile 
from synapse.core.super_node import SuperNode
from synapse.nodes.registry import NodeRegistry
from synapse.core.types import DataType

# Lazy Import winreg (Windows only)
try:
    import winreg
except ImportError:
    winreg = None

@NodeRegistry.register("Environment Var", "System")
class EnvironmentVarNode(SuperNode):
    """
    Manages operating system environment variables (e.g., PATH, HOME).
    
    This node can retrieve (Get), set (Set), or delete (Unset) environment 
    variables. Setting a variable makes it available to the current process 
    and any child processes spawned by Synapse.
    
    Inputs:
    - Flow: Trigger the operation.
    - Variable Name: The key of the environment variable.
    - Variable Value: The new value to set, or empty to retrieve.
    
    Outputs:
    - Flow: Pulse triggered after the operation.
    - Value: The current state of the variable after the operation.
    """
    version = "2.1.0"

    def __init__(self, node_id, name, bridge):
        super().__init__(node_id, name, bridge)
        self.is_native = True
        self.properties["Variable Name"] = ""
        self.properties["Variable Value"] = ""
        self.define_schema()
        self.register_handlers()

    def define_schema(self):
        self.input_schema = {
            "Flow": DataType.FLOW,
            "Variable Name": DataType.STRING,
            "Variable Value": DataType.STRING
        }
        self.output_schema = {
            "Flow": DataType.FLOW,
            "Value": DataType.STRING
        }

    def register_handlers(self):
        self.register_handler("Flow", self.manage_env)

    def manage_env(self, Variable_Name=None, Variable_Value=None, Operation=None, **kwargs):
        var_name = Variable_Name if Variable_Name is not None else self.properties.get("Variable Name", "")
        # Use renamed variable value to avoid collision
        val_input = Variable_Value if Variable_Value is not None else self.properties.get("Variable Value", self.properties.get("Value", ""))
        
        if not var_name:
            self.logger.error("No variable name provided.")
            return False
            
        value_out = ""
        
        # Determine operation based on 'Variable Value' input 
        if val_input is not None and val_input != "": # If a value is provided, it's a 'Set' operation
            op = "Set"
        elif val_input == "": # If an empty string is provided, it's an 'Unset' operation
            op = "Unset"
        else: # Otherwise, it's a 'Get' operation
            op = "Get"

        if op == "Set":
            os.environ[var_name] = str(val_input)
            value_out = str(val_input)
            
        elif op == "Unset":
            os.environ.pop(var_name, None)
            value_out = "" # When unset, the value is effectively empty
            
        else: # Get
            value_out = os.environ.get(var_name, "")
        
        self.bridge.set(f"{self.node_id}_Value", value_out, self.name)
        return True


@NodeRegistry.register("Archive Write", "IO/Files")
class ArchiveWriteNode(SuperNode):
    """
    Compresses files or directories into a ZIP archive.
    
    Inputs:
    - Flow: Trigger the compression process.
    - Source Path: The absolute path of the file or folder to be compressed.
    - Archive Path: The absolute path where the resulting ZIP file will be saved.
    
    Outputs:
    - Flow: Triggered after compression (success or failure).
    - Success: Triggered ONLY if the compression was successful.
    - Result Path: The absolute path to the generated ZIP file.
    """
    version = "2.1.0"

    def __init__(self, node_id, name, bridge):
        super().__init__(node_id, name, bridge)
        self.is_native = True
        self.define_schema()
        self.register_handlers()

    def define_schema(self):
        self.input_schema = {
            "Flow": DataType.FLOW,
            "Source Path": DataType.STRING,
            "Archive Path": DataType.STRING
        }
        self.output_schema = {
            "Flow": DataType.FLOW,
            "Success": DataType.FLOW,
            "Result Path": DataType.STRING
        }

    def register_handlers(self):
        self.register_handler("Flow", self.compress)

    def compress(self, Source_Path=None, Archive_Path=None, **kwargs):
        src = Source_Path if Source_Path is not None else self.properties.get("Source Path", "")
        dst = Archive_Path if Archive_Path is not None else self.properties.get("Archive Path", "")

        if not src:
            self.logger.error("Missing Source Path")
            self.bridge.set(f"{self.node_id}_ActivePorts", ["Flow"], self.name)
            return True

        try:
            base_name = os.path.splitext(dst)[0] if dst else src
            fmt = "zip"
            shutil.make_archive(base_name, fmt, src)
            out_path = f"{base_name}.{fmt}"
            self.bridge.set(f"{self.node_id}_Result Path", out_path, self.name)
            self.logger.info(f"Compressed {src} into {out_path}")
            self.bridge.set(f"{self.node_id}_ActivePorts", ["Success", "Flow"], self.name)
        except Exception as e:
            self.logger.error(f"Compression Error: {e}")
            self.bridge.set(f"{self.node_id}_ActivePorts", ["Flow"], self.name)

        return True


@NodeRegistry.register("Archive Read", "IO/Files")
class ArchiveReadNode(SuperNode):
    """
    Extracts ZIP archives into a targeted destination folder.
    
    Inputs:
    - Flow: Trigger the extraction process.
    - Archive Path: The absolute path to the .zip archive to extract.
    - Destination Folder: The folder path where the contents will be extracted.
    
    Outputs:
    - Flow: Triggered after extraction (success or failure).
    - Success: Triggered ONLY if the extraction was successful.
    - Extracted Path: The absolute path to the folder containing extracted files.
    """
    version = "2.1.0"

    def __init__(self, node_id, name, bridge):
        super().__init__(node_id, name, bridge)
        self.is_native = True
        self.define_schema()
        self.register_handlers()

    def define_schema(self):
        self.input_schema = {
            "Flow": DataType.FLOW,
            "Archive Path": DataType.STRING,
            "Destination Folder": DataType.STRING
        }
        self.output_schema = {
            "Flow": DataType.FLOW,
            "Success": DataType.FLOW,
            "Extracted Path": DataType.STRING
        }

    def register_handlers(self):
        self.register_handler("Flow", self.extract)

    def extract(self, Archive_Path=None, Destination_Folder=None, **kwargs):
        src = Archive_Path if Archive_Path is not None else self.properties.get("Archive Path", "")
        dst = Destination_Folder if Destination_Folder is not None else self.properties.get("Destination Folder", "")

        if not src:
            self.logger.error("Missing Archive Path")
            self.bridge.set(f"{self.node_id}_ActivePorts", ["Flow"], self.name)
            return True

        try:
            out_dir = dst if dst else os.path.splitext(src)[0]
            shutil.unpack_archive(src, out_dir)
            self.bridge.set(f"{self.node_id}_Extracted Path", out_dir, self.name)
            self.logger.info(f"Extracted {src} into {out_dir}")
            self.bridge.set(f"{self.node_id}_ActivePorts", ["Success", "Flow"], self.name)
        except Exception as e:
            self.logger.error(f"Extraction Error: {e}")
            self.bridge.set(f"{self.node_id}_ActivePorts", ["Flow"], self.name)

        return True


@NodeRegistry.register("Registry Modify", "System/Windows")
class RegistryModifyNode(SuperNode):
    """
    Interfaces with the Windows Registry to write or delete keys.
    Requires administrative permissions for some HKEY_LOCAL_MACHINE operations.
    
    Inputs:
    - Flow: Trigger the registry operation.
    - Key Path: The full registry path (e.g., HKEY_CURRENT_USER\Software\Synapse).
    - Value Name: The name of the registry value to target.
    - Value Data: The data to write (used for Write Key action).
    - Action: 'Write' or 'Delete' (Default: Write).
    
    Outputs:
    - Flow: Pulse triggered after the operation completes.
    """
    version = "2.1.0"

    def __init__(self, node_id, name, bridge):
        super().__init__(node_id, name, bridge)
        self.is_native = True
        self.properties["Action"] = "Write" 
        self.properties["Key Path"] = ""
        self.properties["Value Name"] = ""
        self.properties["Value Data"] = ""
        self.define_schema()
        self.register_handlers()

    def define_schema(self):
        self.input_schema = {
            "Flow": DataType.FLOW,
            "Key Path": DataType.STRING,
            "Value Name": DataType.STRING,
            "Value Data": DataType.STRING
        }
        self.output_schema = {
            "Flow": DataType.FLOW
        }

    def register_handlers(self):
        self.register_handler("Flow", self.edit_registry)

    def _parse_root(self, path):
        if not winreg: return None, None
        parts = path.split("\\")
        root_str = parts[0].upper()
        sub_key = "\\".join(parts[1:])
        
        roots = {
            "HKEY_CLASSES_ROOT": winreg.HKEY_CLASSES_ROOT,
            "HKEY_CURRENT_USER": winreg.HKEY_CURRENT_USER,
            "HKEY_LOCAL_MACHINE": winreg.HKEY_LOCAL_MACHINE,
            "HKEY_USERS": winreg.HKEY_USERS,
            "HKEY_CURRENT_CONFIG": winreg.HKEY_CURRENT_CONFIG
        }
        return roots.get(root_str), sub_key

    def edit_registry(self, Key_Path=None, Value_Name=None, Value_Data=None, Action=None, **kwargs):
        key_path = Key_Path if Key_Path is not None else self.properties.get("Key Path", "")
        value_name = Value_Name if Value_Name is not None else self.properties.get("Value Name", "")
        value_data = Value_Data if Value_Data is not None else self.properties.get("Value Data", "")
        action = Action if Action is not None else self.properties.get("Action", "Write")
        
        if not winreg:
            self.logger.error("winreg not available (Windows only).")
            return True

        hkey_root, sub_key = self._parse_root(key_path or "")
        if not hkey_root:
            self.logger.error(f"Invalid Root Key in '{key_path}'")
            return True

        try:
            if "write" in action.lower():
                with winreg.CreateKey(hkey_root, sub_key) as key:
                    winreg.SetValueEx(key, value_name or "", 0, winreg.REG_SZ, str(value_data or ""))
            elif "delete" in action.lower():
                 with winreg.OpenKey(hkey_root, sub_key, 0, winreg.KEY_SET_VALUE) as key:
                     winreg.DeleteValue(key, value_name or "")
        except Exception as e:
            self.logger.error(f"Registry Error: {e}")

        self.bridge.set(f"{self.node_id}_ActivePorts", ["Flow"], self.name)
        return True

@NodeRegistry.register("Registry Read", "System/Windows")
class RegistryReadNode(SuperNode):
    """
    Reads values from the Windows Registry.
    
    Inputs:
    - Flow: Trigger the registry read.
    - Key Path: The full registry path.
    - Value Name: The name of the registry value to read.
    
    Outputs:
    - Flow: Pulse triggered after retrieval.
    - Value: The data retrieved from the registry.
    """
    version = "2.1.0"

    def __init__(self, node_id, name, bridge):
        super().__init__(node_id, name, bridge)
        self.is_native = True
        self.properties["Key Path"] = ""
        self.properties["Value Name"] = ""
        self.define_schema()
        self.register_handlers()

    def define_schema(self):
        self.input_schema = {
            "Flow": DataType.FLOW,
            "Key Path": DataType.STRING,
            "Value Name": DataType.STRING
        }
        self.output_schema = {
            "Flow": DataType.FLOW,
            "Value": DataType.STRING
        }

    def register_handlers(self):
        self.register_handler("Flow", self.read_registry)

    def _parse_root(self, path):
        if not winreg: return None, None
        parts = path.split("\\")
        root_str = parts[0].upper()
        sub_key = "\\".join(parts[1:])
        
        roots = {
            "HKEY_CLASSES_ROOT": winreg.HKEY_CLASSES_ROOT,
            "HKEY_CURRENT_USER": winreg.HKEY_CURRENT_USER,
            "HKEY_LOCAL_MACHINE": winreg.HKEY_LOCAL_MACHINE,
            "HKEY_USERS": winreg.HKEY_USERS,
            "HKEY_CURRENT_CONFIG": winreg.HKEY_CURRENT_CONFIG
        }
        return roots.get(root_str), sub_key

    def read_registry(self, Key_Path=None, Value_Name=None, **kwargs):
        key_path = Key_Path if Key_Path is not None else self.properties.get("Key Path", "")
        value_name = Value_Name if Value_Name is not None else self.properties.get("Value Name", "")
        
        if not winreg:
            self.logger.error("winreg not available (Windows only).")
            return True

        hkey_root, sub_key = self._parse_root(key_path or "")
        if not hkey_root:
            self.logger.error(f"Invalid Root Key in '{key_path}'")
            return True

        try:
            with winreg.OpenKey(hkey_root, sub_key, 0, winreg.KEY_READ) as key:
                value, type_ = winreg.QueryValueEx(key, value_name or "")
                self.bridge.set(f"{self.node_id}_Value", str(value), self.name)
        except Exception as e:
            self.logger.error(f"Registry Error: {e}")
            self.bridge.set(f"{self.node_id}_Value", "", self.name)

        self.bridge.set(f"{self.node_id}_ActivePorts", ["Flow"], self.name)
        return True
