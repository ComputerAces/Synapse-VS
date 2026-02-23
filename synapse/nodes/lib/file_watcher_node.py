from synapse.core.super_node import SuperNode
from synapse.nodes.registry import NodeRegistry
from synapse.core.types import DataType
import os
import datetime

@NodeRegistry.register("File Watcher", "IO/Files")
class FileWatcherNode(SuperNode):
    """
    Monitors a file for changes by comparing its last modification time.
    
    This node checks if the file at 'Path' has been updated since the last check 
    or since 'Last Time'. It is useful for triggering logic when a configuration 
    file, log, or data export is updated by an external process.
    
    Inputs:
    - Flow: Trigger the check.
    - Path: The absolute path to the file to monitor.
    - Last Time: Optional ISO timestamp to compare against (replaces internal memory).
    
    Outputs:
    - Flow: Pulse triggered after the check.
    - Changed: Boolean True if the file has been modified.
    - Time: The ISO timestamp of the file's current modification time.
    """
    version = "2.1.0"

    def define_schema(self):
        self.input_schema = {
            "Flow": DataType.FLOW,
            "Path": DataType.STRING,
            "Last Time": DataType.STRING
        }
        self.output_schema = {
            "Flow": DataType.FLOW,
            "Changed": DataType.BOOLEAN,
            "Time": DataType.STRING
        }

    def register_handlers(self):
        self.register_handler("Flow", self.handle_check)

    def handle_check(self, Path=None, Last_Time=None, **kwargs):
        path_val = Path if Path is not None else kwargs.get("Path") or self.properties.get("Path", "")
        last_time_val = Last_Time if Last_Time is not None else kwargs.get("Last Time") or self.properties.get("Last Time", "")
        
        if not path_val or not os.path.exists(path_val):
            self.bridge.set(f"{self.node_id}_Changed", False, self.name)
            self.bridge.set(f"{self.node_id}_ActivePorts", ["Flow"], self.name)
            return True
            
        mtime = os.path.getmtime(path_val)
        
        # Determine comparison time
        if last_time_val:
            try:
                # Try to parse ISO format
                import datetime
                dt_cmp = datetime.datetime.fromisoformat(last_time_val.replace(" ", "T"))
                last_mtime = dt_cmp.timestamp()
            except:
                last_mtime = self.properties.get("LastMtime", 0.0)
        else:
            last_mtime = self.properties.get("LastMtime", 0.0)

        changed = mtime > last_mtime
        
        self.properties["LastMtime"] = mtime
        self.bridge.set(f"{self.node_id}_Changed", changed, self.name)
        
        dt = datetime.datetime.fromtimestamp(mtime)
        self.bridge.set(f"{self.node_id}_Time", dt.strftime("%Y-%m-%d %H:%M:%S"), self.name)
        self.bridge.set(f"{self.node_id}_ActivePorts", ["Flow"], self.name)
        return True

    def __init__(self, node_id, name, bridge):
        super().__init__(node_id, name, bridge)
        self.properties["Path"] = ""
        self.properties["Last Time"] = ""
        self.properties["LastMtime"] = 0.0
        self.no_show = ["LastMtime"]
        self.define_schema()
        self.register_handlers()
