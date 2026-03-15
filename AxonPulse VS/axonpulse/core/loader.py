import os
import yaml
import re
from axonpulse.nodes.registry import NodeRegistry
from axonpulse.utils.logger import main_logger as logger
from axonpulse.utils.file_utils import smart_load

# Properties that are always allowed (system metadata)
# [FIX] Standardize to lowercase for robust case-insensitive matching
SYSTEM_PROPERTIES = {
    "label", "provider flow id", "singleton scope", 
    "graph path", "embedded data", "is debug", "header color",
    "additional inputs", "additional outputs", "cases"
}

# [OPTIMIZATION] Pre-compiled dynamic patterns for property matching
_DYNAMIC_PATTERNS_RAW = [
    r"item \d+", r"case \d+", r"image [a-z]", r"last image", r"user present", 
    r"var \d+", r"port \d+", r"input \d+", r"output \d+", r"camera index",
    r"path", r"success", r"result", r"data", r"image", # [FIX] Add common generic ports
    r"var.*", r"arg.*", r"param.*", r"last .* image", r"curr.* image", r"prev.* image"
]
DYNAMIC_PATTERNS_COMPILED = [re.compile(p) for p in _DYNAMIC_PATTERNS_RAW]

def load_graph_from_file(path, bridge, engine):
    data = smart_load(path)
    if not data:
        raise ValueError(f"Failed to load graph from {path}")
        
    # [NEW] Inject Project Variables into Bridge
    project_vars = data.get("project_vars", {})
    if project_vars:
        for k, v in project_vars.items():
            bridge.set(f"ProjectVars.{k}", v, "ProjectLoader")
            logger.info(f"Injected Project Variable: {k}")
            
    # [NEW] Inject Project Metadata into Bridge
    bridge.set("ProjectMeta.project_name", data.get("project_name", ""), "ProjectLoader")
    bridge.set("ProjectMeta.project_version", data.get("project_version", "1.0.0"), "ProjectLoader")
    bridge.set("ProjectMeta.project_category", data.get("project_category", ""), "ProjectLoader")
    bridge.set("ProjectMeta.project_description", data.get("project_description", ""), "ProjectLoader")
 
    # [SCHEMA VALIDATION & MIGRATION]
    from axonpulse.core.schema import validate_graph, migrate_graph
    
    is_valid, error = validate_graph(data)
    if not is_valid:
        raise ValueError(f"Invalid Graph Format: {error}")
        
    data, was_migrated = migrate_graph(data)
    if was_migrated:
        logger.info(f"Graph migrated to schema v{data.get('version')}")
 
    node_map, was_pruned = load_graph_data(data, bridge, engine, source_file=path)
    
    # [NEW] After loading the main graph, refresh favorites.
    # Pass embedded_subgraphs so favorites used in the graph can be fully registered without I/O.
    load_favorites_into_registry(mapped_subgraphs=data.get("embedded_subgraphs"))
    
    was_modified = was_migrated or was_pruned
    
    # [NEW] Auto-bump project version for modified graphs
    if was_modified:
        old_ver = data.get("project_version", "1.0.0")
        try:
            parts = old_ver.split(".")
            if len(parts) >= 2:
                major = parts[0]
                minor = int(parts[1])
                new_ver = f"{major}.{minor + 1}.0"
                data["project_version"] = new_ver
                logger.info(f"Auto-bumped project version: {old_ver} -> {new_ver}")
        except Exception as e:
            logger.debug(f"Failed to auto-bump project version: {e}")

    return node_map, was_modified, data


