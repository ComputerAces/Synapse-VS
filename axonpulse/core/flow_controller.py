import heapq
import time
import threading
from collections import deque
from axonpulse.utils.logger import setup_logger

class FlowController:
    """
    Manages the execution flow (Queue, Branching, and Signal Routing).
    Decides WHAT runs next, but not HOW it runs.
    
    Hybrid Optimization:
    - collections.deque for O(1) Default Priority (0) tasks.
    - heapq for O(log N) Elevated/Low Priority and Delayed tasks.
    """
    def __init__(self, start_node_id, initial_stack=None, trace=True):
        self.logger = setup_logger("FlowController")
        
        # 1. Default Priority Queue (O(1) pop/push for 99% of nodes)
        # Entry: (node_id, context_stack, trigger_port)
        self.default_queue = deque()
        
        # 2. Specialty Priority Queue (O(log N))
        # Entry: (neg_prio, arrival_order, node_id, context_stack, trigger_port)
        self.priority_queue = []
        
        # 3. Delayed Queue (O(log N))
        # Entry: (wake_time, priority_item_tuple)
        self.delayed_queue = []
        
        self.counter = 0 # Monotonic counter for priority_queue arrival order
        self.executed_nodes = set()
        self.trace = trace
        self._lock = threading.Lock() # Thread safety for queue operations
        
        # Initial push (Priority 0 goes to default_queue)
        # We assume initial_stack is already in the correct format (None or tuple).
        # But if it's a list, we provide a quick fallback (Outer-to-Inner list to Inner-to-Outer tuple).
        if isinstance(initial_stack, list):
             stack = None
             for s_id in initial_stack:
                 stack = (s_id, stack)
             initial_stack = stack

        self.push(start_node_id, initial_stack, "Flow", priority=0)
        
    def has_next(self):
        with self._lock:
            # Check if any delayed items are ready
            self._process_delayed_locked()
            return len(self.priority_queue) > 0 or len(self.default_queue) > 0 or len(self.delayed_queue) > 0
        
    def pop(self):
        with self._lock:
            self._process_delayed_locked()
            
            # Tier 1: High Priority (Actual P > 0, Negated P < 0)
            if self.priority_queue and self.priority_queue[0][0] < 0:
                _, _, node_id, stack, port = heapq.heappop(self.priority_queue)
                return node_id, stack, port
                
            # Tier 2: Default Priority (O(1) fast path)
            if self.default_queue:
                return self.default_queue.popleft()
                
            # Tier 3: Low Priority (Actual P < 0, Negated P > 0)
            if self.priority_queue:
                _, _, node_id, stack, port = heapq.heappop(self.priority_queue)
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
            elif priority == 0:
                # O(1) Fast path for default priority
                self.default_queue.append((node_id, context_stack, trigger_port))
            else:
                # O(log N) path for non-zero priority
                heapq.heappush(self.priority_queue, (-priority, self.counter, node_id, context_stack, trigger_port))
                self.counter += 1
            
    def _process_delayed_locked(self):
        """Moves ready items from delayed_queue to relevant execution queue."""
        if not self.delayed_queue: return
        
        now = time.time()
        while self.delayed_queue and self.delayed_queue[0][0] <= now:
            _, item = heapq.heappop(self.delayed_queue)
            # item is (neg_prio, arrival_order, node_id, context_stack, trigger_port)
            if item[0] == 0: # Priority 0
                self.default_queue.append((item[2], item[3], item[4]))
            else:
                heapq.heappush(self.priority_queue, item)

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

            # 3. FALLBACK: Standard v2.3.0 Flow (No legacy loop)
            if active_ports is None and not should_trigger and port == "Flow":
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
            "stack": context_stack, # NO CLONING NEEDED! Immutable tuple is safe to share.
            "priority": priority,
            "delay": delay
        }

    def _push_flow_intent(self, pulse, headless, trace=True):
        """Helper to push to queue and print debug info."""
        if trace and not headless:
            prio_str = f" [P:{pulse['priority']}]" if pulse['priority'] != 0 else ""
            delay_str = f" [D:{pulse['delay']}ms]" if pulse['delay'] > 0 else ""
            print(f"[FLOW] {pulse['from_node']}:{pulse['from_port']} -> {pulse['to_node']}:{pulse['to_port']}{prio_str}{delay_str}", flush=True)
            
        self._last_triggered_wire = pulse
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
                 # Default wireless priority is 0
                self.push(sub_id, context_stack, "Wireless", priority=0)
                flow_count += 1
        return flow_count

    def export_state(self):
        """Exports the current flow queue for Time-Travel."""
        return {
            "default_queue": list(self.default_queue),
            "priority_queue": list(self.priority_queue),
            "delayed_queue": list(self.delayed_queue),
            "executed_nodes": list(self.executed_nodes),
            "counter": self.counter
        }

    def import_state(self, state):
        """Restores flow state."""
        if not state: return
        self.default_queue = deque(state.get("default_queue", []))
        self.priority_queue = list(state.get("priority_queue", []))
        heapq.heapify(self.priority_queue)
        self.delayed_queue = list(state.get("delayed_queue", []))
        heapq.heapify(self.delayed_queue)
        self.executed_nodes = set(state.get("executed_nodes", []))
        self.counter = state.get("counter", 0)
