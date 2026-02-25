import os
import json
import shutil
from synapse.core.types import SynapseJSONEncoder

def safe_save_graph(path, data, create_backup=True):
    """
    Atomically saves graph data to a file using a temporary file.
    Optionally creates a .bak file before overwriting.
    """
    try:
        # 1. Create backup
        if create_backup and os.path.exists(path):
            backup_path = path + ".bak"
            try:
                shutil.copy2(path, backup_path)
            except Exception as b_err:
                # Log but don't fail the save
                print(f"[Backup] Failed to create backup for {path}: {b_err}")

        # 2. Save to Temporary File
        temp_path = path + ".tmp"
        with open(temp_path, 'w') as f:
            json.dump(data, f, indent=4, cls=SynapseJSONEncoder)

        # 3. Atomic Replace
        os.replace(temp_path, path)
        return True
    except Exception as e:
        print(f"[SafeSave] Failed to save {path}: {e}")
        if os.path.exists(temp_path):
            try: os.remove(temp_path)
            except: pass
        return False
