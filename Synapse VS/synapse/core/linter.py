
class GraphLinter:
    """
    Static analysis tool to check graph integrity and identify common issues before runtime.
    """
    
    LEVEL_INFO = "INFO"
    LEVEL_WARNING = "WARNING"
    LEVEL_ERROR = "ERROR"
    
    def __init__(self, node_registry=None):
        self.node_registry = node_registry

    def lint(self, graph_data):
        """
        Analyzes the graph data (dict) and returns a list of issues.
        Issue format: {"level": STR, "node_id": STR, "node_name": STR, "message": STR}
        """
        issues = []
        
        nodes = graph_data.get("nodes", [])
        wires = graph_data.get("wires", [])
        
        node_map = {n["id"]: n for n in nodes}
        
        # 1. Build Adjacency
        # input_map: node_id -> count of incoming wires (Flow or Data?)
        # For dead nodes, we care about FLOW inputs mostly, but data inputs matter too.
        # Actually, a node with NO inputs (and not a Start/Event) is dead.
        incoming_wires = {n["id"]: 0 for n in nodes}
        outgoing_wires = {n["id"]: 0 for n in nodes}
        
        for w in wires:
            to_node = w.get("to_node")
            from_node = w.get("from_node")
            if to_node in incoming_wires: incoming_wires[to_node] += 1
            if from_node in outgoing_wires: outgoing_wires[from_node] += 1
            
        # 2. Check Dead Nodes (No Inputs)
        for n in nodes:
            nid = n["id"]
            ntype = n["type"]
            nname = n.get("title", ntype) # Use title if renamed, else type
            
            # Exemptions
            if "Start" in ntype or "Event" in ntype or "Tick" in ntype:
                continue
                
            if incoming_wires[nid] == 0:
                issues.append({
                    "level": self.LEVEL_WARNING,
                    "node_id": nid,
                    "node_name": nname,
                    "message": "Node is disconnected (No inputs). It will never execute."
                })

        # 3. Check Infinite Loops (While Loops with no Exit?)
        # Heuristic: If "While" node, check if "Loop" flow eventually leads back to it?
        # That's hard to trace statically without full traversal.
        # Simpler check: Does a While loop have ANY output on its "Exit" or "Done" port?
        # If not, it MIGHT be an infinite loop (unless it breaks internally).
        # Actually, checking if "Loop" port is wired is more important. A While loop with no body is useless but safe (checks condition -> false -> exit).
        # Infinite loop is: Condition always true AND body path never breaks.
        # Static analysis of condition is impossible.
        # We can only warn about suspicious structures.
        
        # 4. Check Missing Properties / Configuration
        for n in nodes:
            nid = n["id"]
            ntype = n["type"]
            nname = n.get("title", ntype)
            props = n.get("properties", {})
            
            if ntype == "Python Node":
                if not props.get("code") and not props.get("script"):
                     issues.append({
                        "level": self.LEVEL_ERROR,
                        "node_id": nid,
                        "node_name": nname,
                        "message": "Python Node has no code."
                    })
            
            if ntype == "HTTP Request":
                if not props.get("url"):
                    issues.append({
                        "level": self.LEVEL_ERROR,
                        "node_id": nid,
                        "node_name": nname,
                        "message": "HTTP Request URL is empty."
                    })

        # 5. Type Mismatches (Requires Port Registry info)
        # This requires knowing the port types.
        # If we have access to node registry, we can check.
        # For now, we skip heavy type checking as we don't have the graph object fully instantiated here, just JSON.
        
        return issues