def load_graph_data(data, bridge, engine, source_file=None, existing_nodes=None):
    """
    Core logic to instantiate nodes and connect wires from graph data.
    Shared between main loader and SubGraph execution.
    :param existing_nodes: Dictionary of {id: node_instance} to reuse (Surgical Patching)
    Returns: (node_map, was_pruned)
    """
    node_map = {} # id -> Node Instance
    was_pruned = False
    existing_nodes = existing_nodes or {}

    # 1. Soft Migration (Ensure internal data is up-to-date even if file isn't)
    from axonpulse.core.schema import migrate_graph
    data, _ = migrate_graph(data)

    # 1. Create Nodes
    # 1. Create Nodes
    for n_data in data["nodes"]:
        node_id = n_data["id"]
        node_type = n_data["type"]
        node_name = n_data.get("name", node_type)
        
        
        # [SURGICAL PATCHING] Reuse existing node if it matches type
        if node_id in existing_nodes:
            old_node = existing_nodes[node_id]
            current_type = getattr(old_node, "node_type", "Unknown")
            if current_type == node_type:
                old_node.properties.update(n_data.get("properties", {}))
                node_map[node_id] = old_node
                continue
            else:
                 logger.info(f"[LiveSwap] Node {node_id} type mismatch ({current_type} != {node_type}). Re-instantiating.")
        
        node_class = NodeRegistry.get_node_class(node_type)
        
        if node_class:
            node = node_class(node_id, node_name, bridge)
            
            # [VERSIONING] Compare loaded version with current class version
            loaded_ver = n_data.get("node_version", 1)
            current_ver = getattr(node_class, "node_version", 1)
            
            node.loaded_version = loaded_ver
            node.latest_version = current_ver
            
            if current_ver > loaded_ver:
                node.is_legacy = True
                node.properties["is_legacy"] = True
                node.properties["version_mismatch"] = True
                node.properties["latest_version"] = current_ver
                logger.info(f"[{node_name}] Loaded legacy version v{loaded_ver} (Latest: v{current_ver})")
            else:
                # Store the version in properties so it's saved in the next graph save
                node.properties["node_version"] = current_ver

        elif "properties" in n_data and "Graph Path" in n_data["properties"]:
            # Fallback: It's a SubGraph, but maybe not registered by name yet.
            sg_cls = NodeRegistry.get_node_class("SubGraph Node")
            if sg_cls:
                node = sg_cls(node_id, node_name, bridge)
            else:
                 logger.error(f"Critical: SubGraph Node class not found.")
                 continue
        else:
            logger.warning(f"Unknown node type: {node_type}")
            continue

        # Load properties for ALL nodes (Strict Cleanup)
        loaded_props = n_data.get("properties", {})
        
        # Determine allowed dynamic property keys (case-insensitive)
        allowed_dynamic = set()
        for k, v in loaded_props.items():
            kl = k.lower().replace("_", " ")
            if kl in ["additional inputs", "additionalinputs"]: 
                 if isinstance(v, list):
                    allowed_dynamic.update(n.lower() for n in v if isinstance(n, str))
            elif kl in ["additional outputs", "additionaloutputs"]:
                 if isinstance(v, list):
                    allowed_dynamic.update(n.lower() for n in v if isinstance(n, str))
            elif kl == "cases":
                 if isinstance(v, list):
                    allowed_dynamic.update(n.lower() for n in v if isinstance(n, str))
            
        # We use a list of keys to safely iterate while deleting from the dict

        for k in list(loaded_props.keys()):
            v = loaded_props[k]
            k_lower = k.lower()
            k_normalized = k_lower.replace("_", " ")
            
            # 1. Direct match with initialized properties
            if k in node.properties:
                node.properties[k] = v
                continue
            
            # 2. System properties / Metadata
            if k_lower in SYSTEM_PROPERTIES or k_normalized in SYSTEM_PROPERTIES:
                node.properties[k] = v
                continue
            
            # 3. Dynamic Port properties (Start/Return/Calculated)
            if k_lower in allowed_dynamic or k_normalized in allowed_dynamic:
                node.properties[k] = v
                continue
            
            # 4. Case-Insensitive port match (against input_types/output_types)
            matched = False
            for port_map_name in ["input_types", "output_types"]:
                port_map = getattr(node, port_map_name, {})
                for port_name in port_map:
                    if k_lower == port_name.lower() or k_normalized == port_name.lower().replace("_", " "):
                        node.properties[k] = v
                        matched = True
                        break
                if matched: break
            
            # 5. [PROTECTION] Dynamic Port Pattern Match (for nodes that allow dynamic expansion)
            if not matched and (getattr(node, "allow_dynamic_inputs", False) or getattr(node, "allow_dynamic_outputs", False)):
                is_subgraph = getattr(node, "allow_dynamic_inputs", False) and getattr(node, "allow_dynamic_outputs", False)
                if is_subgraph:
                    node.properties[k] = v
                    matched = True
                else:
                    for pattern in DYNAMIC_PATTERNS_COMPILED:
                        if pattern.fullmatch(k_normalized):
                            node.properties[k] = v
                            matched = True
                            break

            if not matched:
                source_name = os.path.basename(source_file) if source_file else "Unknown"
                logger.warning(f"[{source_name}] [{node_name}] Removed dead property '{k}'")
                loaded_props.pop(k) # Remove from JSON data
                was_pruned = True
        
        # [NEW] Re-sync schema AFTER all properties (including Embedded Data) are loaded
        if hasattr(node, '_parse_legacy_ports'):
            node._parse_legacy_ports()
            
        # Embedded SubGraph Handling
        embedded_subgraphs = data.get("embedded_subgraphs", {})
        
        # Check standardized keys for Graph Path and Embedded Data
        graph_path = node.properties.get("Graph Path")
        embedded_data = node.properties.get("Embedded Data")

        if graph_path and not embedded_data:
            if graph_path in embedded_subgraphs:
                node.properties["Embedded Data"] = embedded_subgraphs[graph_path]
                logger.info(f"[{node_name}] Injected embedded data from '{graph_path}'")

        # [NEW] Re-sync schema AFTER embedded data is injected
        if hasattr(node, "sync_schema"):
            node.sync_schema()

        # Name Repair
        if (node.name.startswith("SubGraph") or node.name == node_type):
            path = graph_path
            if path:
                try:
                    name = None
                    if embedded_data:
                        name = embedded_data.get("project_name", "").strip()
                        
                    if not name and os.path.exists(path):
                         p_data = smart_load(path)
                         if p_data:
                            name = p_data.get("project_name", "").strip()
                    
                    if not name:
                        name = os.path.splitext(os.path.basename(path))[0]
                        
                    node.name = name
                except: pass

        # [FIX] Rebuild Schema for Dynamic Graph Hooks
        if node_type in ["Start Node", "Return Node"] and hasattr(node, "define_schema"):
            node.define_schema()

        # Visualization Logic: Header Colors
        is_debug = node.properties.get("is_debug") or getattr(node, "is_debug", False)
        is_native = getattr(node, "is_native", False)
        
        if is_debug:
            node.properties["header_color"] = "#FF8C00" # Dark Orange
        elif is_native:
            node.properties["header_color"] = "#800080" # Dark Purple
        else:
            node.properties["header_color"] = "#008B8B" # Dark Cyan
            
        engine.register_node(node)
        node_map[node_id] = node

    # 2. Connect Wires
    for w_data in data["wires"]:
        from_id = w_data["from_node"]
        to_id = w_data["to_node"]
        from_port = w_data.get("from_port", "Flow")
        to_port = w_data.get("to_port", "In")
        
        if from_id in node_map and to_id in node_map:
            engine.connect(from_id, from_port, to_id, to_port)
        else:
            logger.error(f"Cannot connect {from_id} -> {to_id}: Node not found")
            
    return node_map, was_pruned


