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
                # Construct module path: axonpulse.nodes.sub.foo
                rel_path = os.path.relpath(os.path.join(root, filename), root_dir)
                mod_name_relative = rel_path[:-3].replace(os.path.sep, ".")
                full_module_name = f"axonpulse.nodes.{mod_name_relative}"
                
                try:
                    __import__(full_module_name, locals(), globals())
                except Exception as e:
                    print(f"[ERROR] Failed to load node module {full_module_name}: {e}")
                    import traceback
                    traceback.print_exc()
    
    _DISCOVERY_COMPLETED = True

def discover_plugins(bridge=None):
    """Discovers .syp, .spy, and .zip files from 'plugins/' directory."""
    try:
        from axonpulse.nodes.registry import NodeRegistry
        import inspect
        from axonpulse.core.super_node import SuperNode
        from axonpulse.nodes.lib.provider_node import ProviderNode

        if getattr(NodeRegistry, "_PLUGINS_LOADED", False) and bridge is None:
            return
        
        # If bridge is provided, we allow a second pass specifically for encrypted zips
        if bridge is not None:
            NodeRegistry._PLUGINS_WITH_BRIDGE_LOADED = True
        else:
            NodeRegistry._PLUGINS_LOADED = True
        
        project_root = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
        plugins_dir = os.path.join(project_root, "plugins")
        
        if not os.path.exists(plugins_dir):
            os.makedirs(plugins_dir, exist_ok=True)
            return

        seen_labels = set()
        for root, dirs, files in os.walk(plugins_dir):
            dirs[:] = [d for d in dirs if not d.startswith(".") and not d.startswith("__")]
            
            for file in files:
                path = os.path.join(root, file)
                
                # 1. Handle .syp Subgraphs
                if file.endswith(".syp"):
                    category = "Plugins"
                    label = file.replace(".syp", "").replace("_", " ").title()
                    
                    try:
                        with open(path, 'r') as f:
                            data = json.load(f)
                        
                        from axonpulse.core.schema import migrate_graph
                        data, was_modified = migrate_graph(data)
                        if was_modified:
                            from axonpulse.utils.file_utils import safe_save_graph
                            safe_save_graph(path, data)

                        pcat = data.get("project_category", "").strip()
                        ptype = data.get("project_type", "").strip()
                        if pcat: category = pcat
                        elif ptype: category = ptype
                        
                        pname = data.get("project_name", "").strip()
                        if pname: label = pname
                    except Exception as p_err:
                        print(f"[Plugins] Metadata error in {file}: {p_err}")
                    
                    if label not in NodeRegistry._nodes and label not in seen_labels:
                        NodeRegistry.register_subgraph(label, path, category=category)
                        print(f"[Plugins] Loaded Subgraph: {label} (Category: {category})")
                        seen_labels.add(label)

                # 2. Handle .spy / .py Hard Nodes
                elif file.endswith(".spy") or (file.endswith(".py") and file != "__init__.py"):
                    try:
                        module_name = f"axonpulse_plugin_{file.split('.')[0]}"
                        
                        # Force SourceFileLoader to support .spy extension
                        from importlib.machinery import SourceFileLoader
                        loader = SourceFileLoader(module_name, path)
                        spec = importlib.util.spec_from_loader(module_name, loader)
                        
                        if spec and spec.loader:
                            module = importlib.util.module_from_spec(spec)
                            spec.loader.exec_module(module)
                            
                            # Inspect for SuperNode subclasses
                            seen_any = False
                            for name, cls in inspect.getmembers(module, inspect.isclass):
                                try:
                                    if issubclass(cls, SuperNode) and cls not in (SuperNode, ProviderNode):
                                        # Strict module matching (with fallback for dynamically named modules)
                                        cls_mod = inspect.getmodule(cls)
                                        if cls_mod == module or cls.__module__ == module_name:
                                            label = getattr(cls, "node_label", name)
                                            category = getattr(cls, "node_category", "Custom Nodes")
                                            
                                            # Register with Registry
                                            NodeRegistry.register(label, category)(cls)
                                            print(f"[Plugins] Registered Hard Node: {label} (Category: {category})")
                                            seen_labels.add(label)
                                            seen_any = True
                                except Exception:
                                    pass
                    except Exception as spy_err:
                        print(f"[Plugins] Failed to load Hard Node plugin {file}: {spy_err}")

                # 3. Handle .zip Asset Packages
                elif file.endswith(".zip"):
                    try:
                        from axonpulse.utils.zip_utils import is_zip_encrypted, extract_package
                        zip_name = file.replace(".zip", "")
                        extract_path = os.path.join(plugins_dir, "extracted", zip_name)
                        
                        # Check if extraction is needed
                        needs_extraction = not os.path.exists(extract_path)
                        
                        if needs_extraction:
                            password = None
                            if is_zip_encrypted(path):
                                if bridge:
                                    print(f"[Plugins] Encrypted package detected: {file}. Requesting password...")
                                    password = bridge.request_asset_password(path)
                                    if not password:
                                        print(f"[Plugins] Password request cancelled or timed out for {file}. Skipping.")
                                        continue
                                else:
                                    print(f"[Plugins] Encrypted package {file} detected but no bridge available for password request. Skipping.")
                                    continue
                            
                            print(f"[Plugins] Extracting package: {file} -> {zip_name}...")
                            if extract_package(path, extract_path, password=password):
                                # Immediately scan the newly extracted folder for nodes/subgraphs
                                # We temporarily clear the guard or just call discovery on the new path
                                pass 
                            else:
                                print(f"[Plugins] Extraction failed for {file}.")
                                continue

                        # If we have an extracted path (either just now or previously), scan it
                        if os.path.exists(extract_path):
                            # We don't recurse discover_plugins because of the guard,
                            # but we can scan the files in the extracted dir.
                            for root_ext, _, files_ext in os.walk(extract_path):
                                for f_ext in files_ext:
                                    ext_full_path = os.path.join(root_ext, f_ext)
                                    # Reuse the logic for .syp and .spy
                                    # (Note: This is a bit repetitive, in a refactor we'd move these to helper functions)
                                    if f_ext.endswith(".syp"):
                                        label = f_ext.replace(".syp", "").replace("_", " ").title()
                                        category = "Plugins"
                                        try:
                                            with open(ext_full_path, 'r') as f:
                                                data = json.load(f)
                                            from axonpulse.core.schema import migrate_graph
                                            data, was_modified = migrate_graph(data)
                                            if was_modified:
                                                from axonpulse.utils.file_utils import safe_save_graph
                                                safe_save_graph(ext_full_path, data)
                                            pcat = data.get("project_category", data.get("project_type", "Plugins"))
                                            pname = data.get("project_name", label)
                                            NodeRegistry.register_subgraph(pname, ext_full_path, category=pcat)
                                            print(f"[Plugins] Loaded Subgraph from Package: {pname} (Category: {pcat})")
                                        except Exception as e:
                                            print(f"[Plugins] Package Metadata error in {f_ext}: {e}")

                                    elif f_ext.endswith(".spy") or (f_ext.endswith(".py") and f_ext != "__init__.py"):
                                        # Hard Node logic... (reusing the spec/loader part)
                                        try:
                                            module_name_ext = f"axonpulse_plugin_pkg_{zip_name}_{f_ext.split('.')[0]}"
                                            from importlib.machinery import SourceFileLoader
                                            loader_ext = SourceFileLoader(module_name_ext, ext_full_path)
                                            spec_ext = importlib.util.spec_from_loader(module_name_ext, loader_ext)
                                            if spec_ext and spec_ext.loader:
                                                module_ext = importlib.util.module_from_spec(spec_ext)
                                                spec_ext.loader.exec_module(module_ext)
                                                for name_ext, cls_ext in inspect.getmembers(module_ext, inspect.isclass):
                                                    if issubclass(cls_ext, SuperNode) and cls_ext not in (SuperNode, ProviderNode):
                                                        cls_mod_ext = inspect.getmodule(cls_ext)
                                                        if cls_mod_ext == module_ext or cls_ext.__module__ == module_name_ext:
                                                            label_ext = getattr(cls_ext, "node_label", name_ext)
                                                            cat_ext = getattr(cls_ext, "node_category", "Custom Nodes")
                                                            NodeRegistry.register(label_ext, cat_ext)(cls_ext)
                                                            print(f"[Plugins] Registered Package Node: {label_ext} (Category: {cat_ext})")
                                        except Exception as e:
                                            print(f"[Plugins] Package Hard Node error in {f_ext}: {e}")

                    except Exception as zip_err:
                        print(f"[Plugins] Zip package error {file}: {zip_err}")

    except Exception as e:
        print(f"[Plugins] Loader Error: {e}")

# Initial Discovery of core types and plugins
discover_nodes()
discover_plugins()
