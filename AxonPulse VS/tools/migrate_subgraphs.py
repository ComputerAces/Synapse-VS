import os
import sys
import json
import yaml
import shutil

# Ensure we can import axonpulse
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from axonpulse.core.schema import migrate_graph
from axonpulse.utils.file_utils import AxonPulseYAMLDumper, safe_save_graph, smart_load

def migrate_all():
    print("Starting Mass SubGraph Migration (JSON -> YAML)")
    print("=" * 50)
    
    # 1. Identify Directories
    search_dirs = [
        os.path.join(os.getcwd(), "sub_graphs"),
        os.path.join(os.getcwd(), "plugins")
    ]
    
    count_converted = 0
    count_cleaned = 0
    
    for base_dir in search_dirs:
        if not os.path.exists(base_dir):
            continue
            
        print(f"Scanning: {base_dir}")
        for root, dirs, files in os.walk(base_dir):
            for file in files:
                full_path = os.path.join(root, file)
                ext = os.path.splitext(file)[1].lower()
                
                # A. Handle Migration for .json and .syp
                if ext in [".json", ".syp"]:
                    try:
                        # Try to load as JSON (to verify it needs migration)
                        with open(full_path, 'r', encoding='utf-8') as f:
                            content = f.read().strip()
                        
                        if content.startswith('{'):
                            print(f"  [MIGRATE] {file} (JSON detect)")
                            data = json.loads(content)
                            
                            # Standardize path for .json -> .syp conversion
                            target_path = full_path
                            if ext == ".json":
                                target_path = os.path.splitext(full_path)[0] + ".syp"
                            
                            # Run Migrations (Versioning, Naming, etc.)
                            data, was_modified = migrate_graph(data)
                            
                            # Save as YAML
                            if safe_save_graph(target_path, data, create_backup=False):
                                print(f"    -> Saved to YAML: {os.path.basename(target_path)}")
                                if full_path != target_path:
                                    os.remove(full_path)
                                    print(f"    -> Removed old JSON: {file}")
                                count_converted += 1
                        else:
                            # It's already YAML, but let's ensure it's up to date with schema
                            data = yaml.safe_load(content)
                            data, was_modified = migrate_graph(data)
                            if was_modified:
                                print(f"  [UPDATE] {file} (Schema bump)")
                                safe_save_graph(full_path, data, create_backup=False)
                                
                    except Exception as e:
                        print(f"  [ERROR] Failed to process {file}: {e}")

                # B. Cleanup .bak files
                elif ext == ".bak":
                    try:
                        os.remove(full_path)
                        print(f"  [CLEANUP] Removed backup: {file}")
                        count_cleaned += 1
                    except Exception as e:
                        print(f"  [ERROR] Failed to remove {file}: {e}")

    print("=" * 50)
    print(f"Migration Complete: {count_converted} files converted/updated.")
    print(f"Cleanup Complete: {count_cleaned} legacy backups removed.")

if __name__ == "__main__":
    migrate_all()