# Track registered favorite labels to allow cleanup
_registered_favorite_labels = set()

def load_favorites_into_registry(mapped_subgraphs=None):
    """Registers Favorite SubGraphs into NodeRegistry so they can be instantiated.
    Optimized for startup speed: utilizes mapped_subgraphs if provided, otherwise performs lazy registration.
    """
    global _registered_favorite_labels
    try:
        favorites_path = os.path.join(os.getcwd(), "favorites.json")
        current_favorite_labels = set()
        
        if os.path.exists(favorites_path):
             with open(favorites_path, 'r') as f:
                 import json
                 favorites = json.load(f)
             
             for path in favorites:
                 if not os.path.exists(path):
                     continue
                 
                 # Optimization 1: Skip if already registered
                 if NodeRegistry.is_path_registered(path):
                     # Find the label it was registered with to keep it in current_favorite_labels
                     for label, node_cls in NodeRegistry._nodes.items():
                         if hasattr(node_cls, 'graph_path') and os.path.abspath(node_cls.graph_path) == os.path.abspath(path):
                             current_favorite_labels.add(label)
                     continue

                 try:
                     name = None
                     pcat = "Favorites"
                     pdesc = "Favorite Subgraph"
                     
                     # Optimization 2: Use "Mapped" metadata from the current graph if available
                     if mapped_subgraphs and path in mapped_subgraphs:
                         data = mapped_subgraphs[path]
                         name = data.get("project_name", "").strip()
                         pcat = data.get("project_category", "").strip() or data.get("project_type", "Favorites")
                         pdesc = data.get("project_description", "").strip()
                         logger.debug(f"Registered favorite from mapped subgraphs: {os.path.basename(path)}")
                     
                     if not name:
                         # Lazy Registration: Use filename, skip parsing/migration for speed
                         name = os.path.splitext(os.path.basename(path))[0]
                         logger.debug(f"Lazy-Registered favorite: {name}")
                              
                     NodeRegistry.register_subgraph(name, path, pcat, description=pdesc)
                     current_favorite_labels.add(name)
                     
                     # Double Registration (Project Name AND File Name)
                     filename_label = os.path.splitext(os.path.basename(path))[0]
                     if filename_label != name:
                         NodeRegistry.register_subgraph(filename_label, path, pcat, is_alias=True, description=pdesc)
                         current_favorite_labels.add(filename_label)
                 except Exception as e:
                     logger.debug(f"Failed to lazy-load favorite {path}: {e}")
        
        # Cleanup: Unregister nodes that are no longer favorites
        removed_labels = _registered_favorite_labels - current_favorite_labels
        for label in removed_labels:
            logger.info(f"Unregistering removed favorite: {label}")
            NodeRegistry.unregister(label)
        
        _registered_favorite_labels = current_favorite_labels
        
    except Exception as e:
        logger.warning(f"Failed to load favorites: {e}")
