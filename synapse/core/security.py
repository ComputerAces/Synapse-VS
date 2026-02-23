from synapse.nodes.registry import NodeRegistry

# Nodes classified as High Risk
RISKY_NODES = [
    "Shell Command", 
    "Python Script", 
    "Delete File", 
    "Write File", 
    "Move File", 
    "HTTP Request", 
    "TCP Client", 
    "TCP Server",
    "Socket.IO Client",
    "Flask Server",
    "File Watcher"
]

def scan_for_risks(graph_data):
    """
    Scans a graph dictionary for potential security risks.
    Returns:
        is_risky (bool): True if any high-risk nodes are found.
        risks (list): List of unique risky node types found.
    """
    if not graph_data or "nodes" not in graph_data:
        return False, []
        
    found_risks = set()
    
    for node in graph_data["nodes"]:
        n_type = node.get("type", "")
        # Check explicit list or suspicious generic names
        if n_type in RISKY_NODES:
            found_risks.add(n_type)
        # Check system/execution related keywords
        elif "process" in n_type.lower() or "exec" in n_type.lower():
             found_risks.add(n_type)
             
    # Recursively check subgraphs? 
    # Yes, ideally. But standard scan usually checks top level or flattened.
    # If SubGraphs are expanded, good. If they are referenced by path, we might miss them.
    # For now, strict top-level scan.
    
    return len(found_risks) > 0, list(found_risks)
