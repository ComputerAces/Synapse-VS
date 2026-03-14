import time
import os
import threading
import copy
from axonpulse.utils.logger import setup_logger
from axonpulse.core.flow_controller import FlowController
from axonpulse.core.context_manager import ContextManager
from axonpulse.core.node_dispatcher import NodeDispatcher
from axonpulse.core.port_registry import PortRegistry
from axonpulse.core.dependencies import DependencyManager

from .data_io import DataMixin
from .state_management import StateMixin
from .services import ServiceMixin
from .debugging import DebugMixin

logger = setup_logger("AxonPulseEngine")

class ExecutionEngine(DataMixin, StateMixin, ServiceMixin, DebugMixin):
    """
    Manages the execution flow of the AxonPulse graph.
    Refactored to use Hybrid Architecture (FlowController, ContextManager, NodeDispatcher)
    and Modular Mixins.
    """
    def __init__(self, bridge, headless=False, delay=0.0, pause_file=None, speed_file=None, stop_file=None, trace=True, parent_bridge=None, parent_node_id=None, source_file=None, initial_context=None):
        self.bridge = bridge
        self.parent_bridge = parent_bridge
        self.parent_node_id = parent_node_id
        # [CONTEXT BOOTSTRAP] (IMMUTABLE LINKED-LIST TUPLES)
        # Convert list to tuple-linked list if needed
        self.initial_context = initial_context if initial_context is not None else None
        # The ContextManager will handle converting initial_context to the correct internal format.
        # This line is removed as context_manager is initialized later.
        # if isinstance(self.initial_context, list):
        #      self.initial_context = self.context_manager.stack_from_list(self.initial_context)

        self.nodes = {} 
        self.wires = [] 
        self.headless = headless
        self.delay = delay
        self.pause_file = pause_file if pause_file else "axonpulse.pause"
        self.speed_file = speed_file
        self.stop_file = stop_file
        self.trace = trace
        self.service_registry = {} # node_id -> node instance for cleanup
        self.source_file = source_file
        self._last_mtime = 0
        if self.source_file and os.path.exists(self.source_file):
            self._last_mtime = os.path.getmtime(self.source_file)

        # Expose System State to Bridge
        import platform
        self.bridge.set("_SYSTEM_HEADLESS", self.headless, "Engine")
        self.bridge.set("_SYSTEM_PAUSE_FILE", self.pause_file, "Engine")
        self.bridge.set("_SYSTEM_STOP_FILE", self.stop_file, "Engine")
        self.bridge.set("_SYSTEM_SPEED_FILE", self.speed_file, "Engine")
        self.bridge.set("_OS_TYPE", platform.system(), "Engine")
        
        # [NEW] Set Graph Prefix (Scope ID) for Bridge
        if self.source_file:
            graph_name = os.path.splitext(os.path.basename(self.source_file))[0]
            # Sanitize name for bridge keys
            safe_name = graph_name.replace(" ", "_").replace(":", "_").replace("-", "_")
            
            # [FIX] Randomize Scope for Child Engines to prevent parallel clobbering
            if self.parent_bridge:
                # Use part of the parent node ID and current time for a unique instance scope
                import time
                instance_suffix = f"{str(self.parent_node_id)[:6]}_{int(time.time()*1000) % 1000000}"
                safe_name = f"{safe_name}_{instance_suffix}"
                
            self.bridge.default_scope = safe_name
            logger.info(f"Execution Scope set to: {safe_name}")
        
        # Components
        is_child_engine = self.parent_bridge is not None
        self.dispatcher = NodeDispatcher(bridge, is_child=is_child_engine)
        self.context_manager = ContextManager(bridge, initial_stack=self.initial_context)
        self.port_registry = PortRegistry()
        self.bridge._port_registry = self.port_registry  # Expose to nodes via bridge
        self.history = []
        self._skip_record = False
        
        # Performance Guards
        self._last_control_check = 0
        self._last_reload_check = 0
        self._control_interval = 0.5 # Check controls every 500ms
        self._reload_interval = 2.0  # Check hot reload every 2s
        
        # [NEW] Pulse Tracking & Scoping
        self.scope_pulse_counts = {} # {scope_id: active_pulse_count}
        self.pending_terminations = {} # {scope_id: (stack, prio, delay)}
        self.current_pulse_stack = None # [NEW] Pulse currently being processed
        self._lock = threading.RLock() # [NEW] Protect pulse counts and terminations (Reentrant)
        self.deferred_returns = {} # {scope_id: payload_dict} Lockbox for early returns
        self._stop_event = threading.Event()
        
        # [NEW] Register with CleanupManager for signal-driven stop
        from axonpulse.utils.cleanup import CleanupManager
        CleanupManager.register_engine(self)


    def stop(self):
        """Signals the engine to stop execution and terminate background services."""
        logger.info(f"Engine stop requested for scope: {self.bridge.default_scope}")
        self._stop_event.set()
        
        # 1. Signal to the bridge so nodes and subgraphs can react
        self.bridge.set("_SYSTEM_STOP", True, "System")
        
        # 2. Pulse the speed file if applicable to break out of waiting loops
        if self.speed_file and os.path.exists(self.speed_file):
            try:
                with open(self.speed_file, 'w') as f:
                    f.write("1") 
            except: pass
        


    def register_node(self, node):
        """Registers a node instance with the engine."""
        self.nodes[node.node_id] = node
        # Auto-register all ports for UUID mapping
        self.port_registry.register_node_ports(node)

    def connect(self, from_node, from_port, to_node, to_port):
        """Registers a connection (wire) between nodes."""
        # Register ports (idempotent — safe to call multiple times)
        from_name = self.nodes[from_node].name if from_node in self.nodes else ""
        to_name = self.nodes[to_node].name if to_node in self.nodes else ""
        out_uuid = self.port_registry.register(from_node, from_port, "output", from_name)
        in_uuid = self.port_registry.register(to_node, to_port, "input", to_name)

        wire = {
            "from_node": from_node,
            "from_port": from_port,
            "to_node": to_node,
            "to_port": to_port,
            "from_port_uuid": out_uuid,
            "to_port_uuid": in_uuid,
        }
        self.wires.append(wire)

    def hot_reload_graph(self):
        """Reloads the graph from disk and surgically patches the running engine."""
        if not self.source_file or not os.path.exists(self.source_file):
            return

        logger.info(f"Hot Reloading Graph: {self.source_file}")
        try:
            import json
            with open(self.source_file, 'r') as f:
                data = json.load(f)
            
            # Use apply_live_swap for surgical patching
            if self.apply_live_swap(data):
                # Update mtime to prevent double reload
                self._last_mtime = os.path.getmtime(self.source_file)
                # [TRACE] Notify UI
                if self.trace:
                    print(f"[HOT_RELOAD] {self.source_file}", flush=True)
                logger.info("Hot Reload Successful.")
            else:
                logger.error("Hot Reload Failed.")
        except Exception as e:
            logger.error(f"Hot Reload Error: {e}")

    def apply_live_swap(self, patch_data):
        """
        Surgically patches the running graph state with new data.
        Reuses existing node instances to maintain stateful connections.
        """
        try:
            from axonpulse.core.loader import load_graph_data
            
            # 1. Capture current node ids for deletion tracking
            old_node_ids = set(self.nodes.keys())
            
            # 2. Clear wires (will be repopulated by loader)
            self.wires = []
            
            # 3. Load new data into existing engine structure
            # load_graph_data will reuse nodes from self.nodes if IDs match
            node_map, was_pruned = load_graph_data(patch_data, self.bridge, self, existing_nodes=self.nodes)
            self.nodes = node_map
            
            # 4. Handle Deletions
            new_node_ids = set(n['id'] for n in patch_data.get("nodes", []))
            deleted_ids = old_node_ids - new_node_ids
            for d_id in deleted_ids:
                node = self.nodes.get(d_id)
                if node:
                    # Cleanup Services
                    if hasattr(node, "terminate"):
                        try: node.terminate()
                        except: pass
                    self.service_registry.pop(d_id, None)
                    self.nodes.pop(d_id, None)
                    logger.info(f"[LiveSwap] Removed node {d_id}")

            # 5. Full Wire and Flow Sync
            # Loader repopulated self.wires, but we must ensure FlowController knows.
            self.flow.wires = self.wires
            
            # 5. Notify existing nodes of property updates
            for n_id, node in self.nodes.items():
                if n_id in old_node_ids and hasattr(node, "on_live_swap"):
                    # Pass the node's specific new data if available
                    new_n_data = next((n for n in patch_data.get("nodes", []) if n["id"] == n_id), None)
                    if new_n_data:
                        node.on_live_swap(new_n_data)

            logger.info(f"[LiveSwap] Patch applied. {len(self.nodes)} nodes active.")
            return True
        except Exception as e:
            logger.error(f"[LiveSwap] Patch failed: {e}")
            return False

    def _check_node_upgrades(self):
        """Checks Bridge for any pending node upgrade requests."""
        if not self.bridge: return
        
        # We look for keys starting with NODE_UPGRADE_REQUEST_
        # Since manager.dict doesn't support prefix search well, 
        # we can check all legacy nodes specifically.
        legacy_node_ids = [nid for nid, n in self.nodes.items() if getattr(n, 'is_legacy', False)]
        
        for nid in legacy_node_ids:
            req_key = f"NODE_UPGRADE_REQUEST_{nid}"
            req = self.bridge.get(req_key)
            if req:
                logger.info(f"Processing Upgrade Request for node {nid}...")
                success = self.upgrade_node(nid)
                if success:
                    # Clear request
                    self.bridge.set(req_key, None)
                    logger.info(f"Node {nid} successfully upgraded.")
                    # [TRACE] Notify UI
                    if self.trace:
                         print(f"[NODE_UPGRADED] {nid}", flush=True)

    def upgrade_node(self, node_id):
        """Re-instantiates a node with its latest class from NodeRegistry."""
        old_node = self.nodes.get(node_id)
        if not old_node: return False
        
        from axonpulse.nodes.registry import NodeRegistry
        node_type = getattr(old_node, "node_type", "Unknown")
        node_class = NodeRegistry.get_node_class(node_type)
        if not node_class:
            logger.error(f"Cannot upgrade {node_id}: Type '{node_type}' not found in registry.")
            return False
            
        logger.info(f"Upgrading node {node_id} ('{node_type}') to v{getattr(node_class, 'node_version', 1)}...")
        
        try:
            # 1. Instantiate New Node
            new_node = node_class(old_node.node_id, old_node.name, self.bridge)
            
            # 2. Migrate Properties (Selective)
            # We preserve existing values for ports that still exist in the new schema
            # Loader-managed system properties are also preserved.
            for k, v in old_node.properties.items():
                 # [FIX] Do NOT migrate version-related properties that would make the new node look legacy
                 if k in ["is_legacy", "version_mismatch", "node_version"]:
                     continue
                 
                 # Only migrate if it's a known property or a standard system property
                 if k in new_node.properties or k in ["header_color", "label", "singleton_scope"]:
                     new_node.properties[k] = v
            
            # Ensure new version is set
            new_node.properties["node_version"] = getattr(node_class, "node_version", 1)
            
            # 3. Handle Service Replacement
            if old_node.is_service:
                 try:
                     old_node.terminate()
                 except: pass
                 self.service_registry.pop(node_id, None)
            
            # 4. Update Engine State
            self.nodes[node_id] = new_node
            self.port_registry.register_node_ports(new_node)
            
            if new_node.is_service:
                self.service_registry[node_id] = new_node
                
            return True
        except Exception as e:
            logger.error(f"Node Upgrade failed for {node_id}: {e}", exc_info=True)
            return False

    def run(self, start_node_id, initial_stack=None):
        """
        Executes the graph using components.
        """
        logger.info("Starting Pulse...")
        
        # Use provided stack or engine's initial context
        # The ContextManager will handle converting initial_stack to the correct internal format.
        pulse_stack = initial_stack if initial_stack is not None else self.initial_context

        # [PRE-FLIGHT SCANNER / PRE-WARMING] (Phase 4)
        if hasattr(self, "nodes") and not self.parent_bridge:
            # We only do global pre-warm for the top-level execution engine to avoid infinite hangs on sub-threads
            logger.info("Initializing Pre-Flight Requirement Scan...")
            missing_reqs = set()
            
            for node_id, node in self.nodes.items():
                node_type = type(node).__name__
                node_name = getattr(node, "name", "")
                
                # Dynamic Code requirements
                if "Python" in node_name or "Script" in node_name or "Code" in node_type:
                    explicit_reqs = node.properties.get("Requirements", "")
                    if explicit_reqs:
                        for req in explicit_reqs.splitlines():
                            req = req.strip()
                            if req and not req.startswith("#"):
                                if not DependencyManager.is_installed(req):
                                    missing_reqs.add(req)
                
                # Dynamic node resolution check can be forced here to trigger local `ensure` calls safely.
                # All node constructors run early, so those `ensure` calls technically already triggered.
                # But we explicitly capture Python Script additions which are delayed to logic runtime otherwise.
                
            if missing_reqs:
                logger.warning(f"Pre-Flight Scan found {len(missing_reqs)} missing dependencies.")
                for req in missing_reqs:
                    if not self.headless:
                        # Attempt to auto-install headless or via GUI prompts if needed
                        logger.info(f"Pre-Warming: Attempting to install {req}...")
                        success = DependencyManager.ensure(req)
                        if not success:
                            raise SystemError(f"Pre-Flight Execution Halted: Missing required dependency '{req}' could not be installed.")
                    else:
                        # In headless mode (server), abort immediately to prevent mid-run crash
                        raise SystemError(f"Pre-Flight Execution Halted: Headless runtime is missing dependency '{req}'. Check container image.")
            else:
                logger.info("Pre-Flight Scan completed. All dependencies warmed.")

        # [PRODUCTION MODE VALIDATION]
        start_count = 0
        return_count = 0
        for node_id, node in self.nodes.items():
            ntype = getattr(node, "node_type", "")
            if ntype == "Start Node":
                start_count += 1
            elif ntype == "Return Node":
                return_count += 1
        
        if start_count == 0:
            raise ValueError("[Production Mode] Graph must have at least one Start Node.")
        if start_count > 1:
            logger.warning(f"[Production Mode] Graph has {start_count} Start Nodes. Using provided start_node_id.")
        if return_count == 0:
            logger.warning("[Production Mode] Graph has no Return Node. Execution may not terminate properly.")
        
        # [CONTEXT INITIALIZATION]
        # If this is a child engine (subgraph), inherit parent stack.
        # Otherwise start with the provided or default stack.
        # The ContextManager will handle converting initial_stack to the correct internal format.
        # initial_stack = pulse_stack if pulse_stack is not None else [] # This line is now handled by pulse_stack assignment above
        if self.parent_bridge and self.parent_node_id:
            # SubGraph inheritance: The parent node might have an active stack
            # We can pull it from the bridge if the parent pushed it there, 
            # but usually the run() caller should pass it if known.
            # For now, we allow the Bridge to expose a 'last pulse stack' 
            # but cleaner is to assume a global default or empty for now.
            pass

        self.flow = FlowController(start_node_id, initial_stack=pulse_stack, trace=self.trace)
        
        # Initialize counts
        self.scope_pulse_counts = {"ROOT": 1}
        self.pending_terminations = {}

        
        # Pulse generating UUID
        import uuid
        run_id = str(uuid.uuid4())[:8]
        self.bridge.set("_SYSTEM_RUN_ID", run_id, "Engine")
        
        try:
            # [BARRIER] Block until ALL pulses (including parallel branches) are finished
            while True:
                has_work = self.flow.has_next()
                with self._lock:
                    active_count = self.scope_pulse_counts.get("ROOT", 0)
                
                if not has_work and active_count <= 0:
                    break # Everything is finished
                
                if not has_work:
                    # Waiting for parallel branches to finish or push back to master
                    self._check_scope_terminations()
                    time.sleep(0.01)
                    continue

                # Check for Global Stop Signal
                if self._check_stop_signal():
                    logger.info("Stop signal detected. Terminating execution.")
                    return

                # Check for Yield Signal
                if self.bridge.get("_AXON_YIELD"):
                    logger.info("Yield detected. Returning control.")
                    self.bridge.set("_AXON_YIELD", False, "Engine")
                    return 
                
                # [TIME TRAVEL] Record State
                if not self.headless:
                    self._record_state()
                    
                    if self.bridge.get("_SYSTEM_STEP_BACK"):
                        self.bridge.set("_SYSTEM_STEP_BACK", False, "Engine")
                        self._step_back()
                        self.current_pulse_stack = None
                        continue

                # Deferred Hot Reload Check
                now = time.time()
                if now - self._last_reload_check > self._reload_interval:
                    if self._check_hot_reload() or self.bridge.get("_SYSTEM_FORCE_RELOAD"):
                        self.bridge.set("_SYSTEM_FORCE_RELOAD", False, "Engine")
                        self.hot_reload_graph()
                    
                    # [NEW] Check for Node Upgrades
                    self._check_node_upgrades()
                    
                    self._last_reload_check = now
                
                # 1. Get Next Node
                node_id, pulse_stack, trigger_port = self.flow.pop()
                
                # Check for Delayed Queue Waiting
                if node_id is None:
                    self._check_scope_terminations()
                    time.sleep(0.01)
                    continue

                # 2. Execute Step
                should_continue = self._execute_step(node_id, pulse_stack, trigger_port, self.flow)
                if not should_continue:
                    # ReturnNode barrier or another terminal condition
                    continue
            logger.info("Execution finished.")
            
            # [LOCKBOX] Final Aggregation: Auto-Flush all remaining stashed returns
            with self._lock:
                if self.deferred_returns:
                    parent_id = self.bridge.get("_AXON_PARENT_NODE_ID")
                    return_key = f"SUBGRAPH_RETURN_{parent_id}" if parent_id else "SUBGRAPH_RETURN"
                    
                    aggregated_payload = {}
                    # Combine all stashed returns from all scopes
                    for scope_id in list(self.deferred_returns.keys()):
                        payload = self.deferred_returns.pop(scope_id)
                        if payload:
                            aggregated_payload.update(payload)
                    
                    if aggregated_payload:
                        # Merge with any existing returns (standard behavior)
                        existing = self.bridge.get(return_key) or {}
                        if isinstance(existing, dict):
                            existing.update(aggregated_payload)
                            self.bridge.set(return_key, existing, "Engine_Lockbox_FinalAggregation")
                        else:
                            self.bridge.set(return_key, aggregated_payload, "Engine_Lockbox_FinalAggregation")
                        logger.info(f"Final Aggregation of stashed returns flushed to {return_key}")

            # Notify Parent
            if self.parent_bridge and self.parent_node_id:
                self.parent_bridge.bubble_set(f"{self.parent_node_id}_SubGraphActivity", False, "ChildEngine")
                print(f"[AXON_SUBGRAPH_FINISHED] {self.parent_node_id}")

        finally:
            with self._lock:
                # Cleanup visual states from bridge before stopping services
                self._clear_all_visuals()
                
                # [FIX] Close dispatcher worker pools before stopping node services
                # to prevent race conditions during OS shutdown.
                if self.dispatcher:
                     self.dispatcher.shutdown()
                
                # Only root thread should shutdown services if it's truly the end
                self.stop_all_services()
            
            # If root thread, shutdown dispatcher
            pass

    def _clear_all_visuals(self):
        """Resets all visual activity highlights and minimap dots in the bridge."""
        if not self.bridge: return
        
        logger.info("Clearing session visual activity from bridge...")
        clear_data = {}
        
        # 1. Reset Node Highlights and Activity
        for node_id in self.nodes.keys():
            clear_data[f"{node_id}_ActivePorts"] = None
            clear_data[f"{node_id}_Condition"] = None
            clear_data[f"{node_id}_ActiveWires"] = None
            # SubGraph node activity bubble
            clear_data[f"{node_id}_SubGraphActivity"] = False
            
        # 2. Reset System Stats that cause UI "blinking" or persistence
        clear_data["_AXON_BREAKPOINT_ACTIVE"] = False
        
        # 3. Apply Batch Update
        try:
            self.bridge.set_batch(clear_data, source_node_id="Engine_Cleanup")
            
            # 4. Bubble Up if child engine
            if self.parent_bridge and self.parent_node_id:
                self.parent_bridge.bubble_set(f"{self.parent_node_id}_SubGraphActivity", False, "Engine_Cleanup")
        except Exception as e:
            logger.debug(f"Visual cleanup failed (likely bridge shutdown): {e}")

    def _run_branch(self, start_node_id, initial_stack, trigger_port, priority, delay):
        """
        Isolated execution for a parallel branch.
        Uses its own FlowController but shares the bridge and dispatcher.
        """
        logger.info(f"Branch Started: {start_node_id} (Priority: {priority})")
        
        # 1. Isolated Flow Controller
        # We don't push start_node_id in __init__ because we want to pass custom prio/delay
        branch_flow = FlowController(None, initial_stack=initial_stack, trace=self.trace)
        branch_flow.queue = [] # Clear the default ROOT push if it happened (it shouldn't if None is passed)
        branch_flow.push(start_node_id, initial_stack, trigger_port, priority=priority, delay=delay)
        
        # 2. Scope Safety: Clone the stack to prevent mutation interference
        # context_stack = list(initial_stack) # Not needed here, pulse_stack is passed to _execute_step
        
        # 3. Mini execution loop
        try:
            while branch_flow.has_next():
                # Check for Global Stop Signal
                if self._check_stop_signal(): return

                # Check for yield
                if self.bridge.get("_AXON_YIELD"):
                    logger.info(f"Branch {start_node_id} yielding.")
                    return

                # Get Next Node
                node_id, pulse_stack, t_port = branch_flow.pop()
                if node_id is None:
                    # Still check scope completions during branch waits!
                    self._check_scope_terminations()
                    time.sleep(0.01)
                    continue

                # Execute Cycle
                should_continue = self._execute_step(node_id, pulse_stack, t_port, branch_flow)
                if not should_continue:
                    return # Thread terminates
        finally:
            logger.info(f"Branch Thread Finished: {start_node_id}")
    def _check_cancellation(self, context_stack, pulse_stack, node_name):
        """[PIPELINE] Checks if any scope in the stack is marked as canceled."""
        # Iterate through linked-list stack
        curr = context_stack
        while curr:
            scope_id = curr[0]
            if self.bridge.get(f"AXONPULSE_CANCEL_SCOPE_{scope_id}"):
                logger.info(f"Cancellation: Dropping pulse for {node_name} (Scope {scope_id} terminated)")
                self._decrement_scope_counts(pulse_stack)
                self._check_scope_terminations()
                return True
            curr = curr[1] # Move to parent tuple
        return False

    def _handle_return_barrier(self, node, node_id, context_stack, trigger_port, pulse_stack):
        """[PIPELINE] Handles return node logic and branch termination."""
        ntype = getattr(node, "node_type", "")
        if ntype != "Return Node":
            return True
            
        active_scope = context_stack[0] if context_stack else "ROOT" # Get the top of the immutable stack
        is_loop_scope = str(active_scope).startswith("LO_")
        
        if not is_loop_scope:
            return_data = self._gather_inputs(node_id, trigger_port)
            if return_data:
                reserved = ["Flow", "Exec", "In", "_trigger", "_bridge", "_engine", "_context_stack", "_context_pulse"]
                blocked_keywords = ["color", "additional", "schema", "label", "context", "provider"]
                
                payload = {}
                for k, v in return_data.items():
                    if k in reserved: continue
                    if k.startswith("_AXON_"):
                        payload[k] = v
                        continue
                    pn_lower = k.lower()
                    if any(kw in pn_lower for kw in blocked_keywords): continue
                    payload[k] = v
                
                with self._lock:
                    if active_scope not in self.deferred_returns:
                        self.deferred_returns[active_scope] = {}
                    self.deferred_returns[active_scope].update(payload)
                    label = node.name if node.name != "Return Node" else "Flow"
                    self.deferred_returns[active_scope]["__RETURN_NODE_LABEL__"] = label
                    logger.info(f"Stashed return payload and label '{label}' from {node_id} in {active_scope} lockbox.")

        with self._lock:
            other_pulses = self.scope_pulse_counts.get(active_scope, 0)
            
        if other_pulses > 1:
            logger.info(f"Terminating parallel branch at ReturnNode. (Other pulses in {active_scope}: {other_pulses})")
            self._decrement_scope_counts(pulse_stack)
            self._check_scope_terminations()
            return False 
            
        return True

    def _resolve_inputs(self, node, node_id, trigger_port, context_stack, pulse_stack, flow_controller):
        """[PIPELINE] Validates provider context and gathers node inputs."""
        try:
            self._validate_provider_context(node, context_stack)
        except RuntimeError as e:
            logger.error(f"Provider Validation Error in {node.name}: {e}")
            print(f"[NODE_ERROR] {node_id} | {e}", flush=True)
            
            handler_info = self.context_manager.handle_error(e, node, context_stack, self.wires)
            if handler_info:
                _, parent_stack, catch_wires = handler_info[:3]
                for w in catch_wires:
                    flow_controller.push(w["to_node"], parent_stack, w["to_port"])
                    self._increment_scope_count(parent_stack, 1)
            else:
                self._handle_panic(e, node, context_stack, None, inputs=None)
            
            self._decrement_scope_counts(pulse_stack)
            return None 

        node_inputs = self._gather_inputs(node_id, trigger_port)
        if node_inputs is None:
            logger.warning(f"Skipping {node.name} due to Validation Failure.")
            local_error_wired = any(w["from_node"] == node_id and w["from_port"] in ["Error Flow", "Error", "Panic"] for w in self.wires)
            if local_error_wired:
                triggered = flow_controller.route_outputs(node_id, self.wires, self.bridge, context_stack, headless=self.headless)
                self._increment_scope_count(context_stack, sum(triggered.values()))
            else:
                error = ValueError(f"Validation Failed in {node.name}")
                self._handle_panic(error, node, context_stack, None, inputs=None)
            
            self._decrement_scope_counts(pulse_stack)
            return None 
            
        return node_inputs

    def _dispatch_task(self, node, node_id, node_inputs, context_stack, pulse_stack, flow_controller):
        """[PIPELINE] Dispatches the node task and waits for completion."""
        if self.trace and not self.headless: print(f"[NODE_START] {node_id}", flush=True)
        self.bridge.bubble_set(f"{node_id}_ActivePorts", None, "Engine_Sanitize")
        self.bridge.bubble_set(f"{node_id}_Condition", None, "Engine_Sanitize")

        logger.info(f"Executing {node.name} (Context: {self.context_manager.get_stack_depth(context_stack)})...")
        if self.parent_bridge and self.parent_node_id:
            self.parent_bridge.bubble_set(f"{self.parent_node_id}_SubGraphActivity", True, "ChildEngine")
            print(f"[AXON_SUBGRAPH_ACTIVITY] {self.parent_node_id}")

        node_inputs["_context_stack"] = context_stack
        
        try:
            result_future = self.dispatcher.dispatch(node, node_inputs, context_stack)
            while not result_future.done():
                if self._check_hot_reload(): self.hot_reload_graph()
                if self._check_stop_signal():
                    logger.info(f"Stop signal received while waiting for {node.name}. Pulse dropped.")
                    self._decrement_scope_counts(pulse_stack)
                    return ("STOP", None)
                self._handle_controls()
                time.sleep(0.01)

            exec_result = result_future.wait()
            self.bridge.pin_all()
            if self.trace and not self.headless: print(f"[NODE_STOP] {node_id}", flush=True)
            return ("CONTINUE", exec_result)
        except Exception as e:
            handler_info = self.context_manager.handle_error(e, node, context_stack, self.wires)
            if handler_info:
                _, parent_stack, catch_wires = handler_info[:3]
                self._auto_cleanup_scopes(context_stack, parent_stack)
                for w in catch_wires:
                    flow_controller.push(w["to_node"], parent_stack, w["to_port"])
                    self._increment_scope_count(parent_stack, 1)
            else:
                self._handle_panic(e, node, context_stack, None, inputs=node_inputs)
            
            self._decrement_scope_counts(pulse_stack)
            return ("ERROR", None)

    def _route_signals(self, node, node_id, exec_result, context_stack, pulse_stack, trigger_port, flow_controller):
        """[PIPELINE] Handles wireless signals, yield logic, and output routing."""
        if exec_result is not None: 
            self.bridge.bubble_set(f"{node_id}_Condition", exec_result, "Engine_Sync", scope_id=self.bridge.default_scope)
        self._handle_wireless(node, context_stack)

        cond_result = exec_result 
        node_priority = self.bridge.get(f"{node_id}_Priority")
        current_prio = int(node_priority) if node_priority is not None else 0

        is_provider = hasattr(node, "register_provider_context")
        provider_type = node.register_provider_context() if is_provider else None
        is_delayable_provider = is_provider and provider_type != "Flow Provider"
        prov_wired = any(w["from_port"] == "Provider Flow" for w in self.wires if w["from_node"] == node_id)
        completion_ports = ["Done"]

        stack_overrides = {}
        if is_delayable_provider and prov_wired:
            # Push node_id onto the immutable stack
            stack_overrides["Provider Flow"] = (node_id, context_stack)
            with self._lock:
                if node_id not in self.scope_pulse_counts: self.scope_pulse_counts[node_id] = 0
        
        user_overrides = self.bridge.get(f"{node_id}_StackOverrides")
        if isinstance(user_overrides, dict): stack_overrides.update(user_overrides)

        delay_ms = 0
        if isinstance(cond_result, tuple) and len(cond_result) >= 2 and cond_result[0] == "_YSWAIT":
            delay_ms = cond_result[1]
            should_pulse = len(cond_result) > 2 and bool(cond_result[2])
            if should_pulse: print(f"[NODE_WAITING_PULSE] {node_id} | {delay_ms}", flush=True)
            else: print(f"[NODE_WAITING_START] {node_id} | {delay_ms}", flush=True)

        triggered = flow_controller.route_outputs(
            node_id, self.wires, self.bridge, context_stack,
            headless=self.headless, trace=self.trace,
            priority=current_prio, delay=delay_ms,
            stack_override_map=stack_overrides,
            port_exclude=completion_ports if is_delayable_provider and prov_wired else None,
            push_directly=False
        )

        if triggered:
            primary = triggered[0]
            flow_controller._push_flow_intent(primary, self.headless, self.trace)
            self._increment_scope_count(primary["stack"], 1)
            for i in range(1, len(triggered)):
                bp = triggered[i]
                self._increment_scope_count(bp["stack"], 1)
                threading.Thread(
                    target=self._run_branch,
                    args=(bp["to_node"], bp["stack"], bp["to_port"], bp["priority"], bp["delay"]),
                    daemon=True
                ).start()

        if is_delayable_provider and prov_wired:
            sub_count = sum(1 for p in triggered if p["from_port"] == "Provider Flow")
            if sub_count > 0:
                with self._lock: self.pending_terminations[node_id] = (context_stack, current_prio, delay_ms)
            else:
                triggered_comp = flow_controller.route_outputs(
                    node_id, self.wires, self.bridge, context_stack,
                    port_include=completion_ports, priority=current_prio, delay=delay_ms,
                    headless=self.headless, trace=self.trace,
                    force_trigger=False, push_directly=True
                )
                self._increment_scope_count(context_stack, len(triggered_comp))

        # Final cleanup for this pulse
        self._decrement_scope_counts(pulse_stack)
        self._check_scope_terminations()
        
        if node.is_service and node_id not in self.service_registry:
            logger.info(f"Persistent Service Registered: {node.name}")
            self.service_registry[node_id] = node
            self.bridge.bubble_set(f"{node_id}_IsServiceRunning", True, "Engine")
            print(f"[SERVICE_START] {node_id}")

        return True

    def _execute_step(self, node_id, pulse_stack, trigger_port, flow_controller):
        """
        Executes a single node pulse cycle using the refactored pipeline.
        Thread-safe and shared between main thread and parallel branches.
        Returns: True if iteration should continue, False if thread should terminate.
        """
        # 1. Pipeline: Context and Node Lookup
        # NO CLONING! Immutable stack shared by reference.
        context_stack = pulse_stack 
        node = self.nodes.get(node_id)
        node_name = node.name if node else node_id

        # 2. Pipeline: Cancellation
        if self._check_cancellation(context_stack, pulse_stack, node_name):
            return False

        if not node:
            logger.error(f"Node {node_id} not found!")
            self._decrement_scope_counts(pulse_stack)
            return True

        # 3. Pipeline: Return Barrier
        if not self._handle_return_barrier(node, node_id, context_stack, trigger_port, pulse_stack):
            return False

        # 4. Pipeline: Controls
        self._handle_controls()
        if not self.headless and self.bridge.get("_SYSTEM_STEP_BACK"):
            if threading.current_thread() == threading.main_thread():
                self.bridge.set("_SYSTEM_STEP_BACK", False, "Engine")
                self._step_back()
                return True
            else:
                while self.bridge.get("_SYSTEM_STEP_BACK"): time.sleep(0.1)

        # 5. Pipeline: Resolve Inputs & Validation
        node_inputs = self._resolve_inputs(node, node_id, trigger_port, context_stack, pulse_stack, flow_controller)
        if node_inputs is None:
            return True

        # 6. Pipeline: Update Context Stack
        context_stack = self.context_manager.update_stack(node, context_stack, trigger_port)

        # 7. Pipeline: Dispatch & Execute
        status, exec_result = self._dispatch_task(node, node_id, node_inputs, context_stack, pulse_stack, flow_controller)
        
        # [NEW] Auto-Register background services for cleanup
        if getattr(node, "is_service", False) and node_id not in self.service_registry:
            self.service_registry[node_id] = node
            logger.info(f"Registered background service for cleanup: {node.name} ({node_id})")

        if status == "STOP":
            return False
        if status == "ERROR":
            return True

        # 8. Pipeline: Routing & Signals
        return self._route_signals(node, node_id, exec_result, context_stack, pulse_stack, trigger_port, flow_controller)


    def _decrement_scope_counts(self, stack):
        """Helper to safely decrement pulse hierarchy."""
        with self._lock:
            if "ROOT" in self.scope_pulse_counts:
                self.scope_pulse_counts["ROOT"] -= 1
            
            # Iterate through linked-list stack
            curr = stack
            while curr:
                s_id = curr[0]
                if s_id in self.scope_pulse_counts:
                    self.scope_pulse_counts[s_id] -= 1
                    if self.scope_pulse_counts[s_id] <= 0:
                        del self.scope_pulse_counts[s_id]
                curr = curr[1] # Move to parent tuple

    def _handle_wireless(self, node, context_stack):
        node_type_name = type(node).__name__
        if "SenderNode" in node_type_name:
            tag = node.properties.get("tag", "")
            count = self.flow.route_wireless(tag, self.nodes, context_stack, headless=self.headless, trace=self.trace)
            self._increment_scope_count(context_stack, count)

    def _handle_controls(self):
        if self.headless:
            return
            
        # 1. Immediate Settings Sync
        self._sync_settings()
        
        # 2. Variable Delay (Sliced to remain responsive)
        if self.delay > 0:
            start_wait = time.time()
            while (time.time() - start_wait) < self.delay:
                # Check for stop signal aggressively
                if self._check_stop_signal():
                    return
                
                # Periodically re-sync settings (speed/trace) during long sleeps
                now = time.time()
                if now - self._last_control_check > self._control_interval:
                    self._sync_settings()
                    # If speed was increased (delay decreased) and we've already waited enough, break
                    if self.delay <= (now - start_wait):
                        break

                remaining = self.delay - (time.time() - start_wait)
                if remaining <= 0: break
                time.sleep(min(0.05, remaining)) # Small slices for maximum responsiveness
        
        # 3. Pause Handling (File / Bridge)
        is_file_paused = False
        if self.pause_file and os.path.exists(self.pause_file):
            is_file_paused = True
            
        is_bridge_paused = self.bridge.get("_AXON_BREAKPOINT_ACTIVE") if self.bridge else False
        
        if is_file_paused or is_bridge_paused:
            logger.info("Execution paused (Breakpoint/File)...")
            
            # Record state for hovered data (snapshot current wires)
            if is_bridge_paused and hasattr(self, 'flow') and hasattr(self.flow, '_last_triggered_wire'):
                 # We can pass the full context/inputs if we wanted, but for now we signal we are paused
                 pass
            
            while True:
                # Check for stop/speed signals while paused
                self._sync_settings()
                if self._check_stop_signal():
                    return
                
                # Check for Resume/Step from UI
                if self.bridge:
                    if self.bridge.get("_AXON_BREAKPOINT_RESUME"):
                        self.bridge.set("_AXON_BREAKPOINT_ACTIVE", False, "Engine")
                        self.bridge.set("_AXON_BREAKPOINT_RESUME", False, "Engine")
                        break
                        
                    if self.bridge.get("_AXON_BREAKPOINT_STEP"):
                        self.bridge.set("_AXON_BREAKPOINT_STEP", False, "Engine")
                        # We don't clear ACTIVE here, let the next node hit clear it or re-trigger it.
                        # Wait, Step Over means we run ONE node, so we DO clear ACTIVE and let the engine pulse.
                        # The UI might set a "step mode" flag, but simple 'step over' clears the pause for this pulse.
                        self.bridge.set("_AXON_BREAKPOINT_ACTIVE", False, "Engine")
                        break
                
                # Check file removal
                if self.pause_file and not os.path.exists(self.pause_file) and not is_bridge_paused:
                    break
                    
                time.sleep(0.1)
                
            logger.info("Execution resumed.")

        # 4. [NEW] Live Swapping Check
        if self.bridge.get("_SYSTEM_LIVE_SWAP_DATA"):
            patch_data = self.bridge.get("_SYSTEM_LIVE_SWAP_DATA")
            if patch_data:
                logger.info("[LiveSwap] Signal detected. Applying patch at pulse barrier...")
                if self.apply_live_swap(patch_data):
                    # Clear signal after success
                    self.bridge.set("_SYSTEM_LIVE_SWAP_DATA", None, "Engine")

    def _sync_settings(self):
        """Polls disk and bridge for runtime configuration changes."""
        now = time.time()
        if now - self._last_control_check < self._control_interval:
            # Check Stop Signal ONLY even if interval not passed (Critical)
            return

        self._last_control_check = now
        
        # Speed Control
        if self.speed_file and os.path.exists(self.speed_file):
            try:
                with open(self.speed_file, 'r') as f:
                    val = f.read().strip()
                    if val: self.delay = float(val)
            except: pass
            
        # Trace Flags
        if self.parent_bridge:
            trace_enabled = self.parent_bridge.get("_SYSTEM_TRACE_ENABLED", default=True)
            trace_subgraphs = self.parent_bridge.get("_SYSTEM_TRACE_SUBGRAPHS", default=True)
            self.trace = trace_enabled and trace_subgraphs
            
            # Parent Stop Propagation
            if self.parent_bridge.get("_SYSTEM_STOP"):
                self.bridge.set("_SYSTEM_STOP", True, "Parent_Stop_Propagation")
        else:
            trace_enabled = self.bridge.get("_SYSTEM_TRACE_ENABLED", default=True)
            self.trace = trace_enabled

    def _check_stop_signal(self):
        """Checks for stop signals from internal events, bridge, or file system."""
        # 0. Internal Event Check
        if hasattr(self, "_stop_event") and self._stop_event.is_set():
            return True

        # 1. Bridge Check (Own)
        try:
            if self.bridge.get("_SYSTEM_STOP"):
                return True
        except (BrokenPipeError, EOFError, ConnectionResetError):
            logger.warning("Bridge connection lost. Stopping engine.")
            return True
        except Exception as e:
            if "pipe is being closed" in str(e).lower():
                return True

        # 2. Parent Bridge Check (SubGraph engines inherit parent stop)
        if self.parent_bridge:
            try:
                if self.parent_bridge.get("_SYSTEM_STOP"):
                    return True
            except:
                return True

        # 3. File Check
        if self.stop_file and os.path.exists(self.stop_file):
            return True
        
        return False

    def _validate_provider_context(self, node, context_stack):
        """
        Checks if the node's required providers are present in the current stack.
        Raises RuntimeError if missing.
        """
        required = getattr(node, "required_providers", [])
        if not required: return

        # Get all provider types active in the stack
        active_providers = set()
        curr = context_stack
        while curr:
            ctx_item = curr[0]
            if isinstance(ctx_item, str):
                stack_node_id = ctx_item
                stack_node = self.nodes.get(stack_node_id)
                if stack_node:
                     if hasattr(stack_node, "register_provider_context"):
                         active_providers.add(stack_node.register_provider_context())
                     elif "ProviderNode" in type(stack_node).__name__:
                         active_providers.add("Generic")
            elif isinstance(ctx_item, dict):
                 if ctx_item.get("type") == "provider":
                    active_providers.add(ctx_item.get("provider_type"))
            curr = curr[1] # Move to parent tuple
        
        # Check if ALL required are present
        missing = []
        for req in required:
            if req not in active_providers:
                missing.append(req)
        
        if missing:
            # Check for Fallback (e.g. explicitly connected handle)
            # Some nodes can work without provider scope if input handle is given.
            # But 'required_providers' is usually for strict scope requirements.
            # If the node allows standalone op, it should NOT set required_providers.
            raise RuntimeError(f"Missing Required Provider(s): {', '.join(missing)}")

    def _increment_scope_count(self, stack, count):
        """Helper to safely increment pulse count for all scopes in the stack hierarchy."""
        if count <= 0: return
        
        with self._lock:
            # Always increment ROOT
            if "ROOT" not in self.scope_pulse_counts:
                self.scope_pulse_counts["ROOT"] = 0
            self.scope_pulse_counts["ROOT"] += count
            
            # Increment named scopes in stack
            curr = stack
            while curr:
                s_id = curr[0]
                if s_id not in self.scope_pulse_counts:
                    self.scope_pulse_counts[s_id] = 0
                self.scope_pulse_counts[s_id] += count
                curr = curr[1] # Move to parent tuple
    def _auto_cleanup_scopes(self, current_stack, target_stack):
        """
        Identifies scopes dropped during error handling and triggers cleanup
        on any Providers that were active in those scopes.
        """
        # Walking up current_stack until we find target_stack (the catch handler context)
        dropped_ids = []
        curr = current_stack
        while curr and curr is not target_stack:
            dropped_ids.append(curr[0])
            curr = curr[1]
        
        # Cleanup in order (Innermost to Outermost corresponds to traversal order)
        for nid in dropped_ids:
             node = self.nodes.get(nid)
             if node and hasattr(node, "cleanup_provider_context"):
                 # [SINGLETON CHECK]
                 is_singleton = node.properties.get("Singleton Scope", False)
                 if is_singleton:
                     continue
                     
                 # Force Cleanup
                 try:
                     node.cleanup_provider_context()
                 except Exception as e:
                     logger.warning(f"Failed to cleanup provider {node.name}: {e}")


    def _check_scope_terminations(self):
        """
        Deep check for any scopes that have zero pulses remaining.
        Triggers their final 'Flow' output.
        """
        with self._lock:
            if not self.scope_pulse_counts:
                return

            changed = True
            while changed:
                changed = False
                finished_scopes = []
                for s, count in self.scope_pulse_counts.items():
                    if s == "ROOT": continue
                    
                    # In a multi-threaded model, we rely purely on scope_pulse_counts.
                    # The current_pulse_stack logic for the single thread is no longer viable
                    # across threads, so we assume if count is 0, no thread is handling it.
                    if count <= 0:
                        finished_scopes.append(s)
                
                for scope_id in finished_scopes:
                    if self.scope_pulse_counts.get(scope_id, 1) > 0:
                        continue

                    if scope_id in self.pending_terminations:
                        stack, prio, delay = self.pending_terminations[scope_id]
                        completion_ports = ["Done"]
                        
                        logger.info(f"Provider Scope {scope_id} finished. Resuming completion flow.")
                        
                        # Trigger the completion ports
                        # We use the isolated FlowController of the caller if possible?
                        # No, we can just use self.flow (Master Flow) or a dummy.
                        # Actually, self.flow is safer for convergence back to master.
                        triggered_list = self.flow.route_outputs(
                            scope_id, self.wires, self.bridge, stack,
                            port_include=completion_ports,
                            priority=prio, delay=delay,
                            headless=self.headless, trace=self.trace,
                            force_trigger=True, push_directly=True
                        )
                        
                        # Increment the count of the parent scope for any pulses created
                        # Note: _increment_scope_count already has a lock, but we are inside one.
                        # We should either use a reentrant lock or manual increment here.
                        # Let's assume we need manual increment to avoid deadlocks if Lock is not reentrant.
                        # threading.Lock is NOT reentrant. RLock is.
                        # Let's change self._lock to RLock.
                        
                        # [Refactor] Using RLock below for safety.
                        self._increment_scope_count_locked(stack, len(triggered_list))
                        
                        del self.pending_terminations[scope_id]
                    
                    if scope_id in self.pending_terminations:
                        # ... provider logic ...
                        pass # (kept same as before)

                    # [LOCKBOX] Flush stashed returns for this scope
                    if scope_id in self.deferred_returns:
                        payload = self.deferred_returns.pop(scope_id)
                        if payload:
                            parent_id = self.parent_node_id
                            return_key = f"SUBGRAPH_RETURN_{parent_id}" if parent_id else "SUBGRAPH_RETURN"
                            logger.info(f"Lockbox Flush: Using return_key {return_key} for scope {scope_id} (Parent ID: {parent_id})")
                            logger.info(f"Lockbox Flush: Payload keys: {list(payload.keys())}")
                            
                            # Merge with existing safely (Scrub stale pollution)
                            existing = self.bridge.get(return_key) or {}
                            if isinstance(existing, dict):
                                # Scrub existing data before merge
                                reserved = ["Flow", "Exec", "In", "_trigger", "_bridge", "_engine", "_context_stack", "_context_pulse"]
                                blocked_keywords = ["color", "additional", "schema", "label", "context", "provider"]
                                
                                to_delete = [k for k in existing if any(kw in k.lower() for kw in blocked_keywords) or k in reserved]
                                for k in to_delete: del existing[k]
                                
                                existing.update(payload)
                                self.bridge.set(return_key, existing, "Engine_Lockbox_ScopeFlush")
                            else:
                                self.bridge.set(return_key, payload, "Engine_Lockbox_ScopeFlush")
                            logger.info(f"Auto-flushed stashed returns for scope {scope_id} to {return_key}")

                    if scope_id in self.scope_pulse_counts:
                        if self.scope_pulse_counts[scope_id] <= 0:
                            del self.scope_pulse_counts[scope_id]
                            changed = True

    def _increment_scope_count_locked(self, stack, count):
        """Variant of increment that assumes lock is already held."""
        if count <= 0: return
        self.scope_pulse_counts["ROOT"] = self.scope_pulse_counts.get("ROOT", 0) + count
        
        curr = stack
        while curr:
            s_id = curr[0]
            self.scope_pulse_counts[s_id] = self.scope_pulse_counts.get(s_id, 0) + count
            curr = curr[1]
