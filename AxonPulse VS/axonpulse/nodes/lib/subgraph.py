from axonpulse.core.super_node import SuperNode
from axonpulse.nodes.registry import NodeRegistry
from axonpulse.core.bridge import AxonPulseBridge
from axonpulse.core.engine import ExecutionEngine
from axonpulse.core.types import DataType
from axonpulse.utils.file_utils import smart_load

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
    version = "2.3.0"
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
        
        # [PATCH] Backwards compatibility for legacy saves that have old keys and overriding empty defaults
        if "Graph_Path" in self.properties:
            if not self.properties.get("Graph Path"):
                self.properties["Graph Path"] = self.properties["Graph_Path"]
            del self.properties["Graph_Path"]
        if "graph_path" in self.properties:
            if not self.properties.get("Graph Path"):
                self.properties["Graph Path"] = self.properties["graph_path"]
            del self.properties["graph_path"]
        if "Embedded_Data" in self.properties:
            if not self.properties.get("Embedded Data"):
                self.properties["Embedded Data"] = self.properties["Embedded_Data"]
            del self.properties["Embedded_Data"]
        
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
        
        from axonpulse.core.subgraph_utils import analyze_subgraph_ports
        inputs, _, _ = analyze_subgraph_ports(data)
        return [(name, DataType.ANY) for name in inputs]

    def _build_dynamic_outputs(self):
        """Dynamically builds outputs from the child graph's Return Nodes."""
        data = self._get_graph_data_for_outputs()
        if not data:
            return [("Flow", DataType.FLOW)]
        
        from axonpulse.core.subgraph_utils import analyze_subgraph_ports
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

    def _resolve_graph_path(self, graph_path, parent_file=None):
        """Resolves a graph_path using a 4-step fallback chain.
        
        Priority: Local project files ALWAYS override plugin/builtin files.
        1. Search sub_graphs/ for a local override (by basename)
        2. Try the path as-is (absolute or relative to CWD)
        3. Try relative to the parent graph's directory
        4. Return None (caller should fall back to embedded data)
        
        Returns: resolved absolute path or None
        """
        import os
        if not graph_path:
            return None
        
        basename = os.path.basename(graph_path)
        
        # 1. Local override: search sub_graphs/ for a file with the same basename
        # This enables "hot override" of plugin SubGraphs with project-local versions
        sub_graphs_dir = os.path.join(os.getcwd(), "sub_graphs")
        if os.path.isdir(sub_graphs_dir):
            for root, dirs, files in os.walk(sub_graphs_dir):
                if basename in files:
                    local_path = os.path.join(root, basename)
                    return os.path.abspath(local_path)
        
        # 2. Absolute / relative to CWD
        abs_path = os.path.abspath(graph_path)
        if os.path.exists(abs_path):
            return abs_path
        
        # 3. Relative to parent graph's directory
        if parent_file:
            parent_dir = os.path.dirname(os.path.abspath(parent_file))
            relative_path = os.path.join(parent_dir, basename)
            if os.path.exists(relative_path):
                return relative_path
        
        return None

    def _get_graph_data_for_outputs(self):
        """Loads and returns the child graph's JSON data for port analysis."""
        import os
        # Priority: 1. File on Disk (always freshest), 2. Embedded Data (fallback)
        
        # 1. Resolve Graph Path and try loading from file first
        graph_path = self.properties.get("Graph Path") or \
                     self.properties.get("GraphPath") or \
                     self.properties.get("graph_path") or \
                     getattr(self.__class__, "graph_path", None)
        
        resolved = self._resolve_graph_path(graph_path)
        if resolved:
            try:
                return smart_load(resolved)
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
        
        import os
        data = None
        
        # Priority: 1. File on Disk (freshest), 2. Embedded Data (fallback)
        # Use _resolve_graph_path for the 3-step fallback (absolute → relative → None)
        parent_file = kwargs.get("_source_file") or getattr(self, "_source_file", None)
        resolved = self._resolve_graph_path(graph_path, parent_file)
        
        if resolved:
            try:
                data = smart_load(resolved)
                graph_path = resolved  # Update for downstream use
            except Exception as e:
                self.logger.error(f"Failed to load subgraph file '{resolved}': {e}")
        
        # 2. Fallback to Embedded Data
        if not data and embedded_data and isinstance(embedded_data, dict):
            data = embedded_data

        if not data:
            self.logger.error(f"Execution Failed: No graph data found. Path: {graph_path}")
            return False

        # Prepare Trace/Speed files
        trace_enabled = self.properties.get("IsDebug", False)
        
        # Prepare Child Bridge
        import multiprocessing
        # [OPTIMIZATION] Reuse parent manager if available to avoid expensive process spawn
        manager = getattr(self.bridge, "manager", None)
        local_manager = False
        
        if manager is None:
            # Fallback for isolated contexts or mock bridges
            import multiprocessing
            manager = multiprocessing.Manager()
            local_manager = True
            
        try:
            # [FIX] Surgical state passing. 
            # SubGraphs should share parent "System State" (hardware locks) to avoid OpenCV crashes,
            # but MUST have isolated "Data State" (registries) to avoid Global Variable collisions.
            system_state = self.bridge.get_system_state()
            child_bridge = AxonPulseBridge(manager, system_state=system_state)

            # [FIX] Protect parent context by injecting identifying node ID
            # This allows ReturnNode to write to a scoped key SUBGRAPH_RETURN_{node_id}
            child_bridge.set("_AXON_PARENT_NODE_ID", self.node_id, "Parent_Injection")
            
            # [NEW] Propagate the trigger type (Flow vs Provider Flow)
            parent_trigger = kwargs.get("_trigger", "Flow")
            child_bridge.set("_AXON_PARENT_TRIGGER", parent_trigger, "Parent_Injection")

            # Inherit control files from parent bridge (set by parent engine)
            stop_file = self.bridge.get("_SYSTEM_STOP_FILE")
            pause_file = self.bridge.get("_SYSTEM_PAUSE_FILE")
            speed_file = self.bridge.get("_SYSTEM_SPEED_FILE")

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
            
            from axonpulse.core.loader import load_graph_data
            load_graph_data(data, child_bridge, child_engine)
                
            # Find Start Node ID first — needed for bridge key injection
            start_id = None
            for n_data in data["nodes"]:
                if n_data["type"] == "Start Node":
                    start_id = n_data["id"]
                    break
            
            # Inject parent kwargs into child bridge
            child_registry = child_engine.port_registry
            
            # [FIX] System properties must be filtered from BOTH kwargs and self.properties
            # to prevent Graph Path/Embedded Data from leaking down the SubGraph chain
            system_props = {"Graph Path", "GraphPath", "graph_path", "Embedded Data", "EmbeddedData", "embedded_data", "Isolated", "node_id", "name"}
            
            for k, v in kwargs.items():
                if k.startswith("_") or k == "Flow" or k in system_props:
                    continue
                child_bridge.set(k, v, "Parent_Injection")
                if start_id:
                    # Legacy key
                    child_bridge.set(f"{start_id}_{k}", v, "Parent_Injection")
                    # UUID key
                    uuid_key = child_registry.bridge_key(start_id, k, "output")
                    child_bridge.set(uuid_key, v, "Parent_Injection")

            parent_sub_id = self.bridge.get("_AXON_SUBGRAPH_ID")
            sub_id = f"{parent_sub_id} > {self.name}" if parent_sub_id else self.name
            child_bridge.set("_AXON_SUBGRAPH_ID", sub_id, "Parent_Injection")

            for k, v in self.properties.items():
                if k not in system_props and k not in kwargs:
                    child_bridge.set(k, v, "Parent_Property_Injection")

            try:
                parent_keys = self.bridge.get_all_keys()
                for pk in parent_keys:
                    if pk.startswith("Global:"):
                        var_name = pk.split(":", 1)[1]
                        # [FIX] Do NOT inherit _AXON_PARENT_ keys from grandparent — 
                        # they would overwrite this SubGraph's own parent context.
                        if var_name.startswith("_AXON_PARENT_"):
                            continue
                        val = self.bridge.get(var_name)
                        child_bridge.set(var_name, val, "Parent_Scope_Inheritance")
            except Exception as e:
                self.logger.warning(f"Failed to inherit global variables: {e}")
            
            # [FIX] Set correct parent context AFTER global inheritance to prevent overwrite
            child_bridge.set("_AXON_PARENT_NODE_ID", self.node_id, "Parent_Injection")
            child_bridge.set("_AXON_PARENT_TRIGGER", kwargs.get("_trigger", "Flow"), "Parent_Injection")
                
            if start_id:
                try:
                    child_engine.run(start_id)
                except Exception as e:
                    import traceback
                    self.logger.error(f"Nested SubGraph Failed: {e}\n{traceback.format_exc()}")
                    from axonpulse.core.data import ErrorObject
                    error_obj = ErrorObject(
                        project_name=f"SubGraph: {self.name}",
                        node_name=self.name,
                        inputs={k:v for k,v in kwargs.items() if not k.startswith("_")},
                        error_details={"message": str(e), "type": type(e).__name__}
                    )
                    self.bridge.bubble_set(f"{self.node_id}_LastError", error_obj, self.name)
                    
                    self.bridge.bubble_set(f"{self.node_id}_ActivePorts", ["Error Flow"], self.name)
                    return False

            # [FIX] Retrieve results from instance-specific scoped key
            scoped_return_key = f"SUBGRAPH_RETURN_{self.node_id}"
            results = child_bridge.get(scoped_return_key) or {}
            self.logger.info(f"Retrieved results from {scoped_return_key}: {list(results.keys())}")
            # [NUCLEAR SCRUB] Final safety pass before setting parent outputs.
            # This ensures that NO UI metadata survives the child-to-parent transfer.
            reserved = ["Flow", "Exec", "In", "_trigger", "_bridge", "_engine", "_context_stack", "_context_pulse"]
            blocked_keywords = ["color", "additional", "schema", "label", "context", "provider"]
            
            # Step A: Remove blocked keys from results
            to_delete = [k for k in results if any(kw in k.lower() for kw in blocked_keywords) or k in reserved]
            for k in to_delete:
                del results[k]

            raw_label = child_bridge.get("__RETURN_NODE_LABEL__")

            # Use subgraph_utils to get the SAME mapping used by the GUI
            from axonpulse.core.subgraph_utils import analyze_subgraph_ports
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
                    warn_msg = f"[PORT MISMATCH] SubGraph '{self.name}' expected output '{expected_port}' but child graph returned: {list(results.keys()) or 'No Data'}"
                    self.logger.warning(warn_msg)
                    # Default missing data ports to None so downstream nodes don't crash
                    self.set_output(expected_port, None)
                
            active_ports = [gui_label] if gui_label else ["Flow"]
            self.bridge.set(f"{self.node_id}_ActivePorts", active_ports, self.name)
            return True
        finally:
            # CRITICAL: Clean up the Manager process to prevent leaks (ONLY if we created it)
            if local_manager:
                manager.shutdown()
