import logging
from synapse.nodes.registry import NodeRegistry

logger = logging.getLogger(__name__)

GRAPH_SCHEMA_VERSION = "2.3.0"

def validate_graph(data):
    """
    Validates the structure of a graph dictionary.
    Returns (bool, str) -> (is_valid, error_message)
    """
    if not isinstance(data, dict):
        return False, "Root must be a dictionary."
        
    required_keys = ["nodes", "wires"]
    for key in required_keys:
        if key not in data:
            return False, f"Missing required key: '{key}'"
            
    if not isinstance(data["nodes"], list):
        return False, "'nodes' must be a list."
        
    if not isinstance(data["wires"], list):
        return False, "'wires' must be a list."

    # Validate Nodes
    for i, node in enumerate(data["nodes"]):
        if not isinstance(node, dict):
            return False, f"Node at index {i} is not a dictionary."
        if "id" not in node:
            return False, f"Node at index {i} missing 'id'."
        if "type" not in node:
            return False, f"Node at index {i} missing 'type'."

    # Validate Wires
    for i, wire in enumerate(data["wires"]):
        if not isinstance(wire, dict):
            return False, f"Wire at index {i} is not a dictionary."
        if "from_node" not in wire:
            return False, f"Wire at index {i} missing 'from_node'."
        if "to_node" not in wire:
            return False, f"Wire at index {i} missing 'to_node'."
            
    return True, ""

def migrate_graph(data):
    """
    Migrates a graph to the current schema version using the migration system.
    Returns (data, was_modified)
    """
    from synapse.core.migrations.manager import run_migrations
    
    # 1. Run Modular Migrations
    data, was_modified = run_migrations(data)
    
    # 2. Final Version Check (Fallback)
    current_version = data.get("version", 0)
    try:
        # Convert string version like "2.1.0" to comparable numeric if possible, 
        # or just check against string if using standard formatting.
        if str(current_version) < str(GRAPH_SCHEMA_VERSION):
            logger.info(f"Bumping version from {current_version} to {GRAPH_SCHEMA_VERSION}")
            data["version"] = GRAPH_SCHEMA_VERSION
            was_modified = True
    except:
        pass

    return data, was_modified
