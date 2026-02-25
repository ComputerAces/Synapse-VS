from synapse.core.super_node import SuperNode
from synapse.nodes.registry import NodeRegistry
from synapse.core.types import DataType
import os
import re
import fnmatch

@NodeRegistry.register("Batch Iterator", "Logic/Control Flow")
class BatchIteratorNode(SuperNode):
    """
    Iterates through files in a directory that match a specific pattern.
    Supports recursive searching and provides loop control through 'Loop' and 'Exit' inputs.
    
    Inputs:
    - Flow: Initial trigger to start the iteration.
    - Loop: Trigger for the next iteration step.
    - Exit: Trigger to immediately stop the iteration.
    - Path: The directory path to scan for files.
    - Pattern: Glob pattern for matching files (e.g., '*.txt').
    - Recursive: If True, searches subdirectories.
    
    Outputs:
    - Flow: Triggered once the iteration is complete or exited.
    - Loop Flow: Triggered for each matching file found.
    - File Path: The full path of the current file.
    - File Name: The name of the current file.
    - Index: The current iteration index (starts at 0).
    - Count: Total number of files matched.
    """
    version = "2.1.0"

    def __init__(self, node_id, name, bridge):
        super().__init__(node_id, name, bridge)
        self.is_native = True
        self.properties["Recursive"] = False
        self.define_schema()
        self.register_handlers()

    def register_handlers(self):
        self.register_handler("Flow", self.do_work)
        self.register_handler("Loop", self.do_work)
        self.register_handler("Exit", self.do_work)

    def define_schema(self):
        self.input_schema = {
            "Flow": DataType.FLOW,
            "Loop": DataType.FLOW,
            "Exit": DataType.FLOW,
            "Path": DataType.STRING,
            "Pattern": DataType.STRING,
            "Recursive": DataType.BOOLEAN
        }
        self.output_schema = {
            "Flow": DataType.FLOW,
            "Loop Flow": DataType.FLOW,
            "File Path": DataType.STRING,
            "File Name": DataType.STRING,
            "Index": DataType.NUMBER,
            "Count": DataType.NUMBER
        }

    def do_work(self, **kwargs):
        Path = kwargs.get("Path") or self.properties.get("Path", "")
        Pattern = kwargs.get("Pattern") or self.properties.get("Pattern", "*")
        _trigger = kwargs.get("Trigger")
        
        index_key = f"{self.node_id}_internal_index"
        files_key = f"{self.node_id}_internal_files"

        if _trigger == "Exit":
            self.logger.info(f"EXIT: Breaking batch loop.")
            self.bridge.set(index_key, None, self.name)
            self.bridge.set(files_key, None, self.name)
            self.bridge.set(f"{self.node_id}_ActivePorts", ["Flow"], self.name)
            return True

        stored_index = self.bridge.get(index_key)
        stored_files = self.bridge.get(files_key)
        
        if _trigger == "Loop":
            if stored_index is not None:
                current_index = int(stored_index) + 1
            else:
                current_index = 0
            file_list = stored_files or []
        else:
            folder_path = Path
            pattern = Pattern
            recursive = kwargs.get("Recursive") or self.properties.get("Recursive", False)

            if not folder_path or not os.path.isdir(folder_path):
                self.logger.error(f"Error: Invalid folder path: '{folder_path}'")
                self.bridge.set(f"{self.node_id}_ActivePorts", ["Flow"], self.name)
                return True

            if pattern.startswith(".") and not pattern.startswith("*"):
                pattern = "*" + pattern

            file_list = self._collect_files(folder_path, pattern, recursive)
            current_index = 0
            self.bridge.set(files_key, file_list, self.name)
            self.bridge.set(f"{self.node_id}_Count", len(file_list), self.name)
            self.logger.info(f"Batch Init: {len(file_list)} files.")

        if file_list and current_index < len(file_list):
            file_path = file_list[current_index]
            file_name = os.path.basename(file_path)
            self.bridge.set(index_key, current_index, self.name)
            self.bridge.set(f"{self.node_id}_File Path", file_path, self.name)
            self.bridge.set(f"{self.node_id}_File Name", file_name, self.name)
            self.bridge.set(f"{self.node_id}_Index", current_index, self.name)
            self.bridge.set(f"{self.node_id}_ActivePorts", ["Loop Flow"], self.name)
        else:
            self.logger.info(f"Batch Complete.")
            self.bridge.set(index_key, None, self.name)
            self.bridge.set(files_key, None, self.name)
            self.bridge.set(f"{self.node_id}_ActivePorts", ["Flow"], self.name)
        return True

    def _collect_files(self, folder, pattern, recursive):
        matched = []
        if recursive:
            for root, dirs, files in os.walk(folder):
                for fname in files:
                    if fnmatch.fnmatch(fname, pattern):
                        matched.append(os.path.join(root, fname))
        else:
            try:
                for fname in os.listdir(folder):
                    full_path = os.path.join(folder, fname)
                    if os.path.isfile(full_path) and fnmatch.fnmatch(fname, pattern):
                        matched.append(full_path)
            except PermissionError:
                self.logger.error(f"Permission denied: '{folder}'")
        matched.sort()
        return matched

@NodeRegistry.register("Exit Batch", "Logic/Control Flow")
class ExitBatchNode(SuperNode):
    """
    Immediately terminates an active Batch Iterator loop.
    
    This node acts like a 'break' statement. When triggered, it signals the 
    parent Batch Iterator to stop processing the current batch and transition 
    to its final 'Flow' output.
    
    Inputs:
    - Flow: Trigger the early exit.
    
    Outputs:
    - Flow: Pulse triggered after signaling the break.
    """
    version = "2.1.0"
    def __init__(self, node_id, name, bridge):
        super().__init__(node_id, name, bridge)
        self.is_native = True
        self.define_schema()
        self.register_handlers()

    def register_handlers(self):
        self.register_handler("Flow", self.do_work)

    def define_schema(self):
        self.input_schema = {
            "Flow": DataType.FLOW
        }
        self.output_schema = {
            "Flow": DataType.FLOW
        }

    def do_work(self, **kwargs):
        self.bridge.set(f"{self.node_id}_ActivePorts", ["Flow"], self.name)
        return True
