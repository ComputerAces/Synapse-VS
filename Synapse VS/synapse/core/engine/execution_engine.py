import time
import os
from synapse.utils.logger import setup_logger
from synapse.core.flow_controller import FlowController
from synapse.core.context_manager import ContextManager
from synapse.core.node_dispatcher import NodeDispatcher
from synapse.core.port_registry import PortRegistry

from .data_io import DataMixin
from .state_management import StateMixin
from .services import ServiceMixin
from .debugging import DebugMixin

logger = setup_logger("SynapseEngine")

class ExecutionEngine(DataMixin, StateMixin, ServiceMixin, DebugMixin):
    """
    Manages the execution flow of the Synapse graph.
    Refactored to use Hybrid Architecture (FlowController, ContextManager, NodeDispatcher)
    and Modular Mixins.
    """
    def __init__(self, bridge, headless=False, delay=0.0, pause_file=None, speed_file=None, stop_file=None, trace=True, parent_bridge=None, parent_node_id=None, source_file=None, initial_context=None):
        self.bridge = bridge
        self.parent_bridge = parent_bridge
        self.parent_node_id = parent_node_id
        self.initial_context = initial_context or []
        self.nodes = {} 
        self.wires = [] 
        self.headless = headless
        self.delay = delay
        self.pause_file = pause_file if pause_file else "synapse.pause"
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
        self.bridge.set("_OS_TYPE", platform.system(), "Engine")
        
        # [NEW] Set Graph Prefix (Scope ID) for Bridge
        if self.source_file:
            graph_name = os.path.splitext(os.path.basename(self.source_file))[0]
            # Sanitize name for bridge keys
            safe_name = graph_name.replace(" ", "_").replace(":", "_").replace("-", "_")
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
        
        # [NEW] Runaway Train Guard
        self._max_pulses_per_scope = 10000
        self._scope_execution_totals = {} # {scope_id: total_processed}


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
        """Reloads the graph from disk and patches the running engine state."""
        if not self.source_file or not os.path.exists(self.source_file):
            return

        logger.info(f"Hot Reloading Graph: {self.source_file}")
        try:
            import json
            from synapse.core.loader import load_graph_data
            
            with open(self.source_file, 'r') as f:
                data = json.load(f)
            
            # 1. Capture current node ids for deletion tracking
            old_node_ids = set(self.nodes.keys())
            new_node_data = {n['id']: n for n in data.get("nodes", [])}
            new_node_ids = set(new_node_data.keys())
            
            # 2. Add New Nodes / Update Existing
            # Temporarily bypass the engine's connect/register to manually patch
            load_graph_data(data, self.bridge, self)
            
            # 3. Handle Deletions
            deleted_ids = old_node_ids - new_node_ids
            for d_id in deleted_ids:
                node = self.nodes.get(d_id)
                if node:
                    if hasattr(node, 'terminate'):
                        try:
                            node.terminate()
                        except: pass
                    self.nodes.pop(d_id, None)
                    self.service_registry.pop(d_id, None)
                    logger.info(f"Hot Reload: Removed node {d_id}")

            # 4. Sync Wires (Full replace is easiest for flow)
            self.wires = data.get("wires", [])
            # Re-initialize wires in flow controller
            self.flow.wires = self.wires
            
            # [TRACE] Notify UI of reload if tracing enabled
            if self.trace:
                print(f"[HOT_RELOAD] {self.source_file}", flush=True)
            
            logger.info("Hot Reload Complete. Changes will take effect on next node pulse.")
            
        except Exception as e:
            logger.error(f"Hot Reload Failed: {e}")

    def run(self, start_node_id, initial_stack=None):
        """
        Executes the graph using components.
        """
        logger.info("Starting Pulse...")
        
        # Use provided stack or engine's initial context
        pulse_stack = initial_stack if initial_stack is not None else self.initial_context

        # [PRODUCTION MODE VALIDATION]
        start_count = 0
        return_count = 0
        for node_id, node in self.nodes.items():
            node_type = type(node).__name__
            if "StartNode" in node_type or node_type == "Start Node":
                start_count += 1
            elif hasattr(node, 'node_type') and "Start" in str(getattr(node, 'node_type', '')):
                start_count += 1
            if "ReturnNode" in node_type or "Return" in node_type:
                return_count += 1
        
        if start_count == 0:
            raise ValueError("[Production Mode] Graph must have at least one Start Node.")
        if start_count > 1:
            logger.warning(f"[Production Mode] Graph has {start_count} Start Nodes. Using provided start_node_id.")
        if return_count == 0:
            logger.warning("[Production Mode] Graph has no Return Node. Execution may not terminate properly.")
        
        # [CONTEXT INITIALIZATION]
        # If this is a child engine (subgraph), inherit parent stack.
        # Otherwise start with an empty stack.
        initial_stack = []
        if self.parent_bridge and self.parent_node_id:
            # SubGraph inheritance: The parent node might have an active stack
            # We can pull it from the bridge if the parent pushed it there, 
            # but usually the run() caller should pass it if known.
            # For now, we allow the Bridge to expose a 'last pulse stack' 
            # but cleaner is to assume a global default or empty for now.
            pass

        self.flow = FlowController(start_node_id, initial_stack=initial_stack, trace=self.trace)
        
        # Initialize counts
        self.scope_pulse_counts = {"ROOT": 1}
        self.pending_terminations = {}

        
        # Pulse generating UUID
        import uuid
        run_id = str(uuid.uuid4())[:8]
        self.bridge.set("_SYSTEM_RUN_ID", run_id, "Engine")
        
        try:
            while self.flow.has_next():
                # Check for Global Stop Signal
                if self._check_stop_signal():
                    logger.info("Stop signal detected. Terminating execution.")
                    return

                # Check for Yield Signal
                if self.bridge.get("_SYNP_YIELD"):
                    logger.info("Yield detected. Returning control.")
                    self.bridge.set("_SYNP_YIELD", False, "Engine")
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
                    if self._check_hot_reload():
                        self.hot_reload_graph()
                    self._last_reload_check = now

                # 1. Get Next Node
                current_node_id, pulse_stack, trigger_port = self.flow.pop()
                self.current_pulse_stack = pulse_stack
            
                # [NEW] Runaway Train Guard Detection
                active_scope = pulse_stack[-1] if pulse_stack else "ROOT"
                self._scope_execution_totals[active_scope] = self._scope_execution_totals.get(active_scope, 0) + 1
                if self._scope_execution_totals[active_scope] > self._max_pulses_per_scope:
                    raise RuntimeError(f"RUNAWAY TRAIN: Scope '{active_scope}' exceeded {self._max_pulses_per_scope} pulses without yielding.")

                # [FIX] Handle Delayed Queue Waiting
                if current_node_id is None:
                    # Flow has pending items (delayed) but none are ready.
                    # [NEW] still check scope finishes during waits
                    self._check_scope_terminations()
                    time.sleep(0.01)
                    continue

                # Decrement popped hierarchy
                if "ROOT" in self.scope_pulse_counts:
                    self.scope_pulse_counts["ROOT"] -= 1
                
                if pulse_stack:
                    for s_id in pulse_stack:
                        if s_id in self.scope_pulse_counts:
                            self.scope_pulse_counts[s_id] -= 1

                # Context stack priority: Pulse Stack > Engine Default
                context_stack = pulse_stack if pulse_stack is not None else []
                
                node = self.nodes.get(current_node_id)
                if not node:
                    logger.error(f"Node {current_node_id} not found!")
                    continue

                # [BARRIER] Pulse Synchronization for Return Nodes
                # If this is a Return Node, but there are other flow pulses pending in the queue,
                # defer this return until they finish. This ensures parallel branches complete.
                node_type = type(node).__name__
                is_return = "ReturnNode" in node_type or "Return" in node_type
                if is_return:
                    has_other_pulses = False
                    
                    # 1. Check Main Queue
                    for _, _, q_node_id, q_stack, _ in self.flow.queue:
                        # Only wait for pulses in the SAME or NESTED scope
                        if q_stack[:len(context_stack)] == context_stack:
                            q_node = self.nodes.get(q_node_id)
                            if q_node:
                                q_node_type = type(q_node).__name__
                                if not ("ReturnNode" in q_node_type or "Return" in q_node_type):
                                    has_other_pulses = True
                                    break
                    
                    # 2. Check Delayed Queue (e.g. Wait nodes in same scope)
                    if not has_other_pulses:
                        for _, (_, _, q_node_id, q_stack, _) in self.flow.delayed_queue:
                            if q_stack[:len(context_stack)] == context_stack:
                                q_node = self.nodes.get(q_node_id)
                                if q_node:
                                    q_node_type = type(q_node).__name__
                                    if not ("ReturnNode" in q_node_type or "Return" in q_node_type):
                                        has_other_pulses = True
                                        break

                    if has_other_pulses:
                        # Defer Return execution
                        # [FIX] Must increment scope count when pushing back
                        self.flow.push(current_node_id, context_stack, trigger_port)
                        self._increment_scope_count(context_stack, 1)
                        self.current_pulse_stack = None
                        continue
                
                # Speed/Pause Control
                self._handle_controls()
                
                # Check Step Back AGAIN after controls (user might have stepped back while paused)
                if not self.headless and self.bridge.get("_SYSTEM_STEP_BACK"):
                    self.bridge.set("_SYSTEM_STEP_BACK", False, "Engine")
                    # We popped the node, we must restore flow to put it back
                    # Ideally we should have stepped back BEFORE pop.
                    # But if we step back here, history has the state BEFORE pop.
                    # So restoring history will put the node back in flow queue.
                    self._step_back()
                    self.current_pulse_stack = None
                    self.current_pulse_stack = None
                    continue
                
                # 2. Data Transfer (Inputs) & Validation
                # [NEW] Check Provider Dependencies
                try:
                    self._validate_provider_context(node, context_stack)
                except RuntimeError as e:
                    # Provider Check Failed
                    logger.error(f"Provider Validation Error in {node.name}: {e}")
                     # Notify UI of Error State (Red Highlight)
                    print(f"[NODE_ERROR] {current_node_id} | {e}", flush=True)
                    
                    # Handle as standard error
                    handler_info = self.context_manager.handle_error(e, node, context_stack, self.wires)
                    if handler_info:
                        handler_id, parent_stack, catch_wires = handler_info[:3]

                        for w in catch_wires:
                            self.flow.push(w["to_node"], parent_stack, w["to_port"])
                            self._increment_scope_count(parent_stack, 1)
                    else:
                        # If unhandled, we can either stop or panic. 
                        # For visual feedback, we want the node to stay red.
                        # We trigger the panic handler which might stop the engine or just log.
                        self._handle_panic(e, node, context_stack, start_node_id, inputs=None)
                    
                    self.current_pulse_stack = None
                    continue

                node_inputs = self._gather_inputs(current_node_id, trigger_port)
                
                if node_inputs is None:
                    # strict validation failed. Error Flow triggered in _gather_inputs.
                    logger.warning(f"Skipping {node.name} due to Validation Failure.")
                    
                    # Check if Local Error Flow is wired
                    local_error_wired = False
                    for w in self.wires:
                        if w["from_node"] == current_node_id and w["from_port"] in ["Error Flow", "Error", "Panic"]:
                            local_error_wired = True
                            break
                    
                    if local_error_wired:
                        # 4a. Local Route Output Flow (Error Flow only)
                        triggered = self.flow.route_outputs(
                            current_node_id, 
                            self.wires, 
                            self.bridge, 
                            context_stack,
                            headless=self.headless
                        )
                        self._increment_scope_count(context_stack, sum(triggered.values()))
                    else:
                        # 4b. Global Panic Fallback
                        error = ValueError(f"Validation Failed in {node.name}")
                        self._handle_panic(error, node, context_stack, start_node_id, inputs=node_inputs)
                        
                    self.current_pulse_stack = None
                    continue
                
                # Update Stack (Entering/Exiting Try/Catch or Provider Scopes)
                context_stack = self.context_manager.update_stack(node, context_stack, trigger_port)

                # [STEP DEBUGGING]
                skip_execution = False 
                if not self.headless:
                    step_mode = self.bridge.get("_SYSTEM_STEP_MODE")
                    if step_mode:
                        # Signal UI that we are paused at this node
                        self.bridge.set("_SYSTEM_NEXT_NODE", current_node_id, "Engine")
                        
                        # Wait for Trigger
                        while self.bridge.get("_SYSTEM_STEP_MODE"):
                            # Check Step Back in loop
                            if self.bridge.get("_SYSTEM_STEP_BACK"):
                                self.bridge.set("_SYSTEM_STEP_BACK", False, "Engine")
                                self.bridge.set("_SYSTEM_NEXT_NODE", None, "Engine")
                                # We popped context/node, so stepping back restores state before this.
                                self._step_back()
                                # We need to break to 'continue' outer loop
                                # But we can't easily jump to outer loop continue from here.
                                # Use flag or structured control
                                skip_execution = "STEP_BACK" 
                                break

                            if self.bridge.get("_SYSTEM_STEP_TRIGGER"):
                                # Consumable Trigger
                                self.bridge.set("_SYSTEM_STEP_TRIGGER", False, "Engine")
                                self.bridge.set("_SYSTEM_NEXT_NODE", None, "Engine") 
                                
                                # Check for Skip
                                if self.bridge.get("_SYSTEM_SKIP_NEXT"):
                                    skip_execution = True
                                    self.bridge.set("_SYSTEM_SKIP_NEXT", False, "Engine")
                                break
                            
                            if self._check_hot_reload():
                                self.hot_reload_graph()
                            time.sleep(0.05)
                
                if skip_execution == "STEP_BACK":
                    continue

                # 3. Execution (Trace Signals for UI)
                if self.trace and not self.headless:
                    print(f"[NODE_START] {current_node_id}", flush=True)

                # [Fix ForEach Leakage] Explicitly clear stale triggers
                self.bridge.set(f"{current_node_id}_ActivePorts", None, "Engine_Sanitize")
                self.bridge.set(f"{current_node_id}_Condition", None, "Engine_Sanitize")
                
                logger.info(f"Executing {node.name} (Context: {len(context_stack)})...")
                
                # Initialize result container
                exec_result = None
                
                try:
                    # Trigger Bubble-up
                    if self.parent_bridge and self.parent_node_id:
                        self.parent_bridge.set(f"{self.parent_node_id}_SubGraphActivity", True, "ChildEngine")
                        print(f"[SYNP_SUBGRAPH_ACTIVITY] {self.parent_node_id}")
                    
                    # Dispatch
                    if not skip_execution:
                        node.context_stack = context_stack
                        result_future = self.dispatcher.dispatch(node, node_inputs, context_stack)
                        exec_result = result_future.wait() 
                        
                        # [IPC OPTIMIZATION] Hold handles to any new SHM blocks from workers
                        self.bridge.pin_all() # Note: internally skips if not dirty
                    else:
                        logger.info(f"Skipping execution of {node.name}")
                        exec_result = None
                    
                    # Notify UI
                    if self.trace and not self.headless:
                        print(f"[NODE_STOP] {current_node_id}", flush=True)
                    
                    # Store result
                    if exec_result is not None:
                        self.bridge.set(f"{current_node_id}_Condition", exec_result, "Engine_Sync")
                    
                    # Wireless Routing
                    self._handle_wireless(node, context_stack)

                except Exception as e:
                    # Error Handling
                    handler_info = self.context_manager.handle_error(e, node, context_stack, self.wires)
                    
                    if handler_info:
                        handler_id, parent_stack, catch_wires = handler_info[:3]
                        
                        # [SAFETY NET] Auto-Cleanup Dropped Scopes
                        self._auto_cleanup_scopes(context_stack, parent_stack)
                        
                        for w in catch_wires:
                            self.flow.push(w["to_node"], parent_stack, w["to_port"])
                            self._increment_scope_count(parent_stack, 1)
                    else:
                        panic_handled = self._handle_panic(e, node, context_stack, start_node_id, inputs=node_inputs)
                        if not panic_handled:
                            raise RuntimeError(f"Unhandled graph error in '{node.name}': {e}") from e

                # [YIELD HANDLING] Check for Special Yield Signals in Result
                # Nodes can return ("_YSWAIT", ms) or ("_YSYIELD",) to pause/defer
                
                # Use local result variable instead of round-tripping to Bridge
                cond_result = exec_result 
                
                # Debug Logging
                if isinstance(cond_result, tuple) and len(cond_result) > 0 and str(cond_result[0]).startswith("_YS"):
                     logger.info(f"Yield Signal Detected: {cond_result}")

                # Check priority from node (set during execute)
                node_priority = self.bridge.get(f"{current_node_id}_Priority")
                current_prio = int(node_priority) if node_priority is not None else 0

                # 4. Route Output Flow
                # [NEW] Safe Provider Termination Logic
                is_provider = hasattr(node, "register_provider_context")
                provider_type = node.register_provider_context() if is_provider else None
                
                # We only delay termination for NON-ROOT providers (Start Node is a Root Provider)
                is_delayable_provider = is_provider and provider_type != "Flow Provider"
                
                provider_flow_wired = any(w["from_port"] == "Provider Flow" for w in self.wires if w["from_node"] == current_node_id)
                
                # Ports that shouldn't fire until Provider Flow is done
                completion_ports = ["Flow", "Out", "Done", "Success", "True", "False"]

                stack_overrides = {}
                if is_delayable_provider and provider_flow_wired:
                    stack_overrides["Provider Flow"] = context_stack + [current_node_id]
                    if current_node_id not in self.scope_pulse_counts:
                        self.scope_pulse_counts[current_node_id] = 0
                
                # Check for special signals from cond_result
                delay_ms = 0
                if isinstance(cond_result, tuple) and len(cond_result) >= 2 and cond_result[0] == "_YSWAIT":
                    delay_ms = cond_result[1]
                    # Check for Pulse Flag (Index 2)
                    should_pulse = False
                    if len(cond_result) > 2:
                        should_pulse = bool(cond_result[2])
                    
                    if should_pulse:
                        print(f"[NODE_WAITING_PULSE] {current_node_id} | {delay_ms}", flush=True)
                    else:
                        print(f"[NODE_WAITING_START] {current_node_id} | {delay_ms}", flush=True)

                # Route with exclusions if it's a sub-graph starting
                port_counts = self.flow.route_outputs(
                    current_node_id, 
                    self.wires, 
                    self.bridge, 
                    context_stack,
                    headless=self.headless,
                    trace=self.trace,
                    priority=current_prio,
                    delay=delay_ms,
                    stack_override_map=stack_overrides,
                    port_exclude=completion_ports if is_delayable_provider and provider_flow_wired else None
                )
                
                # Update pulse counts
                for port, count in port_counts.items():
                    target_stack = stack_overrides.get(port, context_stack)
                    self._increment_scope_count(target_stack, count)

                # If we delayed completion, save metadata for later
                if is_delayable_provider and provider_flow_wired:
                    sub_pulse_count = port_counts.get("Provider Flow", 0)
                    if sub_pulse_count > 0:
                        self.pending_terminations[current_node_id] = (context_stack, current_prio, delay_ms)
                    else:
                        # Sub-graph was wired but didn't fire (conditional).
                        # Fire the completion ports now!
                        triggered = self.flow.route_outputs(
                            current_node_id, self.wires, self.bridge, context_stack,
                            port_include=completion_ports,
                            priority=current_prio, delay=delay_ms,
                            headless=self.headless, trace=self.trace,
                            force_trigger=True
                        )
                        self._increment_scope_count(context_stack, sum(triggered.values()))
                
                # [Refined] Handle Scope Termination at end of step
                self._check_scope_terminations()
                self.current_pulse_stack = None

                # Handle Service Persistence
                if node.is_service:
                    if node.node_id not in self.service_registry:
                        logger.info(f"Persistent Service Registered: {node.name}")
                        self.service_registry[node.node_id] = node
                        self.bridge.set(f"{node.node_id}_IsServiceRunning", True, "Engine")
                        print(f"[SERVICE_START] {node.node_id}")
                        
            logger.info("Execution finished.")
            
            # Notify Parent
            if self.parent_bridge and self.parent_node_id:
                self.parent_bridge.set(f"{self.parent_node_id}_SubGraphActivity", False, "ChildEngine")
                print(f"[SYNP_SUBGRAPH_FINISHED] {self.parent_node_id}")

        finally:
            self.stop_all_services()
            self.dispatcher.shutdown()

    def _handle_wireless(self, node, context_stack):
        node_type_name = type(node).__name__
        if "SenderNode" in node_type_name:
            tag = node.properties.get("tag", "")
            count = self.flow.route_wireless(tag, self.nodes, context_stack, headless=self.headless, trace=self.trace)
            self._increment_scope_count(context_stack, count)

    def _handle_controls(self):
        if self.headless:
            return
            
        now = time.time()
        # Only poll disk if interval passed OR if we are currently paused (to catch resume)
        # Actually, if we are paused, we poll more frequently in the while loop anyway.
        if now - self._last_control_check > self._control_interval:
            self._last_control_check = now
            
            # Speed
            if self.speed_file and os.path.exists(self.speed_file):
                try:
                    with open(self.speed_file, 'r') as f:
                        val = f.read().strip()
                        if val: self.delay = float(val)
                except: pass
                
            # [TRACE OPTIMIZATION] Sync Trace Flags
            trace_enabled = self.bridge.get("_SYSTEM_TRACE_ENABLED", default=True)
            if self.parent_bridge:
                # [NEW] Parent Stop Propagation
                if self.parent_bridge.get("_SYSTEM_STOP"):
                    self.bridge.set("_SYSTEM_STOP", True, "Parent_Stop_Propagation")

                # We are a sub-graph, check if sub-graph tracing is enabled
                trace_subgraphs = self.bridge.get("_SYSTEM_TRACE_SUBGRAPHS", default=True)
                self.trace = trace_enabled and trace_subgraphs
            else:
                self.trace = trace_enabled
        
        if self.delay > 0:
            time.sleep(self.delay)
        
        # Pause
        if self.pause_file and os.path.exists(self.pause_file):
            logger.info("Execution paused...")
            while os.path.exists(self.pause_file):
                # We check Speed even while paused so we can resume fast/slow
                if self.speed_file and os.path.exists(self.speed_file):
                    try:
                        with open(self.speed_file, 'r') as f:
                             val = f.read().strip()
                             if val: self.delay = float(val)
                    except: pass
                
                # [NEW] still check for Stop while paused
                if self._check_stop_signal():
                    return

                time.sleep(0.1)
            logger.info("Execution resumed.")

    def _check_stop_signal(self):
        """Checks bridge and optional stop file for termination request."""
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
        for ctx_item in context_stack:
            # Stack contains IDs (Strings) or Dicts (Legacy/Future?) 
            # Currently ContextManager pushes IDs.
            if isinstance(ctx_item, str):
                stack_node_id = ctx_item
                stack_node = self.nodes.get(stack_node_id)
                if stack_node:
                    # Check if it is a provider
                     if hasattr(stack_node, "register_provider_context"):
                         active_providers.add(stack_node.register_provider_context())
                     elif "ProviderNode" in type(stack_node).__name__:
                         active_providers.add("Generic")
            elif isinstance(ctx_item, dict):
                 # Fallback for structured context if implemented later
                 if ctx_item.get("type") == "provider":
                    active_providers.add(ctx_item.get("provider_type"))
        
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
        
        # Always increment ROOT
        if "ROOT" not in self.scope_pulse_counts:
            self.scope_pulse_counts["ROOT"] = 0
        self.scope_pulse_counts["ROOT"] += count
        
        # Increment named scopes in stack
        if stack:
            for s_id in stack:
                if s_id not in self.scope_pulse_counts:
                    self.scope_pulse_counts[s_id] = 0
                self.scope_pulse_counts[s_id] += count

    def _auto_cleanup_scopes(self, current_stack, target_stack):
        """
        Identifies scopes dropped during error handling and triggers cleanup
        on any Providers that were active in those scopes.
        """
        if len(current_stack) <= len(target_stack):
            return

        # Identify dropped scopes (suffix)
        dropped_ids = current_stack[len(target_stack):]
        
        # Cleanup in reverse order (LIFO)
        for node_id in reversed(dropped_ids):
             # Handle IDs (Standard) or Objects (Legacy/Future)
             nid = node_id if isinstance(node_id, str) else getattr(node_id, "get", lambda x: None)("id")
             
             if not nid: continue
             
             node = self.nodes.get(nid)
             if node and hasattr(node, "cleanup_provider_context"):
                 # [SINGLETON CHECK]
                 # If Singleton Scope is True, we DO NOT force cleanup on error
                 is_singleton = node.properties.get("Singleton Scope", False)
                 if is_singleton:
                     # logger.info(f"Preserving Singleton Provider: {node.name}")
                     continue
                     
                 # Force Cleanup
                 try:
                     node.cleanup_provider_context()
                     # logger.info(f"[Safety Net] Cleaned up dropped provider: {node.name}")
                 except Exception as e:
                     logger.warning(f"Failed to cleanup provider {node.name}: {e}")

    def _check_scope_terminations(self):
        """
        Deep check for any scopes that have zero pulses remaining.
        Triggers their final 'Flow' output.
        """
        if not self.scope_pulse_counts:
            return

        changed = True
        while changed:
            changed = False
            # Identify scopes that hit zero active pulses.
            # We must account for the pulse currently being processed (current_pulse_stack).
            finished_scopes = []
            for s, count in self.scope_pulse_counts.items():
                if s == "ROOT": continue
                
                # Check if this scope is in the current in-flight pulse stack
                in_flight_count = 0
                if self.current_pulse_stack and s in self.current_pulse_stack:
                    in_flight_count = 1
                
                if count + in_flight_count <= 0:
                    finished_scopes.append(s)
            
            # Sort finished scopes by deepest nesting level (if possible to infer)
            # Actually, the re-check inside the loop is the most robust way.
            
            for scope_id in finished_scopes:
                # [FIX] Re-verify count hasn't been incremented by a child termination in this same pass
                if self.scope_pulse_counts.get(scope_id, 0) > 0:
                    continue

                if scope_id in self.pending_terminations:
                    # Retrieve original context to resume completion flow
                    stack, prio, delay = self.pending_terminations[scope_id]
                    completion_ports = ["Flow", "Out", "Done", "Success", "True", "False"]
                    
                    logger.info(f"Provider Scope {scope_id} finished. Resuming completion flow.")
                    
                    # Trigger the completion ports
                    triggered_map = self.flow.route_outputs(
                        scope_id, self.wires, self.bridge, stack,
                        port_include=completion_ports,
                        priority=prio, delay=delay,
                        headless=self.headless, trace=self.trace,
                        force_trigger=True
                    )
                    
                    # Increment the count of the parent scope for any pulses created
                    self._increment_scope_count(stack, sum(triggered_map.values()))
                    
                    del self.pending_terminations[scope_id]
                else:
                    pass
                
                # Cleanup scope tracking
                if scope_id in self.scope_pulse_counts:
                    # Only delete if it's still <= 0 after everything
                    if self.scope_pulse_counts[scope_id] <= 0:
                        del self.scope_pulse_counts[scope_id]
                        changed = True
