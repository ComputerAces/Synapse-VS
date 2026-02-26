import heapq
import time
import threading
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
        self._lock = threading.Lock() # Thread safety for queue operations
        
        # Initial push
        self.push(start_node_id, initial_stack or [], "Flow", priority=0)
        
    def has_next(self):
        with self._lock:
            # Check if any delayed items are ready
            self._process_delayed_locked()
            return len(self.queue) > 0 or len(self.delayed_queue) > 0
        
    def pop(self):
        with self._lock:
            self._process_delayed_locked()
            
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
        with self._lock:
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
            
    def _process_delayed_locked(self):
        """Moves ready items from delayed_queue to main queue. ASSUMES LOCK IS HELD."""
        if not self.delayed_queue: return
        
        now = time.time()
        while self.delayed_queue and self.delayed_queue[0][0] <= now:
            _, item = heapq.heappop(self.delayed_queue)
            heapq.heappush(self.queue, item)

    def route_outputs(self, node_id, wires, bridge, context_stack, headless=False, trace=None, priority=0, delay=0, stack_override_map=None, port_exclude=None, port_include=None, force_trigger=False, push_directly=True):
        """
        Determines which wires to activate based on node output state.
        Returns a list of triggered pulses (dicts): [{"to_node": id, "stack": s, "port": p, "prio": pr, "delay": d}]
        """
        trace_active = trace if trace is not None else self.trace
        
        if force_trigger:
            active_ports = None
            condition_result = None
        else:
            signals = bridge.get_batch([f"{node_id}_ActivePorts", f"{node_id}_Condition", f"{node_id}_Priority"])
            active_ports = signals.get(f"{node_id}_ActivePorts")
            condition_result = signals.get(f"{node_id}_Condition")

        flow_priority = priority
        legacy_flow_names = [
            "Flow", "True", "False", "Out", "Exec", "Then", "Else", "Loop", 
            "Try", "Catch", "Finished Flow", "Done", "Success", "Failure"
        ]
        
        relevant_wires = [w for w in wires if w["from_node"] == node_id]
        triggered_pulses = []
        
        for w in relevant_wires:
            port = w["from_port"]
            if port_exclude and port in port_exclude: continue
            if port_include and port not in port_include: continue

            should_trigger = False
            
            # 1. PRIMARY: Explicit Active Ports
            if active_ports is not None:
                if port in active_ports:
                    should_trigger = True
                
                if should_trigger:
                    target_stack = stack_override_map.get(port, context_stack) if stack_override_map else context_stack
                    pulse = self._build_pulse(w, target_stack, flow_priority, delay)
                    if push_directly:
                        self._push_flow_intent(pulse, headless, trace_active)
                    triggered_pulses.append(pulse)
                continue

            # 2. SECONDARY: Condition Result
            if condition_result is not None:
                has_true_false = any(pw["from_port"] in ("True", "False") for pw in relevant_wires)
                
                if port == "True" and condition_result is True: should_trigger = True
                elif port == "False" and condition_result is False: should_trigger = True
                
                if should_trigger:
                    target_stack = stack_override_map.get(port, context_stack) if stack_override_map else context_stack
                    pulse = self._build_pulse(w, target_stack, flow_priority, delay)
                    if push_directly:
                        self._push_flow_intent(pulse, headless, trace_active)
                    triggered_pulses.append(pulse)
                
                if isinstance(condition_result, bool) and has_true_false:
                    continue 

            # 3. FALLBACK: Legacy Name Convention
            if port in legacy_flow_names:
                should_trigger = True
            
            if should_trigger:
                target_stack = stack_override_map.get(port, context_stack) if stack_override_map else context_stack
                pulse = self._build_pulse(w, target_stack, flow_priority, delay)
                if push_directly:
                    self._push_flow_intent(pulse, headless, trace_active)
                triggered_pulses.append(pulse)
        
        return triggered_pulses

    def _build_pulse(self, wire, context_stack, priority, delay):
        """Creates a pulse dictionary."""
        return {
            "from_node": wire["from_node"],
            "from_port": wire["from_port"],
            "to_node": wire["to_node"],
            "to_port": wire["to_port"],
            "stack": list(context_stack), # Clone stack
            "priority": priority,
            "delay": delay
        }

    def _push_flow_intent(self, pulse, headless, trace=True):
        """Helper to push to queue and print debug info."""
        if trace and not headless:
            prio_str = f" [P:{pulse['priority']}]" if pulse['priority'] != 0 else ""
            delay_str = f" [D:{pulse['delay']}ms]" if pulse['delay'] > 0 else ""
            print(f"[FLOW] {pulse['from_node']}:{pulse['from_port']} -> {pulse['to_node']}:{pulse['to_port']}{prio_str}{delay_str}", flush=True)
        self.push(pulse["to_node"], pulse["stack"], pulse["to_port"], priority=pulse["priority"], delay=pulse["delay"])
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
