import os
import json
import shutil
import yaml
from axonpulse.core.types import AxonPulseJSONEncoder

# Custom YAML Dumper to force | block scalars for multi-line strings
class AxonPulseYAMLDumper(yaml.SafeDumper):
    pass

def str_presenter(dumper, data):
    if '\n' in data:
        return dumper.represent_scalar('tag:yaml.org,2002:str', data, style='|')
    return dumper.represent_scalar('tag:yaml.org,2002:str', data)

AxonPulseYAMLDumper.add_representer(str, str_presenter)


def smart_load(path):
    """
    Loads a YAML file from the given path.
    JSON support is deprecated and removed after v2.4.0 migration.
    """
    if not os.path.exists(path):
        return None
        
    with open(path, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)

# Legacy Alias for GUI/Clipboard operations
def parse_yaml_or_json(data):
    """Parses a YAML string (legacy alias for GUI compatibility)."""
    return yaml.safe_load(data)

def serialize_to_yaml(data):
    """Returns a YAML string with block scalars and sorted keys."""
    return yaml.dump(data, Dumper=AxonPulseYAMLDumper, sort_keys=True, default_flow_style=False, allow_unicode=True)

def safe_save_graph(path, data, create_backup=True):
    """
    Atomically saves graph data to a file using a temporary file.
    Optionally creates a .bak file before overwriting.
    Always saves in YAML format.
    """
    try:
        # 1. Create backup
        if create_backup and os.path.exists(path):
            backup_path = path + ".bak"
            try:
                shutil.copy2(path, backup_path)
            except Exception as b_err:
                print(f"[Backup] Failed to create backup for {path}: {b_err}")

        # 2. Save to Temporary File
        temp_path = path + ".tmp"
        with open(temp_path, 'w', encoding='utf-8') as f:
            yaml.dump(data, f, Dumper=AxonPulseYAMLDumper, sort_keys=True, default_flow_style=False, allow_unicode=True)

        # 3. Atomic Replace
        os.replace(temp_path, path)
        return True
    except Exception as e:
        print(f"[SafeSave] Failed to save {path}: {e}")
        if os.path.exists(temp_path):
            try: os.remove(temp_path)
            except: pass
        return False

