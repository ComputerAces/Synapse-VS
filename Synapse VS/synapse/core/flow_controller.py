import heapq
import time
from synapse.utils.logger import setup_logger

class FlowController:
    """
    Manages the execution flow (Queue, Branching, and Signal Routing).
    Decides WHAT runs next, but not HOW it runs.
    
    Updated to use Priority Queue and Delayed Execution.
    """
    def __init__(self, start_node_id, initial_stack=None, trace=True):
        self.logger = setup_logger("FlowController")
        
        # Priority Queue Item: (-priority, arrival_order, node_id, context_stack, trigger_port)
        # Python's heapq is a min-heap. We want max priority first, so negating priority.
        # arrival_order ensures FIFO for same priority.
        self.queue = []
        self.counter = 0 # Monotonic counter for arrival order
        
        # Delayed Queue: List of (wake_time, item_tuple)
        self.delayed_queue = []
        
        self.executed_nodes = set()
        self.trace = trace
        
        # Initial push
        self.push(start_node_id, initial_stack or [], "Flow", priority=0)
        
    def has_next(self):
        # Check if any delayed items are ready
        self._process_delayed()
        return len(self.queue) > 0 or len(self.delayed_queue) > 0
        
    def pop(self):
        self._process_delayed()
        
        if self.queue:
            # Item: (neg_prio, count, node_id, stack, port)
            _, _, node_id, stack, port = heapq.heappop(self.queue)
            return node_id, stack, port
            
        return None, None, None
        
    def push(self, node_id, context_stack, trigger_port="Flow", priority=0, delay=0):
        """
        Pushes a node to the execution queue.
        :param priority: Higher numbers run first.
        :param delay: Milliseconds to wait before making eligible.
        """
        if delay > 0:
            wake_time = time.time() + (delay / 1000.0)
            item = (-priority, self.counter, node_id, context_stack, trigger_port)
            self.counter += 1
            heapq.heappush(self.delayed_queue, (wake_time, item))
            # self.logger.debug(f"Delayed {node_id} for {delay}ms")
        else:
            # Immediate Push
            heapq.heappush(self.queue, (-priority, self.counter, node_id, context_stack, trigger_port))
            self.counter += 1
            
    def _process_delayed(self):
        """Moves ready items from delayed_queue to main queue."""
        if not self.delayed_queue: return
        
        now = time.time()
        # delayed_queue is a heap sorted by wake_time effectively if we push right
        # But we pushed tuples (wake_time, item). 
        # So heappush ensures earliest wake_time is at [0].
        
        while self.delayed_queue and self.delayed_queue[0][0] <= now:
            _, item = heapq.heappop(self.delayed_queue)
            heapq.heappush(self.queue, item)

    def route_outputs(self, node_id, wires, bridge, context_stack, headless=False, trace=None, priority=0, delay=0, stack_override_map=None, port_exclude=None, port_include=None, force_trigger=False):
        """
        Determines which wires to activate based on node output state.
        Now supports Priority, Delay, Stack Overrides, Filtering, and Force Trigger.
        Returns a dict of {port_name: count} for all triggered pulses.
        """
        trace_active = trace if trace is not None else self.trace
        
        # [NEW] Force Trigger bypasses bridge signals
        if force_trigger:
            active_ports = None
            condition_result = None
        else:
            # [IPC OPTIMIZATION] Fetch signals in batch
            signals = bridge.get_batch([f"{node_id}_ActivePorts", f"{node_id}_Condition", f"{node_id}_Priority"])
            active_ports = signals.get(f"{node_id}_ActivePorts")
            condition_result = signals.get(f"{node_id}_Condition")
        # priority_override = signals.get(f"{node_id}_Priority") # Already passed as arg from Engine

        flow_priority = priority
        
        # Legacy Flow Ports
        legacy_flow_names = [
            "Flow", "True", "False", "Out", "Exec", "Then", "Else", "Loop", 
            "Try", "Catch", "Finished Flow", "Done", "Success", "Failure"
        ]
        
        relevant_wires = [w for w in wires if w["from_node"] == node_id]
        
        port_counts = {}
        for w in relevant_wires:
            port = w["from_port"]
            
            # Apply Filters
            if port_exclude and port in port_exclude: continue
            if port_include and port not in port_include: continue

            should_trigger = False
            
            # 1. PRIMARY: Explicit Active Ports
            # If the node explicitly declared which ports are active, we follow ONLY that.
            if active_ports is not None:
                if port in active_ports:
                    should_trigger = True
                
                if should_trigger:
                    target_stack = stack_override_map.get(port, context_stack) if stack_override_map else context_stack
                    self._push_flow(w, target_stack, headless, trace_active, flow_priority, delay)
                    port_counts[port] = port_counts.get(port, 0) + 1
                continue # Strictly skip all fallbacks for this wire

            # 2. SECONDARY: Condition Result
            # If no active_ports, check for True/False branching.
            if condition_result is not None:
                # Check for special signals, ignore for routing decision logic (handled delay passing already)
                # But we need to ensure we don't treat ("_YSWAIT", 500) as "True".
                if isinstance(condition_result, tuple) and len(condition_result) > 0 and str(condition_result[0]).startswith("_YS"):
                    pass # It's a signal, treat as "Flow" basically implies standard flow? 
                    # Usually Wait Node returns True or Signal. 
                    # If it returns Signal, we assume Success/Flow.
                
                # Check if this node even HAS condition ports before we commit to this routing path
                has_true_false = any(pw["from_port"] in ("True", "False") for pw in relevant_wires)
                
                if port == "True" and condition_result is True: should_trigger = True
                elif port == "False" and condition_result is False: should_trigger = True
                
                if should_trigger:
                    target_stack = stack_override_map.get(port, context_stack) if stack_override_map else context_stack
                    self._push_flow(w, target_stack, headless, trace_active, flow_priority, delay)
                    port_counts[port] = port_counts.get(port, 0) + 1
                
                # ONLY skip legacy fallback if the result was a boolean AND the node has conditional ports
                if isinstance(condition_result, bool) and has_true_false:
                    continue 

            # 3. FALLBACK: Legacy Name Convention
            # Only reached if both active_ports and condition_result are None.
            # OR if condition_result was a Signal tuple (Wait Node)
            if port in legacy_flow_names:
                should_trigger = True
            
            if should_trigger:
                target_stack = stack_override_map.get(port, context_stack) if stack_override_map else context_stack
                self._push_flow(w, target_stack, headless, trace_active, flow_priority, delay)
                port_counts[port] = port_counts.get(port, 0) + 1
        
        return port_counts

    def _push_flow(self, wire, context_stack, headless, trace=True, priority=0, delay=0):
        """Helper to push to queue and print debug info."""
        if trace and not headless:
            prio_str = f" [P:{priority}]" if priority != 0 else ""
            delay_str = f" [D:{delay}ms]" if delay > 0 else ""
            print(f"[FLOW] {wire['from_node']}:{wire['from_port']} -> {wire['to_node']}:{wire['to_port']}{prio_str}{delay_str}", flush=True)
        self.push(wire["to_node"], context_stack, wire["to_port"], priority=priority, delay=delay)
        return 1

    def route_wireless(self, tag, all_nodes, context_stack, headless=False, trace=True):
        """
        Handles wireless signal broadcasting.
        """
        if not tag: return
        
        if trace and not headless:
            print(f"[WIRELESS] Broadcasting tag: {tag}")
            
        flow_count = 0
        for sub_id, sub_node in all_nodes.items():
            sub_tag = sub_node.properties.get("tag", "")
            if sub_tag == tag:
                self.logger.info(f"Wireless Jump: -> {sub_node.name}")
                if trace and not headless:
                    print(f"[FLOW] Wireless -> {sub_id}:Wireless")
                self.push(sub_id, context_stack, "Wireless") # Priority 0 for wireless default
                flow_count += 1
        return flow_count

    def export_state(self):
        """Exports the current flow queue and history for Time-Travel."""
        # Clean queue for export (remove neg priority for readability if needed, but pickle handles implementation)
        return {
            "queue": list(self.queue),
            "delayed_queue": list(self.delayed_queue),
            "executed_nodes": list(self.executed_nodes),
            "counter": self.counter
        }

    def import_state(self, state):
        """Restores flow state."""
        if not state: return
        self.queue = list(state.get("queue", []))
        heapq.heapify(self.queue) # Re-heapify just in case
        self.delayed_queue = list(state.get("delayed_queue", []))
        heapq.heapify(self.delayed_queue)
        self.executed_nodes = set(state.get("executed_nodes", []))
        self.counter = state.get("counter", 0)
