import json
import os
from synapse.nodes.registry import NodeRegistry
from synapse.utils.logger import main_logger as logger

def load_graph_from_json(json_path, bridge, engine):
    with open(json_path, 'r') as f:
        data = json.load(f)
        
    # [NEW] Inject Project Variables into Bridge
    project_vars = data.get("project_vars", {})
    if project_vars:
        for k, v in project_vars.items():
            bridge.set(f"ProjectVars.{k}", v, "ProjectLoader")
            logger.info(f"Injected Project Variable: {k}")

    # [SCHEMA VALIDATION & MIGRATION]
    from synapse.core.schema import validate_graph, migrate_graph
    
    is_valid, error = validate_graph(data)
    if not is_valid:
        raise ValueError(f"Invalid Graph Format: {error}")
        
    data, was_modified = migrate_graph(data)
    if was_modified:
        logger.info(f"Graph migrated to schema v{data.get('version')}")

    node_map = load_graph_data(data, bridge, engine)
    return node_map, was_modified

def load_graph_data(data, bridge, engine):
    """
    Core logic to instantiate nodes and connect wires from graph data.
    Shared between main loader and SubGraph execution.
    """
    node_map = {} # id -> Node Instance

    # 1. Create Nodes
    for n_data in data["nodes"]:
        node_id = n_data["id"]
        node_type = n_data["type"]
        node_name = n_data.get("name", node_type)
        
        node_class = NodeRegistry.get_node_class(node_type)
        
        if node_class:
            node = node_class(node_id, node_name, bridge)
        elif "graph_path" in n_data.get("properties", {}):
            # Fallback: It's a SubGraph, but maybe not registered by name yet.
            sg_cls = NodeRegistry.get_node_class("SubGraph Node")
            if sg_cls:
                logger.warning(f"Node Type '{node_type}' not found. Falling back to generic SubGraphNode.")
                node = sg_cls(node_id, node_name, bridge)
            else:
                 logger.error(f"Critical: SubGraph Node class not found.")
                 continue
        else:
            logger.warning(f"Unknown node type in JSON: {node_type}")
            continue

        # Load properties for ALL nodes (Strict Cleanup)
        loaded_props = n_data.get("properties", {})
        
        # Determine allowed dynamic property keys (case-insensitive)
        allowed_dynamic = set()
        if "additional_inputs" in loaded_props:
            allowed_dynamic.update(name.lower() for name in loaded_props["additional_inputs"])
        if "additional_outputs" in loaded_props:
            allowed_dynamic.update(name.lower() for name in loaded_props["additional_outputs"])
            
        is_subgraph = "graph_path" in loaded_props or isinstance(node, NodeRegistry.get_node_class("SubGraph Node"))

        for k, v in loaded_props.items():
            if k in node.properties:
                node.properties[k] = v
            elif k.lower() in allowed_dynamic or is_subgraph:
                node.properties[k] = v
            else:
                is_input_match = False
                if hasattr(node, "input_types"):
                    for input_name in node.input_types:
                        if k.lower() == input_name.lower():
                            node.properties[k] = v
                            is_input_match = True
                            break
                            
                if not is_input_match:
                     logger.warning(f"[{node_name}] Skipped dead property '{k}'")
        
        if hasattr(node, '_parse_legacy_ports'):
            node._parse_legacy_ports()
            
        # Embedded SubGraph Handling
        embedded_subgraphs = data.get("embedded_subgraphs", {})
        graph_path = node.properties.get("graph_path")
        
        if graph_path and not node.properties.get("embedded_data"):
            if graph_path in embedded_subgraphs:
                node.properties["embedded_data"] = embedded_subgraphs[graph_path]
                logger.info(f"[{node_name}] Injected embedded data from '{graph_path}'")

        # Name Repair
        if (node.name.startswith("SubGraph") or node.name == node_type):
            path = node.properties.get("graph_path")
            if path:
                try:
                    name = None
                    emb_data = node.properties.get("embedded_data")
                    if emb_data:
                        name = emb_data.get("project_name", "").strip()
                        
                    if not name and os.path.exists(path):
                         with open(path, 'r') as f:
                             p_data = json.load(f)
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
            
    return node_map

# Track registered favorite labels to allow cleanup
_registered_favorite_labels = set()

def load_favorites_into_registry():
    """Registers Favorite SubGraphs into NodeRegistry so they can be instantiated."""
    global _registered_favorite_labels
    try:
        favorites_path = os.path.join(os.getcwd(), "favorites.json")
        current_favorite_labels = set()
        
        if os.path.exists(favorites_path):
             with open(favorites_path, 'r') as f:
                 favorites = json.load(f)
             
             for path in favorites:
                 if os.path.exists(path):
                     try:
                         with open(path, 'r') as f:
                             data = json.load(f)
                             
                         # [MIGRATION] Automatically patch favorites to latest version
                         from synapse.core.schema import migrate_graph
                         data, was_modified = migrate_graph(data)
                         if was_modified:
                             from synapse.utils.file_utils import safe_save_graph
                             if safe_save_graph(path, data):
                                 logger.info(f"Auto-Migrated favorite: {os.path.basename(path)} to latest schema.")

                         name = data.get("project_name", "").strip()
                         # [FIX] Prioritize project_category over project_type
                         pcat = data.get("project_category", "").strip() or data.get("project_type", "Uncategorized")
                         pdesc = data.get("project_description", "").strip()
                             
                         if not name:
                             name = os.path.splitext(os.path.basename(path))[0]
                                  
                         NodeRegistry.register_subgraph(name, path, pcat, description=pdesc)
                         current_favorite_labels.add(name)
                         
                         # Double Registration (Project Name AND File Name)
                         # [FIX] Register filename as alias to prevent duplication in Node Library
                         filename_label = os.path.splitext(os.path.basename(path))[0]
                         if filename_label != name:
                             NodeRegistry.register_subgraph(filename_label, path, pcat, is_alias=True, description=pdesc)
                             current_favorite_labels.add(filename_label)
                     except Exception:
                         pass
        
        # Cleanup: Unregister nodes that are no longer favorites
        removed_labels = _registered_favorite_labels - current_favorite_labels
        for label in removed_labels:
            logger.info(f"Unregistering removed favorite: {label}")
            NodeRegistry.unregister(label)
        
        _registered_favorite_labels = current_favorite_labels
        
    except Exception as e:
        logger.warning(f"Failed to load favorites: {e}")
