from synapse.core.super_node import SuperNode
from synapse.nodes.registry import NodeRegistry
from synapse.core.types import DataType
import time

@NodeRegistry.register("Barrier", "Logic/Control Flow")
class BarrierNode(SuperNode):
    """
    A synchronization point that waits for multiple parallel execution paths to arrive before proceeding.
    Useful for merging branches of a graph that were split for parallel processing.
    
    Inputs:
    - Flow: Primary trigger.
    - Flow 1, 2, ...: Additional synchronization inputs (can be added dynamically).
    - Timeout: Maximum time (in seconds) to wait for all flows. 0 = wait forever.
    
    Outputs:
    - Flow: Triggered once all wired inputs have arrived or the timeout is reached.
    """
    version = "2.1.0"

    def __init__(self, node_id, name, bridge):
        super().__init__(node_id, name, bridge)
        self.is_native = True
        self.properties["Timeout"] = 0  # 0 = no timeout
        self.dynamic_inputs = True
        
        # Tracking state (reset each run)
        self._trigger_count = 0
        self._triggered_ports = set()
        self._run_id = None
        
        self.define_schema()
        self.register_handlers()

    def register_handlers(self):
        # Register handler for all existing and future flow inputs
        for name, dtype in self.input_schema.items():
            if dtype == DataType.FLOW:
                self.register_handler(name, self.do_work)

    def define_schema(self):
        self.input_schema = {
            "Flow": DataType.FLOW,
            "Flow 1": DataType.FLOW,
            "Timeout": DataType.NUMBER
        }
        self.output_schema = {
            "Flow": DataType.FLOW
        }

    def do_work(self, Timeout=None, **kwargs):
        """
        Called each time a flow arrives at this node.
        Only proceeds when all expected flows have arrived.
        """
        # Get current run ID to reset state between graph runs
        current_run_id = self.bridge.get("_SYSTEM_RUN_ID")
        if current_run_id != self._run_id:
            self._run_id = current_run_id
            self._trigger_count = 0
            self._triggered_ports = set()
            self._start_time = time.time()
        
        # Determine which port triggered this call (Engine passes this as _trigger)
        trigger_port = kwargs.get("_trigger", "Flow")
        
        # Prevent double-counting same port in same run
        if trigger_port in self._triggered_ports:
            return
            
        self._triggered_ports.add(trigger_port)
        self._trigger_count += 1
        
        # Determine expected count based on wired inputs
        wired_ports = self._get_wired_flow_ports()
        expected = len(wired_ports)
        if expected == 0: expected = 1 # Minimum 1
        
        timeout = float(Timeout) if Timeout is not None else float(self.properties.get("Timeout", 0))
        
        self.logger.info(f"Barrier: {self._trigger_count}/{expected} paths arrived ({trigger_port})")
        self.bridge.set(f"{self.node_id}_Progress", f"{self._trigger_count}/{expected}", self.name)
        
        # Check if we should proceed (either all arrived or timeout)
        all_arrived = self._trigger_count >= expected
        timed_out = timeout > 0 and (time.time() - self._start_time) >= timeout
        
        if all_arrived or timed_out:
            if timed_out and not all_arrived:
                self.logger.warning(f"Barrier TIMEOUT reached ({timeout}s). Proceeding with {self._trigger_count}/{expected} paths.")
            else:
                self.logger.info(f"✓ All paths arrived, proceeding!")
            
            self.bridge.set(f"{self.node_id}_ActivePorts", ["Flow"], self.name)
            # Reset for potential re-entry in same run (loops)
            self._triggered_ports = set()
            self._trigger_count = 0
        else:
            self.bridge.set(f"{self.node_id}_ActivePorts", [], self.name)
        return True
    
    def _get_wired_flow_ports(self):
        """Get list of Flow input ports that are actually wired."""
        wired = []
        for port_name, dtype in self.input_schema.items():
            if dtype != DataType.FLOW: continue
            
            # Check various ways engine tracks wires
            if self.bridge.get(f"{self.node_id}_{port_name}_Wired_In") or \
               self.bridge.get(f"{self.node_id}_{port_name}_HasInput"):
                wired.append(port_name)
        return wired



@NodeRegistry.register("Reset Barrier", "Logic/Control Flow")
class ResetBarrierNode(SuperNode):
    """
    Resets a 'Barrier' node's internal synchronization counters.
    
    Forcibly clears the progress of a specific Barrier, allowing it to 
    re-synchronize from zero. Useful for looping or complex branches 
    that re-enter the same Barrier multiple times.
    
    Inputs:
    - Flow: Trigger the reset.
    - Barrier ID: The unique node ID of the Barrier to reset.
    
    Outputs:
    - Flow: Triggered after the reset.
    """
    version = "2.1.0"

    def __init__(self, node_id, name, bridge):
        super().__init__(node_id, name, bridge)
        self.is_native = True
        self.properties["Barrier ID"] = ""
        
        self.define_schema()
        self.register_handler("Flow", self.do_work)
    
    def define_schema(self):
        self.input_schema = {
            "Flow": DataType.FLOW,
            "Barrier ID": DataType.STRING,
            "TargetCount": DataType.INTEGER
        }
        self.output_schema = {
            "Flow": DataType.FLOW
        }

    def do_work(self, **kwargs):
        barrier_id = kwargs.get("Barrier ID") or self.properties.get("Barrier ID", "")
        
        if not barrier_id:
            self.logger.error(f"Error: No Barrier ID provided")
            return
        
        # Reset the barrier's state via bridge
        self.bridge.set(f"{barrier_id}_Progress", "0/0", self.name)
        self.bridge.set(f"{barrier_id}_TriggerCount", 0, self.name)
        
        self.logger.info(f"Reset Barrier {barrier_id}")
        self.bridge.set(f"{self.node_id}_ActivePorts", ["Flow"], self.name)
        return True
