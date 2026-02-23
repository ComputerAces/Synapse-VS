import re
from synapse.nodes.registry import NodeRegistry

def migrate(data):
    """
    Patches legacy graphs:
    1. Standardizes property names (Proper Case with Spacing).
    2. Maps legacy loop ports for While/For/ForEach nodes.
    3. Bumps version to 2.1.0.
    """
    was_modified = False
    
    # 1. Bump Version
    current_version = data.get("version", "2.0.0")
    if current_version < "2.1.0":
        data["version"] = "2.1.0"
        was_modified = True

    # 2. Iterate Nodes for Property Migration
    for node in data.get("nodes", []):
        node_type = node.get("type")
        props = node.get("properties", {})
        if not props: continue

        keys_to_fix = []
        for key in list(props.keys()):
            # Rule: If it contains underscores or lacks spaces between caps, it needs fixing
            # However, we only fix if the conversion actually changes the string
            # to prevent infinite loops or unnecessary marks
            new_key = fix_name(key)
            if new_key != key:
                if new_key not in props: # Safety
                    props[new_key] = props.pop(key)
                    was_modified = True

    # 3. Map Legacy Loop Ports in Wires
    # While: Loop -> Continue, Exit -> Break, Loop Flow -> Body
    loop_port_map = {
        "While Node": {
            "Loop": "Continue",
            "Exit": "Break",
            "Loop Flow": "Body"
        },
        "ForEach Node": {
             "Loop Flow": "Body"
        },
        "For Node": {
            "Loop Flow": "Body"
        }
    }

    # Build node ID -> Type map for wire check
    node_id_to_type = {n["id"]: n["type"] for n in data.get("nodes", [])}

    for wire in data.get("wires", []):
        from_node_type = node_id_to_type.get(wire["from_node"])
        to_node_type = node_id_to_type.get(wire["to_node"])

        # Check Output Ports
        if from_node_type in loop_port_map:
            mapping = loop_port_map[from_node_type]
            old_port = wire.get("from_port")
            if old_port in mapping:
                new_port = mapping[old_port]
                if new_port != old_port:
                    wire["from_port"] = new_port
                    was_modified = True

        # Check Input Ports
        if to_node_type in loop_port_map:
            mapping = loop_port_map[to_node_type]
            old_port = wire.get("to_port")
            if old_port in mapping:
                new_port = mapping[old_port]
                if new_port != old_port:
                    wire["to_port"] = new_port
                    was_modified = True

    return data, was_modified

def fix_name(name):
    """Converts snake_case or CamelCase to Proper Case With Space."""
    if not name or " " in name and name == name.title():
        return name
        
    # 1. Handle Snake Case
    s1 = name.replace("_", " ")
    
    # 2. Handle CamelCase (Insert space before caps)
    # Insert space between lowercase and uppercase
    s2 = re.sub(r'([a-z0-9])([A-Z])', r'\1 \2', s1)
    
    # 3. Title Case (but preserve all-caps words of length 2-4 if they were already all-caps)
    # This helps preserve things like "URL" or "ID" or "API"
    words = s2.split()
    fixed_words = []
    for word in words:
        if word.isupper() and 1 < len(word) <= 4:
            fixed_words.append(word)
        else:
            fixed_words.append(word.capitalize())
            
    return " ".join(fixed_words).strip()
