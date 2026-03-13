import os

import shutil

import zipfile

from axonpulse.core.super_node import SuperNode

from axonpulse.nodes.registry import NodeRegistry

from axonpulse.core.types import DataType

from typing import Any, List, Dict, Optional

from axonpulse.core.types import DataType, TypeCaster

from axonpulse.nodes.decorators import axon_node

try:
    import winreg
except ImportError:
    winreg = None

@NodeRegistry.register('Registry Modify', 'System/Windows')
class RegistryModifyNode(SuperNode):
    """
    Interfaces with the Windows Registry to write or delete keys.
    Requires administrative permissions for some HKEY_LOCAL_MACHINE operations.
    
    Inputs:
    - Flow: Trigger the registry operation.
    - Key Path: The full registry path (e.g., HKEY_CURRENT_USER\\Software\\AxonPulse).
    - Value Name: The name of the registry value to target.
    - Value Data: The data to write (used for Write Key action).
    - Action: 'Write' or 'Delete' (Default: Write).
    
    Outputs:
    - Flow: Pulse triggered after the operation completes.
    """
    version = '2.1.0'

    def __init__(self, node_id, name, bridge):
        super().__init__(node_id, name, bridge)
        self.is_native = True
        self.properties['Action'] = 'Write'
        self.properties['Key Path'] = ''
        self.properties['Value Name'] = ''
        self.properties['Value Data'] = ''
        self.define_schema()
        self.register_handlers()

    def define_schema(self):
        self.input_schema = {'Flow': DataType.FLOW, 'Key Path': DataType.STRING, 'Value Name': DataType.STRING, 'Value Data': DataType.STRING}
        self.output_schema = {'Flow': DataType.FLOW}

    def register_handlers(self):
        self.register_handler('Flow', self.edit_registry)

    def _parse_root(self, path):
        if not winreg:
            return (None, None)
        parts = path.split('\\')
        root_str = parts[0].upper()
        sub_key = '\\'.join(parts[1:])
        roots = {'HKEY_CLASSES_ROOT': winreg.HKEY_CLASSES_ROOT, 'HKEY_CURRENT_USER': winreg.HKEY_CURRENT_USER, 'HKEY_LOCAL_MACHINE': winreg.HKEY_LOCAL_MACHINE, 'HKEY_USERS': winreg.HKEY_USERS, 'HKEY_CURRENT_CONFIG': winreg.HKEY_CURRENT_CONFIG}
        return (roots.get(root_str), sub_key)

    def edit_registry(self, Key_Path=None, Value_Name=None, Value_Data=None, Action=None, **kwargs):
        key_path = Key_Path if Key_Path is not None else self.properties.get('Key Path', '')
        value_name = Value_Name if Value_Name is not None else self.properties.get('Value Name', '')
        value_data = Value_Data if Value_Data is not None else self.properties.get('Value Data', '')
        action = Action if Action is not None else self.properties.get('Action', 'Write')
        if not winreg:
            self.logger.error('winreg not available (Windows only).')
            return True
        (hkey_root, sub_key) = self._parse_root(key_path or '')
        if not hkey_root:
            self.logger.error(f"Invalid Root Key in '{key_path}'")
            return True
        try:
            if 'write' in action.lower():
                with winreg.CreateKey(hkey_root, sub_key) as key:
                    winreg.SetValueEx(key, value_name or '', 0, winreg.REG_SZ, str(value_data or ''))
            elif 'delete' in action.lower():
                with winreg.OpenKey(hkey_root, sub_key, 0, winreg.KEY_SET_VALUE) as key:
                    winreg.DeleteValue(key, value_name or '')
        except Exception as e:
            self.logger.error(f'Registry Error: {e}')
        self.bridge.set(f'{self.node_id}_ActivePorts', ['Flow'], self.name)
        return True

@NodeRegistry.register('Registry Read', 'System/Windows')
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
    version = '2.1.0'

    def __init__(self, node_id, name, bridge):
        super().__init__(node_id, name, bridge)
        self.is_native = True
        self.properties['Key Path'] = ''
        self.properties['Value Name'] = ''
        self.define_schema()
        self.register_handlers()

    def define_schema(self):
        self.input_schema = {'Flow': DataType.FLOW, 'Key Path': DataType.STRING, 'Value Name': DataType.STRING}
        self.output_schema = {'Flow': DataType.FLOW, 'Value': DataType.STRING}

    def register_handlers(self):
        self.register_handler('Flow', self.read_registry)

    def _parse_root(self, path):
        if not winreg:
            return (None, None)
        parts = path.split('\\')
        root_str = parts[0].upper()
        sub_key = '\\'.join(parts[1:])
        roots = {'HKEY_CLASSES_ROOT': winreg.HKEY_CLASSES_ROOT, 'HKEY_CURRENT_USER': winreg.HKEY_CURRENT_USER, 'HKEY_LOCAL_MACHINE': winreg.HKEY_LOCAL_MACHINE, 'HKEY_USERS': winreg.HKEY_USERS, 'HKEY_CURRENT_CONFIG': winreg.HKEY_CURRENT_CONFIG}
        return (roots.get(root_str), sub_key)

    def read_registry(self, Key_Path=None, Value_Name=None, **kwargs):
        key_path = Key_Path if Key_Path is not None else self.properties.get('Key Path', '')
        value_name = Value_Name if Value_Name is not None else self.properties.get('Value Name', '')
        if not winreg:
            self.logger.error('winreg not available (Windows only).')
            return True
        (hkey_root, sub_key) = self._parse_root(key_path or '')
        if not hkey_root:
            self.logger.error(f"Invalid Root Key in '{key_path}'")
            return True
        try:
            with winreg.OpenKey(hkey_root, sub_key, 0, winreg.KEY_READ) as key:
                (value, type_) = winreg.QueryValueEx(key, value_name or '')
                self.bridge.set(f'{self.node_id}_Value', str(value), self.name)
        except Exception as e:
            self.logger.error(f'Registry Error: {e}')
            self.bridge.set(f'{self.node_id}_Value', '', self.name)
        self.bridge.set(f'{self.node_id}_ActivePorts', ['Flow'], self.name)
        return True

