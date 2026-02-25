import os
import json
import uuid
from synapse.gui.node_widget import NodeWidget
from synapse.nodes.registry import NodeRegistry
from synapse.core.types import DataType

class NodeFactory:
    def __init__(self, scene):
        self.scene = scene

    # [REMOVED] Local analyze_subgraph_ports removed in favor of synapse.core.subgraph_utils

    def configure_node_ports(self, new_node, node_type_label, node_instance=None):
        node_class = NodeRegistry.get_node_class(node_type_label)
        if node_class:
            target_instance = node_instance
            def get_defaults(attr_name, default=[]):
                # Priority: 
                # 1. Instance attributes (important for dynamic schemas)
                if target_instance and hasattr(target_instance, attr_name):
                    val = getattr(target_instance, attr_name)
                    if not isinstance(val, property): return val
                
                # 2. Class attributes
                val = getattr(node_class, attr_name, None)
                if isinstance(val, property):
                     # 3. Dummy Instance
                     try: dummy = node_class("temp_id", "temp_name", None)
                     except: return default
                     return getattr(dummy, attr_name, default)
                return val if val is not None else default

            inputs = get_defaults('default_inputs')
            if inputs:
                for inp in inputs:
                    if isinstance(inp, tuple):
                        d_type = inp[1]
                        
                        # Robust Flow Detection (Enum or String)
                        is_flow = False
                        if d_type in [DataType.FLOW, DataType.PROVIDER_FLOW]:
                            is_flow = True
                        elif str(d_type).lower() in ["flow", "datatype.flow", "provider_flow", "datatype.provider_flow"]:
                            is_flow = True
                        elif inp[0] == "Flow": # Hard-coded exception for the main flow port
                            is_flow = True
                            d_type = DataType.FLOW
                            
                        p_cls = "flow" if is_flow else "data"
                        if inp[0] not in [p.name for p in new_node.inputs]:
                            new_node.add_input(inp[0], port_class=p_cls, data_type=d_type)
                    else: 
                        if inp not in [p.name for p in new_node.inputs]:
                            new_node.add_input(inp, data_type=DataType.ANY)
                    
            outputs = get_defaults('default_outputs')
            if outputs:
                for outp in outputs:
                    if isinstance(outp, tuple):
                        d_type = outp[1]
                        
                        # Robust Flow Detection
                        is_flow = False
                        if d_type in [DataType.FLOW, DataType.PROVIDER_FLOW]:
                            is_flow = True
                        elif str(d_type).lower() in ["flow", "datatype.flow", "provider_flow", "datatype.provider_flow"]:
                            is_flow = True
                        elif outp[0] == "Flow":
                            is_flow = True
                            d_type = DataType.FLOW

                        p_cls = "flow" if is_flow else "data"
                        if outp[0] not in [p.name for p in new_node.outputs]:
                            new_node.add_output(outp[0], port_class=p_cls, data_type=d_type)
                    else: 
                        d_type = DataType.ANY
                        is_flow = outp.lower() in ["flow", "exec", "out"]
                        p_cls = "flow" if is_flow else "data"
                        if is_flow: d_type = DataType.FLOW
                        
                        if outp not in [p.name for p in new_node.outputs]:
                            new_node.add_output(outp, port_class=p_cls, data_type=d_type)

            # SubGraph Specific Analysis (Legacy/External Support)
            # Only run if we don't have an instance that already handles this via rebuild_ports
            if not target_instance or not hasattr(target_instance, 'input_types'):
                path = getattr(node_class, "graph_path", None)
                if path and os.path.exists(path):
                    try:
                        with open(path, 'r') as f: data = json.load(f)
                        from synapse.core.subgraph_utils import analyze_subgraph_ports
                        inputs, flow_ports, _ = analyze_subgraph_ports(data)
                        for inp in inputs:
                            if inp not in [p.name for p in new_node.ports]: new_node.add_input(inp, port_class="data")
                        for label, d_ports in flow_ports:
                            if label not in [p.name for p in new_node.ports]: new_node.add_output(label, port_class="flow")
                            for dp in d_ports:
                                if dp not in [p.name for p in new_node.ports]: new_node.add_output(dp, port_class="data")
                    except Exception as e: print(f"Error auto-configuring SubGraph ports: {e}")
        else:
             print(f"Warning: Node type '{node_type_label}' not found.")

    def create_standard_node(self, node_type, pos):
        new_node = NodeWidget(node_type)
        new_node.setPos(pos)
        
        node_class = NodeRegistry.get_node_class(node_type)
        logical_node = None
        if node_class:
            node_id = str(uuid.uuid4())
            try:
                logical_node = node_class(node_id, node_type, None)
                path = getattr(node_class, "graph_path", None)
                if path: logical_node.properties["graph_path"] = path
                new_node.node = logical_node
            except Exception as e: print(f"Error instantiating logical node {node_type}: {e}")
        
        self.configure_node_ports(new_node, node_type, node_instance=logical_node)
        if "Python Script" in node_type and hasattr(new_node, "_sync_python_auto_vars"):
            new_node._sync_python_auto_vars()
            
        self.scene.addItem(new_node)
        return new_node

    def create_subgraph_node(self, file_path, pos):
        try:
            with open(file_path, 'r') as f: data = json.load(f)
        except Exception as e:
            print(f"Failed to load subgraph file: {e}")
            return

        from synapse.core.subgraph_utils import analyze_subgraph_ports
        inputs_to_add, flow_ports_to_add, _ = analyze_subgraph_ports(data)
        p_name = data.get("project_name", "").strip()
        label = p_name if p_name else os.path.basename(file_path)
        
        # [FIX] Check if this SubGraph is already registered as a Class (e.g. from Node Library)
        # If so, delegate to create_standard_node to use the Dynamic Class with correct graph_path.
        if NodeRegistry.get_node_class(label):
             # Ensure the registered class actually has the graph_path we expect?
             # Or trust the label. 
             # If we just registered it, it should be fine.
             return self.create_standard_node(label, pos)
        
        new_node = NodeWidget(label) 
        new_node.setPos(pos)
        
        node_class = NodeRegistry.get_node_class("SubGraph Node")
        if node_class:
            node_id = str(uuid.uuid4())
            try:
                logical_node = node_class(node_id, "SubGraph", None)
                logical_node.properties["graph_path"] = file_path
                new_node.node = logical_node
                
                new_node.add_input("Flow")
                for inp in inputs_to_add: new_node.add_input(inp)
                
                # If no flow ports found (rare), force one
                if not flow_ports_to_add: 
                    new_node.add_output("Flow", port_class="flow")
                
                for label, d_ports in flow_ports_to_add:
                    # Flow Port (Green)
                    if label not in [p.name for p in new_node.ports]: 
                        new_node.add_output(label, port_class="flow")
                    
                    # Data Ports (Blue)
                    for dp in d_ports:
                        if dp not in [p.name for p in new_node.ports]: 
                            new_node.add_output(dp, port_class="data")
                
                new_node.update_subgraph_status(True)
                self.scene.addItem(new_node)
            except Exception as e: print(f"Error creating SubGraph node: {e}")
        return new_node