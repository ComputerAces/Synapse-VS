import os
import importlib.util
import json

# Clean Recursive Loader
_DISCOVERY_COMPLETED = False

def discover_nodes():
    """Discover core nodes (side-effect limited)."""
    global _DISCOVERY_COMPLETED
    if _DISCOVERY_COMPLETED:
        return
        
    root_dir = os.path.dirname(__file__)
    
    for root, dirs, files in os.walk(root_dir):
        # Skip __pycache__ and hidden dirs
        dirs[:] = [d for d in dirs if not d.startswith("__") and not d.startswith(".")]
        
        for filename in files:
            if filename.endswith(".py") and filename != "__init__.py":
                # Construct module path: synapse.nodes.sub.foo
                rel_path = os.path.relpath(os.path.join(root, filename), root_dir)
                mod_name_relative = rel_path[:-3].replace(os.path.sep, ".")
                full_module_name = f"synapse.nodes.{mod_name_relative}"
                
                try:
                    __import__(full_module_name, locals(), globals())
                except Exception as e:
                    print(f"[ERROR] Failed to load node module {full_module_name}: {e}")
                    import traceback
                    traceback.print_exc()
    
    _DISCOVERY_COMPLETED = True

def discover_plugins():
    """Discovers .syp and .spy files from 'plugins/' directory."""
    try:
        from synapse.nodes.registry import NodeRegistry
        # Check a specific static flag in registry to avoid multi-process/multi-import spam
        if getattr(NodeRegistry, "_PLUGINS_LOADED", False):
            return
        
        NodeRegistry._PLUGINS_LOADED = True
        
        project_root = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
        plugins_dir = os.path.join(project_root, "plugins")
        
        if os.path.exists(plugins_dir):
            seen_labels = set()
            for root, dirs, files in os.walk(plugins_dir):
                # Skip hidden/system dirs
                dirs[:] = [d for d in dirs if not d.startswith(".") and not d.startswith("__")]
                
                for file in files:
                    if file.endswith(".syp"):
                        path = os.path.join(root, file)
                        
                        # [NEW] Default to "Plugins" category
                        category = "Plugins"
                        
                        # Default label from filename
                        label = file.replace(".syp", "").replace("_", " ").title()
                        
                        try:
                            # Attempt to read metadata for better categorization and LABELING
                            with open(path, 'r') as f:
                                data = json.load(f)
                                
                            # [MIGRATION] Automatically patch plugins to latest version
                            from synapse.core.schema import migrate_graph
                            data, was_modified = migrate_graph(data)
                            if was_modified:
                                from synapse.utils.file_utils import safe_save_graph
                                if safe_save_graph(path, data):
                                    print(f"[Plugins] Auto-Migrated plugin: {file} to latest schema.")

                            # [SCHEMA] Check project_category, project_type, and project_name
                            pcat = data.get("project_category", "").strip()
                            ptype = data.get("project_type", "").strip()
                            if pcat: category = pcat
                            elif ptype: category = ptype # Fallback
                            
                            pname = data.get("project_name", "").strip()
                            if pname: label = pname
                        except Exception as p_err:
                            print(f"[Plugins] Metadata error in {file}: {p_err}")
                        
                        # Check if already in registry (_nodes) or seen in this loop
                        if label not in NodeRegistry._nodes and label not in seen_labels:
                            NodeRegistry.register_subgraph(label, path, category=category)
                            print(f"[Plugins] Loaded Subgraph: {label} (Category: {category})")
                            seen_labels.add(label)
                    elif file.endswith(".spy"):
                        spy_path = os.path.join(root, file)
                        module_name = f"synapse_plugin_{file[:-4]}"
                        spec = importlib.util.spec_from_file_location(module_name, spy_path)
                        if spec and spec.loader:
                            module = importlib.util.module_from_spec(spec)
                            spec.loader.exec_module(module)
                            print(f"[Plugins] Loaded Python Plugin: {file}")
    except Exception as e:
        print(f"[Plugins] Loader Error: {e}")

# Initial Discovery of core types
discover_nodes()
