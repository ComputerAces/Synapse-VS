from synapse.core.super_node import SuperNode
from synapse.nodes.registry import NodeRegistry
from synapse.core.types import DataType
import time

try:
    import psutil
except ImportError:
    psutil = None

@NodeRegistry.register("Watchdog", "System/Monitor")
class WatchdogNode(SuperNode):
    """
    Monitors system resource usage including CPU, RAM, and Disk space.
    Provides real-time telemetry about the host operating system.
    
    Inputs:
    - Flow: Trigger the resource check.
    
    Outputs:
    - Flow: Pulse triggered after data is captured.
    - CPU: Total CPU usage percentage (FLOAT).
    - RAM: Total RAM usage percentage (FLOAT).
    - Drives: List of connected drives and their usage (LIST).
    - OS: The name of the host operating system (STRING).
    """
    version = "2.1.0"

    def __init__(self, node_id, name, bridge):
        super().__init__(node_id, name, bridge)
        self.define_schema()
        self.register_handlers()

    def register_handlers(self):
        self.register_handler("Flow", self.do_work)

    def define_schema(self):
        self.input_schema = {"Flow": DataType.FLOW}
        self.output_schema = {
            "Flow": DataType.FLOW,
            "CPU": DataType.FLOAT,
            "RAM": DataType.FLOAT,
            "Drives": DataType.LIST,
            "OS": DataType.STRING
        }

    def do_work(self, **kwargs):
        import platform
        current_os = platform.system() 
        
        if not psutil:
            self.logger.error("'psutil' not installed.")
            self.bridge.set(f"{self.node_id}_ActivePorts", ["Flow"], self.name)
            return True

        cpu = psutil.cpu_percent(interval=0.1)
        ram = psutil.virtual_memory().percent
        
        drives = []
        try:
            partitions = psutil.disk_partitions()
            for p in partitions:
                try:
                    usage = psutil.disk_usage(p.mountpoint)
                    # format: "C: 50.5GB/100.0GB"
                    total_gb = usage.total / (1024**3)
                    used_gb = usage.used / (1024**3)
                    drives.append(f"{p.device} {used_gb:.1f}GB/{total_gb:.1f}GB")
                except PermissionError:
                    continue
        except Exception as e:
            self.logger.error(f"Disk Error: {e}")
            
        self.bridge.set(f"{self.node_id}_CPU", cpu, self.name)
        self.bridge.set(f"{self.node_id}_RAM", ram, self.name)
        self.bridge.set(f"{self.node_id}_Drives", drives, self.name)
        self.bridge.set(f"{self.node_id}_OS", current_os, self.name)
        
        self.bridge.set(f"{self.node_id}_ActivePorts", ["Flow"], self.name)
        return True
