
import re
from axonpulse.utils.logger import main_logger as logger

# Ports that should be migrated to the standard "Flow" name
FLOW_ALIASES = {"Out", "Exec", "Then", "Else", "Loop", "Finished Flow", "Done", "Success", "Failure", "Try"}

def migrate(data):
    """
    Standardizes legacy flow names to "Flow" for v2.3.1.
    Allows the execution engine to remove expensive fallback loops.
    """
    was_modified = False
    
    # 1. Bump Version
    current_version = data.get("version", "2.3.0")
    if current_version < "2.3.1":
        data["version"] = "2.3.1"
        was_modified = True

    # 2. Map Wires
    for wire in data.get("wires", []):
        # Map Output Ports (from_port)
        old_from = wire.get("from_port")
        if old_from in FLOW_ALIASES:
            wire["from_port"] = "Flow"
            was_modified = True
            
        # Map Input Ports (to_port) if they use legacy names (usually "In" or "Trigger")
        # For now, we only map the explicitly listed flow aliases.
        old_to = wire.get("to_port")
        if old_to in FLOW_ALIASES:
            wire["to_port"] = "In" # Standard input for flow
            was_modified = True

    # 3. Map Node Definitions (Optional metadata)
    for node in data.get("nodes", []):
        props = node.get("properties", {})
        
        # Standardize 'outputs' list in properties (used by decorated nodes)
        if "outputs" in props and isinstance(props["outputs"], list):
            new_outputs = []
            node_mod = False
            for p in props["outputs"]:
                if p in FLOW_ALIASES:
                    new_outputs.append("Flow")
                    node_mod = True
                else:
                    new_outputs.append(p)
            if node_mod:
                props["outputs"] = new_outputs
                was_modified = True
                
        # Standardize any legacy input/output type maps if they exist
        for m_name in ["input_types", "output_types", "CustomInputSchema", "CustomOutputSchema"]:
            if m_name in props and isinstance(props[m_name], dict):
                new_map = {}
                map_mod = False
                for k, v in props[m_name].items():
                    if k in FLOW_ALIASES:
                        new_map["Flow"] = v
                        map_mod = True
                    else:
                        new_map[k] = v
                if map_mod:
                    props[m_name] = new_map
                    was_modified = True

    if was_modified:
        logger.info("Graph standardized to v2.3.1 (Flow aliasing removed)")

    return data, was_modified
