"""
System Monitor Nodes.

Resource Monitor: CPU, RAM, Disk usage using psutil.

Dependencies: psutil.
"""
import time
import threading
from synapse.core.super_node import SuperNode
from synapse.nodes.registry import NodeRegistry
from synapse.core.types import DataType

try:
    import psutil
except ImportError:
    psutil = None

@NodeRegistry.register("Resource Monitor", "System/Hardware")
class ResourceMonitorNode(SuperNode):
    """
    Background service that periodically captures system performance metrics.
    Monitors CPU, RAM, and primary drive usage on a fixed interval.
    
    Inputs:
    - Flow: Start the monitoring service.
    
    Outputs:
    - Tick: Pulse triggered on every monitoring interval update.
    - CPU Usage: Current CPU utilization percentage.
    - RAM Usage: Current RAM utilization percentage.
    - Disk Usage: Current primary drive utilization percentage.
    """
    version = "2.1.0"

    def __init__(self, node_id, name, bridge):
        super().__init__(node_id, name, bridge)
        self.is_native = True
        self.is_service = True
        self.properties["Interval"] = 1.0 # Seconds
        self.no_show = ["Interval"]
        self._running = False
        
        self.define_schema()
        self.register_handler("Flow", self.start_monitor)

    def define_schema(self):
        self.input_schema = {
            "Flow": DataType.FLOW
        }
        self.output_schema = {
            "Tick": DataType.FLOW,
            "CPU Usage": DataType.NUMBER,
            "RAM Usage": DataType.NUMBER,
            "Disk Usage": DataType.NUMBER
        }

    def start_monitor(self, **kwargs):
        if self._running: return
        
        if not psutil:
            self.logger.error("Dependency 'psutil' not found.")
            return

        self._running = True
        interval = float(self.properties.get("Interval", 1.0))
        
        threading.Thread(target=self._monitor, args=(interval,), daemon=True).start()
        self.logger.info(f"Monitoring service started (interval: {interval}s).")
        # Service started, no immediate output flow to trigger (Tick triggers later)

    def _monitor(self, interval):
        while self._running:
            try:
                cpu = psutil.cpu_percent(interval=None)
                ram = psutil.virtual_memory().percent
                disk = psutil.disk_usage('/').percent
                
                self.bridge.set(f"{self.node_id}_CPU Usage", cpu, self.name)
                self.bridge.set(f"{self.node_id}_RAM Usage", ram, self.name)
                self.bridge.set(f"{self.node_id}_Disk Usage", disk, self.name)
                self.bridge.set(f"_TRIGGER_FIRE_{self.node_id}", "Tick", self.name) # Firing Tick port
                
            except Exception as e:
                self.logger.error(f"Monitor service error: {e}")
                
            time.sleep(interval)

    def stop(self):
        self._running = False
        self.logger.info("Monitoring service stopped.")
