import os
import json
import shutil
import yaml
from synapse.core.types import SynapseJSONEncoder

# Custom YAML Dumper to force | block scalars for multi-line strings
class SynapseYAMLDumper(yaml.SafeDumper):
    pass

def str_presenter(dumper, data):
    if '\n' in data:
        return dumper.represent_scalar('tag:yaml.org,2002:str', data, style='|')
    return dumper.represent_scalar('tag:yaml.org,2002:str', data)

SynapseYAMLDumper.add_representer(str, str_presenter)


def smart_load(path):
    """
    Detects if a file is JSON or YAML based on its first non-whitespace character.
    Returns the parsed data.
    """
    if not os.path.exists(path):
        return None
        
    with open(path, 'r', encoding='utf-8') as f:
        content = f.read()
        return parse_yaml_or_json(content)

def parse_yaml_or_json(text):
    """Parses text as either JSON or YAML based on the first character."""
    if not text: return None
    content_start = text.strip()
    if content_start.startswith('{'):
        return json.loads(text)
    else:
        return yaml.safe_load(text)

def serialize_to_yaml(data):
    """Returns a YAML string with block scalars and sorted keys."""
    return yaml.dump(data, Dumper=SynapseYAMLDumper, sort_keys=True, default_flow_style=False, allow_unicode=True)

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
            yaml.dump(data, f, Dumper=SynapseYAMLDumper, sort_keys=True, default_flow_style=False, allow_unicode=True)

        # 3. Atomic Replace
        os.replace(temp_path, path)
        return True
    except Exception as e:
        print(f"[SafeSave] Failed to save {path}: {e}")
        if os.path.exists(temp_path):
            try: os.remove(temp_path)
            except: pass
        return False

