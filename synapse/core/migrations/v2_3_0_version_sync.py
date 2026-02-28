def migrate(data):
    """
    Synchronizes the graph version to v2.3.0.
    Ensures that any project with version < 2.3.0 is bumped 
    and then correctly serialized with the new version.
    """
    was_modified = False
    current_version = data.get("version", "2.0.0")
    
    if str(current_version) < "2.3.0":
        data["version"] = "2.3.0"
        was_modified = True
        
    # Scrub legacy keys
    if "nodes" in data:
        for node in data["nodes"]:
            props = node.get("properties", {})
            legacy_keys = {
                "additional_inputs": "Additional Inputs",
                "additional_outputs": "Additional Outputs",
                "embedded_data": "Embedded Data",
                "isolated_execution": "Isolated"
            }
            for old_key, new_key in legacy_keys.items():
                if old_key in props:
                    val = props.pop(old_key)
                    if new_key not in props:
                        props[new_key] = val
                    was_modified = True
                    
    return data, was_modified
