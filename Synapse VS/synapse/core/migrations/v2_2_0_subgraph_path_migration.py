import re

def migrate_node_properties(props):
    """
    Standardizes property names in a non-destructive way.
    """
    was_modified = False
    rename_map = {
        "graph_path": "Graph Path",
        "GraphPath": "Graph Path",
        "embedded_data": "Embedded Data",
        "EmbeddedData": "Embedded Data",
        "additional_inputs": "Additional Inputs",
        "AdditionalInputs": "Additional Inputs",
        "additional_outputs": "Additional Outputs",
        "AdditionalOutputs": "Additional Outputs"
    }

    for old_key, new_key in rename_map.items():
        if old_key in props:
            val = props.pop(old_key)
            was_modified = True
            
            # Non-Destructive Merging
            if new_key in props:
                existing = props[new_key]
                if isinstance(val, list) and isinstance(existing, list):
                    # Merge lists, keeping unique items
                    for item in val:
                        if item not in existing:
                            existing.append(item)
                elif isinstance(val, dict) and isinstance(existing, dict):
                    # Merge dicts
                    existing.update(val)
                else:
                    # For strings/values, keep the non-empty one if possible
                    if not existing and val:
                        props[new_key] = val
            else:
                props[new_key] = val

    return was_modified

def migrate(data):
    """
    Patches legacy graphs for v2.2.0:
    1. Renames property keys reliably across all nodes.
    2. Recursively migrates embedded_subgraphs.
    3. Bumps version to 2.2.0.
    """
    was_modified = False
    
    # 1. Bump Version
    current_version = data.get("version", "2.1.0")
    if current_version < "2.2.0":
        data["version"] = "2.2.0"
        was_modified = True

    # 2. Migrate Main Nodes
    for node in data.get("nodes", []):
        props = node.get("properties", {})
        if props:
            if migrate_node_properties(props):
                was_modified = True

    # 3. Recursive Migration for Embedded SubGraphs
    embedded = data.get("embedded_subgraphs", {})
    for path, subgraph_data in embedded.items():
        if isinstance(subgraph_data, dict):
            # Recurse: Each embedded graph is just another data blob
            _, sub_modified = migrate(subgraph_data) 
            if sub_modified:
                was_modified = True

    return data, was_modified

