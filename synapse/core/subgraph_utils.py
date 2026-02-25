import os
import json
from synapse.core.types import DataType

def analyze_subgraph_ports(data):
    """
    Unified logic to extract Dynamic Inputs and Outputs from a SubGraph.
    Used by both NodeFactory (for UI) and SubGraphNode (for logic).
    
    Returns: (inputs_to_add, flow_ports_to_add, label_to_gui)
    where flow_ports_to_add is a list of tuples: (label, data_ports)
    and label_to_gui maps raw Return Node labels to their GUI pin labels.
    """
    inputs_to_add = [] 
    flow_ports_to_add = []
    
    start_node = None
    return_nodes = []
    
    for n in data.get("nodes", []):
        if n["type"] == "Start Node": start_node = n
        elif n["type"] == "Return Node": return_nodes.append(n)
    
    if not start_node: return [], [], {}

    # 1. Analyze Inputs (Start Node Outputs)
    # Check both Title Case and lowercase for compatibility
    props = start_node.get("properties", {})
    start_outputs = props.get("Additional Outputs") or props.get("additional_outputs") or start_node.get("outputs")
        
    if not start_outputs:
        # Fallback: Scan wires from Start Node
        start_id = start_node["id"]
        if "wires" in data:
            for w in data["wires"]:
                if w["from_node"] == start_id:
                     port = w.get("from_port")
                     if port and port != "Flow":
                         if port not in inputs_to_add: inputs_to_add.append(port)
    else:
        for out in start_outputs:
            if out != "Flow": inputs_to_add.append(out)

    # 2. Analyze Outputs (Return Nodes)
    label_to_gui = {}
    
    for r_node in return_nodes:
         r_props = r_node.get("properties", {})
         # Priority: 1. "Label" property, 2. "label" property, 3. Node Name, 4. Default
         raw_label = r_props.get("Label") or r_props.get("label") or r_node.get("name") or "Return Node"
         
         data_ports = []
         r_inputs = r_props.get("Additional Inputs") or r_props.get("additional_inputs") or r_node.get("inputs")
             
         if not r_inputs:
             # Fallback: Scan wires to Return Node
             r_id = r_node["id"]
             if "wires" in data:
                 for w in data["wires"]:
                     if w["to_node"] == r_id:
                         port = w.get("to_port")
                         if port and port not in ["Flow", "In", "Exec"]:
                             if port not in data_ports: data_ports.append(port)
         else:
              for inp in r_inputs:
                  if inp not in ["Flow", "In", "Exec"]: data_ports.append(inp)
         
         # Naming Logic:
         label = raw_label
         is_generic = label in ["Return Node", "Return", "Return Search"]
         
         if len(return_nodes) == 1 and is_generic:
             label = "Flow"
         elif not label:
             label = "Flow"
         else:
             # Prefix collision check: if the label is already a data port, disambiguate
             if label in data_ports:
                 label = f"{label} Flow"

             # Uniqueness within this node
             base_label = label
             counter = 1
             while any(o[0] == label for o in flow_ports_to_add):
                 label = f"{base_label}_{counter}"
                 counter += 1

         label_to_gui[raw_label] = label

         # Map variables directly to their raw names
         prefixed_data_ports = []
         for dp in data_ports:
             prefixed_data_ports.append(dp)
         
         flow_ports_to_add.append((label, prefixed_data_ports))
         
    return inputs_to_add, flow_ports_to_add, label_to_gui