@axon_node(category="System", version="2.3.0", node_label="Environment Var", outputs=['Value'])
def EnvironmentVarNode(Variable_Name: str = '', Variable_Value: str = '', _bridge: Any = None, _node: Any = None, _node_id: str = None, **kwargs) -> Any:
    """Manages operating system environment variables (e.g., PATH, HOME).

This node can retrieve (Get), set (Set), or delete (Unset) environment 
variables. Setting a variable makes it available to the current process 
and any child processes spawned by AxonPulse.

Inputs:
- Flow: Trigger the operation.
- Variable Name: The key of the environment variable.
- Variable Value: The new value to set, or empty to retrieve.

Outputs:
- Flow: Pulse triggered after the operation.
- Value: The current state of the variable after the operation."""
    var_name = Variable_Name if Variable_Name is not None else _node.properties.get('Variable Name', '')
    val_input = Variable_Value if Variable_Value is not None else _node.properties.get('Variable Value', _node.properties.get('Value', ''))
    if not var_name:
        _node.logger.error('No variable name provided.')
        return False
    else:
        pass
    value_out = ''
    if val_input is not None and val_input != '':
        op = 'Set'
    elif val_input == '':
        op = 'Unset'
    else:
        op = 'Get'
    if op == 'Set':
        os.environ[var_name] = str(val_input)
        value_out = str(val_input)
    elif op == 'Unset':
        os.environ.pop(var_name, None)
        value_out = ''
    else:
        value_out = os.environ.get(var_name, '')
    return value_out


@axon_node(category="IO/Files", version="2.3.0", node_label="Archive Write", outputs=['Success', 'Result Path'])
def ArchiveWriteNode(Source_Path: str, Archive_Path: str, _bridge: Any = None, _node: Any = None, _node_id: str = None, **kwargs) -> Any:
    """Compresses files or directories into a ZIP archive.

Inputs:
- Flow: Trigger the compression process.
- Source Path: The absolute path of the file or folder to be compressed.
- Archive Path: The absolute path where the resulting ZIP file will be saved.

Outputs:
- Flow: Triggered after compression (success or failure).
- Success: Triggered ONLY if the compression was successful.
- Result Path: The absolute path to the generated ZIP file."""
    src = Source_Path if Source_Path is not None else _node.properties.get('Source Path', '')
    dst = Archive_Path if Archive_Path is not None else _node.properties.get('Archive Path', '')
    if not src:
        _node.logger.error('Missing Source Path')
        _bridge.set(f'{_node_id}_ActivePorts', ['Flow'], _node.name)
    else:
        pass
    try:
        base_name = os.path.splitext(dst)[0] if dst else src
        fmt = 'zip'
        shutil.make_archive(base_name, fmt, src)
        out_path = f'{base_name}.{fmt}'
        _node.logger.info(f'Compressed {src} into {out_path}')
        _bridge.set(f'{_node_id}_ActivePorts', ['Success', 'Flow'], _node.name)
    except Exception as e:
        _node.logger.error(f'Compression Error: {e}')
        _bridge.set(f'{_node_id}_ActivePorts', ['Flow'], _node.name)
    finally:
        pass
    return {'Result Path': out_path}


@axon_node(category="IO/Files", version="2.3.0", node_label="Archive Read", outputs=['Success', 'Extracted Path'])
def ArchiveReadNode(Archive_Path: str, Destination_Folder: str, _bridge: Any = None, _node: Any = None, _node_id: str = None, **kwargs) -> Any:
    """Extracts ZIP archives into a targeted destination folder.

Inputs:
- Flow: Trigger the extraction process.
- Archive Path: The absolute path to the .zip archive to extract.
- Destination Folder: The folder path where the contents will be extracted.

Outputs:
- Flow: Triggered after extraction (success or failure).
- Success: Triggered ONLY if the extraction was successful.
- Extracted Path: The absolute path to the folder containing extracted files."""
    src = Archive_Path if Archive_Path is not None else _node.properties.get('Archive Path', '')
    dst = Destination_Folder if Destination_Folder is not None else _node.properties.get('Destination Folder', '')
    if not src:
        _node.logger.error('Missing Archive Path')
        _bridge.set(f'{_node_id}_ActivePorts', ['Flow'], _node.name)
    else:
        pass
    try:
        out_dir = dst if dst else os.path.splitext(src)[0]
        shutil.unpack_archive(src, out_dir)
        _node.logger.info(f'Extracted {src} into {out_dir}')
        _bridge.set(f'{_node_id}_ActivePorts', ['Success', 'Flow'], _node.name)
    except Exception as e:
        _node.logger.error(f'Extraction Error: {e}')
        _bridge.set(f'{_node_id}_ActivePorts', ['Flow'], _node.name)
    finally:
        pass
    return {'Extracted Path': out_dir}
