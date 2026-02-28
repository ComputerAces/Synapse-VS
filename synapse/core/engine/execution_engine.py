import time
import os
import threading
import copy
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
                    parent_id = self.bridge.get("_SYNP_PARENT_NODE_ID")
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
                print(f"[SYNP_SUBGRAPH_FINISHED] {self.parent_node_id}")

        finally:
            with self._lock:
                # Only root thread should shutdown services if it's truly the end
                # Note: SubGraphs should not stop master services, only their own.
                # stop_all_services only cleans up nodes registered to *this engine's* registry.
                self.stop_all_services()
            
            # If root thread, shutdown dispatcher
            # Actually, we should only shutdown if we are the MASTER thread.
            # Master thread is the one that started with START_NODE.
            # branches should just exit.
            pass
            
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
                if self.bridge.get("_SYNP_YIELD"):
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

    def _execute_step(self, node_id, pulse_stack, trigger_port, flow_controller):
        """
        Executes a single node pulse cycle. 
        Thread-safe and shared between main thread and parallel branches.
        Returns: True if iteration should continue, False if thread should terminate.
        """
        # 0. Setup
        context_stack = list(pulse_stack) if pulse_stack else []
        node = self.nodes.get(node_id)

        # 0. [NEW] Cancellation Check
        # If any scope in the stack is marked as canceled in the bridge, drop this pulse.
        for scope_id in context_stack:
            if self.bridge.get(f"SYNAPSE_CANCEL_SCOPE_{scope_id}"):
                # Node might be None if it was removed by hot reload, so check before accessing .name
                node_name = node.name if node else node_id
                logger.info(f"Cancellation: Dropping pulse for {node_name} (Scope {scope_id} terminated)")
                self._decrement_scope_counts(pulse_stack)
                self._check_scope_terminations()
                return False

        if not node:
            logger.error(f"Node {node_id} not found!")
            # Decrement pulse count for this "failed" pulse
            self._decrement_scope_counts(pulse_stack)
            return True


        # 1. Barrier/Return check
        node_type = type(node).__name__
        is_return = "ReturnNode" in node_type or "Return" in node_type
        if is_return:
            active_scope = context_stack[-1] if context_stack else "ROOT"
            
            # [FIX] Do NOT apply Return Barrier for Loop Iterations
            # Loops manage their own continuity via active_ports/stack_overrides.
            # Terminating them here can break the loop chain.
            is_loop_scope = str(active_scope).startswith("LO_")
            
            if not is_loop_scope:
                # [LOCKBOX] Gather return data immediately
                return_data = self._gather_inputs(node_id, trigger_port)
                if return_data:
                    # [STRICT WHITELIST] Filter by schema AND aggressive keyword block
                    reserved = ["Flow", "Exec", "In", "_trigger", "_bridge", "_engine", "_context_stack", "_context_pulse"]
                    blocked_keywords = ["color", "additional", "schema", "label", "context", "provider"]
                    
                    payload = {}
                    for k, v in return_data.items():
                        # [FIX] Capture ALL non-reserved, non-UI-blocked ports
                        # Dynamic Return nodes may not have 'Last Image' in their schema cache yet.
                        if k in reserved:
                            continue
                            
                        # Allow internal metadata, block everything else containing keywords
                        if k.startswith("_SYNP_"):
                            payload[k] = v
                            continue
                            
                        pn_lower = k.lower()
                        if any(kw in pn_lower for kw in blocked_keywords):
                            continue
                        payload[k] = v
                    
                    with self._lock:
                        if active_scope not in self.deferred_returns:
                            self.deferred_returns[active_scope] = {}
                        self.deferred_returns[active_scope].update(payload)
                        
                        # [LABEL] Stash node name for the parent return path
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

        # 2. Controls (Speed/Pause)
        self._handle_controls()
        if not self.headless and self.bridge.get("_SYSTEM_STEP_BACK"):
            # Master thread handles step back; branches just wait or skip
            if threading.current_thread() == threading.main_thread():
                self.bridge.set("_SYSTEM_STEP_BACK", False, "Engine")
                self._step_back()
                # If main thread steps back, it means the current node was put back in queue.
                # So this pulse didn't "complete" its execution cycle.
                # We should NOT decrement its count here.
                return True
            else:
                # Branch threads just wait for the main thread to resolve the step back
                while self.bridge.get("_SYSTEM_STEP_BACK"): time.sleep(0.1)

        # 3. Validation & Update Stack
        try:
            self._validate_provider_context(node, context_stack)
        except RuntimeError as e:
            logger.error(f"Provider Validation Error in {node.name}: {e}")
            # Notify UI of Error State (Red Highlight)
            print(f"[NODE_ERROR] {node_id} | {e}", flush=True)
            
            # Handle as standard error
            handler_info = self.context_manager.handle_error(e, node, context_stack, self.wires)
            if handler_info:
                handler_id, parent_stack, catch_wires = handler_info[:3]

                for w in catch_wires:
                    flow_controller.push(w["to_node"], parent_stack, w["to_port"])
                    self._increment_scope_count(parent_stack, 1)
            else:
                # If unhandled, we can either stop or panic. 
                # For visual feedback, we want the node to stay red.
                # We trigger the panic handler which might stop the engine or just log.
                self._handle_panic(e, node, context_stack, None, inputs=None)
            
            # Final Decrement for this pulse
            self._decrement_scope_counts(pulse_stack)
            return True

        node_inputs = self._gather_inputs(node_id, trigger_port)
        if node_inputs is None:
            # strict validation failed. Error Flow triggered in _gather_inputs.
            logger.warning(f"Skipping {node.name} due to Validation Failure.")
            
            # Check if Local Error Flow is wired
            local_error_wired = False
            for w in self.wires:
                if w["from_node"] == node_id and w["from_port"] in ["Error Flow", "Error", "Panic"]:
                    local_error_wired = True
                    break
            
            if local_error_wired:
                # 4a. Local Route Output Flow (Error Flow only)
                triggered = flow_controller.route_outputs(
                    node_id, 
                    self.wires, 
                    self.bridge, 
                    context_stack,
                    headless=self.headless
                )
                self._increment_scope_count(context_stack, sum(triggered.values()))
            else:
                # 4b. Global Panic Fallback
                error = ValueError(f"Validation Failed in {node.name}")
                self._handle_panic(error, node, context_stack, None, inputs=node_inputs)
            
            # Final Decrement for this pulse
            self._decrement_scope_counts(pulse_stack)
            return True

        context_stack = self.context_manager.update_stack(node, context_stack, trigger_port)

        # 4. Dispatch & Execute
        if self.trace and not self.headless: print(f"[NODE_START] {node_id}", flush=True)
        # Sanitize
        self.bridge.bubble_set(f"{node_id}_ActivePorts", None, "Engine_Sanitize")
        self.bridge.bubble_set(f"{node_id}_Condition", None, "Engine_Sanitize")

        logger.info(f"Executing {node.name} (Context: {len(context_stack)})...")
        exec_result = None
        # Trigger Bubble-up
        if self.parent_bridge and self.parent_node_id:
            self.parent_bridge.bubble_set(f"{self.parent_node_id}_SubGraphActivity", True, "ChildEngine")
            print(f"[SYNP_SUBGRAPH_ACTIVITY] {self.parent_node_id}")

        # [FIX] Thread-Safe Context Passing
        # We pass it in inputs so handlers can access it, and to the dispatcher explicitly.
        # We NO LONGER set node.context_stack = context_stack here because nodes are singletons
        # and parallel pulses would overwrite each other.
        node_inputs["_context_stack"] = context_stack
        
        try:
            result_future = self.dispatcher.dispatch(node, node_inputs, context_stack)
            exec_result = result_future.wait()
            self.bridge.pin_all()
        except Exception as e:
            # Error Handling
            handler_info = self.context_manager.handle_error(e, node, context_stack, self.wires)
            if handler_info:
                handler_id, parent_stack, catch_wires = handler_info[:3]
                self._auto_cleanup_scopes(context_stack, parent_stack)
                for w in catch_wires:
                    flow_controller.push(w["to_node"], parent_stack, w["to_port"])
                    self._increment_scope_count(parent_stack, 1)
            else:
                self._handle_panic(e, node, context_stack, None, inputs=node_inputs)
            
            # Final Decrement for this pulse
            self._decrement_scope_counts(pulse_stack)
            return True

        if self.trace and not self.headless: print(f"[NODE_STOP] {node_id}", flush=True)
        if exec_result is not None: self.bridge.bubble_set(f"{node_id}_Condition", exec_result, "Engine_Sync")
        self._handle_wireless(node, context_stack)

        # [YIELD HANDLING] Check for Special Yield Signals in Result
        # Nodes can return ("_YSWAIT", ms) or ("_YSYIELD",) to pause/defer
        cond_result = exec_result 
        
        # Debug Logging
        if isinstance(cond_result, tuple) and len(cond_result) > 0 and str(cond_result[0]).startswith("_YS"):
             logger.info(f"Yield Signal Detected: {cond_result}")

        # Check priority from node (set during execute)
        node_priority = self.bridge.get(f"{node_id}_Priority")
        current_prio = int(node_priority) if node_priority is not None else 0

        # 5. Routing
        is_provider = hasattr(node, "register_provider_context")
        provider_type = node.register_provider_context() if is_provider else None
        is_delayable_provider = is_provider and provider_type != "Flow Provider"
        prov_wired = any(w["from_port"] == "Provider Flow" for w in self.wires if w["from_node"] == node_id)
        completion_ports = ["Flow", "Out", "Done", "Success", "True", "False"]

        stack_overrides = {}
        # 1. Provider Scoping (Native)
        if is_delayable_provider and prov_wired:
            stack_overrides["Provider Flow"] = context_stack + [node_id]
            with self._lock:
                if node_id not in self.scope_pulse_counts: self.scope_pulse_counts[node_id] = 0
        
        # 2. General Scoping (Bridge-driven)
        user_overrides = self.bridge.get(f"{node_id}_StackOverrides")
        if isinstance(user_overrides, dict):
            stack_overrides.update(user_overrides)

        delay_ms = 0
        if isinstance(cond_result, tuple) and len(cond_result) >= 2 and cond_result[0] == "_YSWAIT":
            delay_ms = cond_result[1]
            # Check for Pulse Flag (Index 2)
            should_pulse = False
            if len(cond_result) > 2:
                should_pulse = bool(cond_result[2])
            
            if should_pulse:
                print(f"[NODE_WAITING_PULSE] {node_id} | {delay_ms}", flush=True)
            else:
                print(f"[NODE_WAITING_START] {node_id} | {delay_ms}", flush=True)

        triggered = flow_controller.route_outputs(
            node_id, self.wires, self.bridge, context_stack,
            headless=self.headless, trace=self.trace,
            priority=current_prio,
            delay=delay_ms,
            stack_override_map=stack_overrides,
            port_exclude=completion_ports if is_delayable_provider and prov_wired else None,
            push_directly=False
        )

        if triggered:
            # Primary continues in current thread
            primary = triggered[0]
            if delay_ms > 0:
                logger.info(f"Delaying primary flow -> {primary['to_node']} by {delay_ms}ms")
            flow_controller._push_flow_intent(primary, self.headless, self.trace)
            self._increment_scope_count(primary["stack"], 1)
            
            # Spawn threads for additional branches
            for i in range(1, len(triggered)):
                bp = triggered[i]
                if delay_ms > 0:
                    logger.info(f"Delaying branch flow -> {bp['to_node']} by {delay_ms}ms")
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
                # Immediate completion
                triggered_comp = flow_controller.route_outputs(
                    node_id, self.wires, self.bridge, context_stack,
                    port_include=completion_ports, priority=current_prio, delay=delay_ms,
                    headless=self.headless, trace=self.trace,
                    force_trigger=False, push_directly=True
                )
                self._increment_scope_count(context_stack, len(triggered_comp))

        # 6. Step Cleanup
        self._decrement_scope_counts(pulse_stack) # Use original pulse stack for decrement
        self._check_scope_terminations()
        
        if node.is_service and node.node_id not in self.service_registry:
            logger.info(f"Persistent Service Registered: {node.name}")
            self.service_registry[node.node_id] = node
            self.bridge.bubble_set(f"{node.node_id}_IsServiceRunning", True, "Engine")
            print(f"[SERVICE_START] {node.node_id}")

        return True

    def _decrement_scope_counts(self, stack):
        """Helper to safely decrement pulse hierarchy."""
        with self._lock:
            if "ROOT" in self.scope_pulse_counts:
                self.scope_pulse_counts["ROOT"] -= 1
            if stack:
                for s_id in stack:
                    if s_id in self.scope_pulse_counts:
                        self.scope_pulse_counts[s_id] -= 1

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
        
        # 3. Pause Handling
        if self.pause_file and os.path.exists(self.pause_file):
            logger.info("Execution paused...")
            while os.path.exists(self.pause_file):
                # Still check for stop/speed signals while paused
                self._sync_settings()
                if self._check_stop_signal():
                    return
                time.sleep(0.1)
            logger.info("Execution resumed.")

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
        trace_enabled = self.bridge.get("_SYSTEM_TRACE_ENABLED", default=True)
        if self.parent_bridge:
            # Parent Stop Propagation
            if self.parent_bridge.get("_SYSTEM_STOP"):
                self.bridge.set("_SYSTEM_STOP", True, "Parent_Stop_Propagation")

            # Sub-graph specific tracing
            trace_subgraphs = self.bridge.get("_SYSTEM_TRACE_SUBGRAPHS", default=True)
            self.trace = trace_enabled and trace_subgraphs
        else:
            self.trace = trace_enabled

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
        
        with self._lock:
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
                        completion_ports = ["Flow", "Out", "Done", "Success", "True", "False"]
                        
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
        if stack:
            for s_id in stack:
                self.scope_pulse_counts[s_id] = self.scope_pulse_counts.get(s_id, 0) + count
