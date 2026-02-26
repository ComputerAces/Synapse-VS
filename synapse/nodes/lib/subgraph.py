from synapse.core.super_node import SuperNode
from synapse.nodes.registry import NodeRegistry
from synapse.core.bridge import SynapseBridge
from synapse.core.engine import ExecutionEngine
from synapse.core.types import DataType

@NodeRegistry.register("SubGraph Node", "Flow/SubGraph")
class SubGraphNode(SuperNode):
    """
    Executes a nested graph (subgraph) as a single node within the current context.
    
    This node allows for hierarchical graph design and logic reuse. It dynamically 
    generates input and output ports based on the 'Start' and 'Return' nodes found 
    within the child graph file.
    
    Inputs:
    - Flow: Trigger execution of the subgraph.
    - GraphPath: Path to the .syp graph file to load.
    - [Dynamic Inputs]: Data variables passed into the subgraph's Start node.
    
    Outputs:
    - Flow: Pulse triggered when the subgraph reaches a Return node.
    - Error Flow: Pulse triggered if the subgraph fails to load or execute.
    - [Dynamic Outputs]: Data variables returned from the subgraph's Return node.
    """
    version = "2.1.0"
    allow_dynamic_inputs = True
    allow_dynamic_outputs = True

    def __init__(self, node_id, name, bridge):
        self.properties = {} # Initialize properties dict first
        self.input_types = {}
        self.output_types = {}
        
        super().__init__(node_id, name, bridge)
        self.is_native = True
        self.properties["Graph Path"] = ""
        self.properties["Embedded Data"] = None
        self.properties["Isolated"] = False
        self._last_mtime = 0
        
        # Hide system properties from the properties panel
        self.define_schema()
        # registration handled by super().__init__ calling register_handlers()

    def register_handlers(self):
        self.register_handler("Flow", self.do_work)

    def define_schema(self):
        """
        SubGraphs have dynamic schemas based on their internal variables.
        """
        self.input_schema = {
            "Flow": DataType.FLOW,
            "Graph Path": DataType.STRING,
            "Embedded Data": DataType.ANY,
            "Isolated": DataType.BOOLEAN
        }
        dynamic_inputs = self._build_dynamic_inputs()
        if dynamic_inputs:
            for name, dtype in dynamic_inputs:
                self.input_schema[name] = dtype
                
        # 2. Outputs - ORDER MATTERS (Flow at top)
        new_outputs = {}
        
        # Get dynamic items first
        dynamic_outputs = self._build_dynamic_outputs()
        
        # Priority 1: Main "Flow"
        has_flow = False
        if dynamic_outputs:
            for name, dtype in dynamic_outputs:
                if name == "Flow":
                    new_outputs[name] = DataType.FLOW
                    has_flow = True
                    break
        if not has_flow:
            new_outputs["Flow"] = DataType.FLOW
            
        # Priority 2: Error Flow
        new_outputs["Error Flow"] = DataType.FLOW
        
        # Priority 3: The rest of the dynamic ports
        if dynamic_outputs:
            for name, dtype in dynamic_outputs:
                if name not in ["Flow", "Error Flow"]:
                    new_outputs[name] = dtype
                    
        self.output_schema = new_outputs

        # Populate internal type caches for UI sync
        self.input_types = self.input_schema.copy()
        self.output_types = self.output_schema.copy()

    def _build_dynamic_inputs(self):
        """Scans child graph for Start Node and builds data inputs."""
        data = self._get_graph_data_for_outputs()
        if not data: return []
        
        from synapse.core.subgraph_utils import analyze_subgraph_ports
        inputs, _, _ = analyze_subgraph_ports(data)
        return [(name, DataType.ANY) for name in inputs]

    def _build_dynamic_outputs(self):
        """Dynamically builds outputs from the child graph's Return Nodes."""
        data = self._get_graph_data_for_outputs()
        if not data:
            return [("Flow", DataType.FLOW)]
        
        from synapse.core.subgraph_utils import analyze_subgraph_ports
        _, flow_ports, _ = analyze_subgraph_ports(data)
        
        outputs = []
        for label, data_ports in flow_ports:
             outputs.append((label, DataType.FLOW))
             for dp in data_ports:
                 outputs.append((dp, DataType.ANY))
        
        if not outputs:
            outputs.append(("Flow", DataType.FLOW))
        
        # [ORDERING] Ensure "Flow" is always at the top if it exists
        # We sort based on whether it's a Flow type or not.
        # But we want to keep data ports UNDER their respective Flow labels.
        # Actually, the user said "our 'Flow' output should be above the vars for it"
        # The current interleaved append (Flow, then its data) already does this.
        # However, if there are MULTIPLE Return nodes, they look like:
        # Flow 1
        # Var 1a
        # Flow 2
        # Var 2a
        # The user might want all Flows at the top. Let's stick to the interleaving
        # but ensure the MAIN "Flow" (generic one) is at the very top.
        
        def sort_key(item):
            name, dtype = item
            if name == "Flow": return 0
            # Keep order otherwise
            return 1

        # We can't simply sort everything because data ports must follow their flows.
        # Let's find the "Flow" item and move it to index 0 if it exists.
        flow_idx = -1
        for i, (name, dtype) in enumerate(outputs):
            if name == "Flow":
                flow_idx = i
                break
        
        if flow_idx > 0:
            flow_item = outputs.pop(flow_idx)
            outputs.insert(0, flow_item)
            
        return outputs

    def _get_graph_data_for_outputs(self):
        """Loads and returns the child graph's JSON data for port analysis."""
        import json, os
        # Priority: 1. File on Disk (always freshest), 2. Embedded Data (fallback)
        
        # 1. Resolve Graph Path and try loading from file first
        graph_path = self.properties.get("Graph Path") or \
                     self.properties.get("GraphPath") or \
                     self.properties.get("graph_path") or \
                     getattr(self.__class__, "graph_path", None)
        
        if graph_path:
            try:
                abs_path = os.path.abspath(graph_path)
                if os.path.exists(abs_path):
                    with open(abs_path, 'r') as f:
                        return json.load(f)
            except:
                pass
        
        # 2. Fallback to Embedded Data
        embedded = self.properties.get("Embedded Data") or \
                   self.properties.get("EmbeddedData") or \
                   self.properties.get("embedded_data")
        if embedded and isinstance(embedded, dict):
            return embedded
            
        return None

    def rebuild_ports(self):
        """Refreshes all ports after graph change."""
        self.define_schema()
        # SuperNode doesn't use input_types/output_types directly but define_schema does essentially the same
         
    def do_work(self, **kwargs):
        # Resolve Properties (with Input Overrides)
        graph_path = kwargs.get("Graph Path") or \
                     self.properties.get("Graph Path") or \
                     self.properties.get("GraphPath") or \
                     self.properties.get("graph_path") or \
                     getattr(self.__class__, "graph_path", "")

        embedded_data = kwargs.get("Embedded Data") or \
                        self.properties.get("Embedded Data") or \
                        self.properties.get("EmbeddedData") or \
                        self.properties.get("embedded_data")

        isolated = kwargs.get("Isolated") if "Isolated" in kwargs else self.properties.get("Isolated", False)
        
        import json, os
        data = None
        if embedded_data and isinstance(embedded_data, dict):
            data = embedded_data
        elif graph_path:
             try:
                if os.path.exists(graph_path):
                    with open(graph_path, 'r') as f:
                        data = json.load(f)
             except Exception as e:
                 self.logger.error(f"Failed to load subgraph file '{graph_path}': {e}")

        if not data:
            self.logger.error(f"Execution Failed: No graph data found. Path: {graph_path}")
            return False

        # Prepare Trace/Speed files
        trace_enabled = self.properties.get("IsDebug", False)
        speed_file = None
        
        # Prepare Child Bridge
        import multiprocessing
        # [OPTIMIZATION] Reuse parent manager if available to avoid expensive process spawn
        manager = getattr(self.bridge, "manager", None)
        local_manager = False
        
        if manager is None:
            manager = multiprocessing.Manager()
            local_manager = True
            
        try:
            child_bridge = SynapseBridge(manager)

            # Inherit control files from parent bridge (set by parent engine)
            stop_file = self.bridge.get("_SYSTEM_STOP_FILE")
            pause_file = self.bridge.get("_SYSTEM_PAUSE_FILE")

            child_engine = ExecutionEngine(
                child_bridge, 
                headless=False,
                delay=0.0,
                parent_bridge=self.bridge,
                parent_node_id=self.node_id,
                trace=trace_enabled,
                speed_file=speed_file,
                stop_file=stop_file,
                pause_file=pause_file,
                source_file=graph_path,
                initial_context=kwargs.get("_context_stack", []) if not isolated else []
            )
            
            from synapse.core.loader import load_graph_data
            load_graph_data(data, child_bridge, child_engine)
                
            # Find Start Node ID first — needed for bridge key injection
            start_id = None
            for n_data in data["nodes"]:
                if n_data["type"] == "Start Node":
                    start_id = n_data["id"]
                    break
            
            # Inject parent kwargs into child bridge
            child_registry = child_engine.port_registry
            for k, v in kwargs.items():
                if k.startswith("_") or k == "Flow":
                    continue
                child_bridge.set(k, v, "Parent_Injection")
                if start_id:
                    # Legacy key
                    child_bridge.set(f"{start_id}_{k}", v, "Parent_Injection")
                    # UUID key
                    uuid_key = child_registry.bridge_key(start_id, k, "output")
                    child_bridge.set(uuid_key, v, "Parent_Injection")

            parent_sub_id = self.bridge.get("_SYNP_SUBGRAPH_ID")
            sub_id = f"{parent_sub_id} > {self.name}" if parent_sub_id else self.name
            child_bridge.set("_SYNP_SUBGRAPH_ID", sub_id, "Parent_Injection")

            system_props = ["Graph Path", "GraphPath", "graph_path", "Embedded Data", "EmbeddedData", "embedded_data", "node_id", "name"]
            for k, v in self.properties.items():
                if k not in system_props:
                    child_bridge.set(k, v, "Parent_Property_Injection")

            try:
                parent_keys = self.bridge.get_all_keys()
                for pk in parent_keys:
                    if pk.startswith("Global:"):
                        var_name = pk.split(":", 1)[1]
                        val = self.bridge.get(var_name)
                        child_bridge.set(var_name, val, "Parent_Scope_Inheritance")
            except Exception as e:
                self.logger.warning(f"Failed to inherit global variables: {e}")
                
            if start_id:
                try:
                    child_engine.run(start_id)
                except Exception as e:
                    self.logger.error(f"Nested SubGraph Failed: {e}")
                    from synapse.core.data import ErrorObject
                    error_obj = ErrorObject(
                        project_name=f"SubGraph: {self.name}",
                        node_name=self.name,
                        inputs={k:v for k,v in kwargs.items() if not k.startswith("_")},
                        error_details={"message": str(e), "type": type(e).__name__}
                    )
                    self.bridge.set(f"{self.node_id}_LastError", error_obj, self.name)
                    
                    self.bridge.set(f"{self.node_id}_ActivePorts", ["Error Flow"], self.name)
                    return False

            results = child_bridge.get("SUBGRAPH_RETURN") or {}
            raw_label = child_bridge.get("__RETURN_NODE_LABEL__")

            # Use subgraph_utils to get the SAME mapping used by the GUI
            from synapse.core.subgraph_utils import analyze_subgraph_ports
            _, _, label_to_gui = analyze_subgraph_ports(data)
            
            gui_label = label_to_gui.get(raw_label, raw_label)
            
            # Track which ports were actually updated
            captured_ports = set()
            for k, v in results.items():
                self.set_output(k, v)
                captured_ports.add(k)
            
            # [PORT MISMATCH REPORTING]
            for expected_port in self.output_schema.keys():
                if expected_port in ["Flow", "Error Flow"]: continue
                if expected_port not in captured_ports:
                    error_msg = f"[PORT MISMATCH] SubGraph '{self.name}' expected output '{expected_port}' but child graph returned: {list(results.keys()) or 'No Data'}"
                    self.logger.error(error_msg)
                    self.bridge.set(f"{self.node_id}_LastError", error_msg, self.name)
                
            active_ports = [gui_label] if gui_label else ["Flow"]
            self.bridge.set(f"{self.node_id}_ActivePorts", active_ports, self.name)
            return True
        finally:
            # CRITICAL: Clean up the Manager process to prevent leaks (ONLY if we created it)
            if local_manager:
                manager.shutdown()
