from synapse.core.super_node import SuperNode
from synapse.nodes.registry import NodeRegistry
from synapse.core.types import DataType
import subprocess
import threading
import queue
import os

@NodeRegistry.register("Shell Command", "System/Terminal")
class ShellNode(SuperNode):
    """
    Executes shell commands on the host system.
    Supports both synchronous execution and long-running service processes with 
    standard I/O interaction.
    
    Inputs:
    - Flow: Execute the command.
    - Command: The shell command string to run.
    - EnvPath: Optional path to a virtual environment to activate.
    - StdIn: Trigger to send 'TextIn' to the running process (Service mode).
    - TextIn: String data to send to stdin.
    
    Outputs:
    - Started: Triggered when the process starts (Service mode).
    - Finished: Triggered when the process exits.
    - StdoutData: The full stdout output (Sync mode).
    - StderrData: The full stderr output (Sync mode).
    - ExitCode: The process exit return code.
    - StdOut: Triggered for each line of stdout (Service mode).
    - Flow: General pulse triggered after execution starts/finishes.
    - TextOut: The most recent line from stdout/stderr (Service mode).
    - EnvResult: The environment path that was actually used.
    """
    version = "2.1.0"

    def __init__(self, node_id, name, bridge):
        super().__init__(node_id, name, bridge)
        self.is_native = True # Run in native thread to avoid pickling locks
        self.properties["Command"] = "echo Hello"
        self.properties["Run As Service"] = False
        
        self.process = None
        self._input_queue = queue.Queue()
        
        self.define_schema()
        self.register_handlers()

    def define_schema(self):
        self.input_schema = {
            "Flow": DataType.FLOW,
            "Command": DataType.STRING,
            "EnvPath": DataType.STRING,
            "StdIn": DataType.FLOW,
            "TextIn": DataType.STRING,
            "Run As Service": DataType.BOOLEAN
        }
        self.output_schema = {
            "Started": DataType.FLOW,
            "Finished": DataType.FLOW,
            "StdoutData": DataType.STRING,
            "StderrData": DataType.STRING,
            "ExitCode": DataType.INT,
            "StdOut": DataType.FLOW,
            "Flow": DataType.FLOW,
            "TextOut": DataType.STRING,
            "EnvResult": DataType.STRING
        }

    def register_handlers(self):
        self.register_handler("Flow", self.start_command)
        self.register_handler("StdIn", self.send_input)

    def send_input(self, **kwargs):
        """Handler for 'StdIn' trigger"""
        text_in = self.bridge.get(f"{self.node_id}_TextIn")
        if self.process and self.process.poll() is None:
            if text_in:
                try:
                    if self.process.stdin:
                        self.process.stdin.write(text_in + "\n")
                        self.process.stdin.flush()
                except Exception as e:
                    self.logger.error(f"Failed to write to stdin: {e}")
        return True

    def start_command(self, Command=None, EnvPath=None, **kwargs):
        """Handler for 'Flow' trigger"""
        Command = Command if Command is not None else self.properties.get("Command", "echo Hello")
        is_service = kwargs.get("Run As Service") if kwargs.get("Run As Service") is not None else self.properties.get("Run As Service", False)
        
        # Environment Handling
        env_val = EnvPath
        if env_val is None:
            provider_id = self.get_provider_id("VENV Provider")
            if provider_id:
                env_val = self.bridge.get(f"{provider_id}_VENV Path")

        self.env_vars = os.environ.copy()
        if env_val:
            if os.path.isdir(env_val):
                if os.name == 'nt':
                     scripts = os.path.join(env_val, "Scripts")
                     self.env_vars["PATH"] = scripts + os.pathsep + self.env_vars["PATH"]
                     self.env_vars["VIRTUAL_ENV"] = env_val
                else:
                     bin_dir = os.path.join(env_val, "bin")
                     self.env_vars["PATH"] = bin_dir + os.pathsep + self.env_vars["PATH"]
                     self.env_vars["VIRTUAL_ENV"] = env_val
            self.bridge.set(f"{self.node_id}_EnvResult", env_val, self.name)

        if is_service:
            self._start_process(Command)
            self.bridge.set(f"{self.node_id}_ActivePorts", ["Started"], self.name)
            return True
        else:
            return self._run_sync(Command)

    def _start_process(self, cmd):
        if self.process and self.process.poll() is None:
            self.process.terminate()
            
        env = getattr(self, 'env_vars', None)

        try:
            self.process = subprocess.Popen(
                cmd, 
                shell=True, 
                stdout=subprocess.PIPE, 
                stderr=subprocess.PIPE, 
                stdin=subprocess.PIPE,
                text=True,
                bufsize=1, # Line buffered
                env=env
            )
            
            # Register for global cleanup
            from synapse.utils.cleanup import CleanupManager
            CleanupManager.register_process(self.process)
            
            # Start Output Readers
            threading.Thread(target=self._read_stream, args=(self.process.stdout, "Stdout"), daemon=True).start()
            threading.Thread(target=self._read_stream, args=(self.process.stderr, "Stderr"), daemon=True).start()
            
            # Start Waiter
            threading.Thread(target=self._wait_for_exit, daemon=True).start()
            
        except Exception as e:
            self.logger.error(f"Failed to start service: {e}")

    def _read_stream(self, stream, stream_name):
        if not stream: return
        for line in iter(stream.readline, ''):
            if line:
                self.bridge.set(f"{self.node_id}_TextOut", line, self.name)
                if stream_name == "Stdout":
                    self.bridge.set(f"{self.node_id}_ActivePorts", ["StdOut"], self.name)

    def _wait_for_exit(self):
        if self.process:
            rc = self.process.poll() # poll first
            if rc is None:
                rc = self.process.wait()
            self.bridge.set(f"{self.node_id}_ExitCode", rc, self.name)
            self.bridge.set(f"{self.node_id}_ActivePorts", ["Finished"], self.name)

    def _run_sync(self, cmd):
        env = getattr(self, 'env_vars', None)
        try:
            result = subprocess.run(cmd, shell=True, capture_output=True, text=True, env=env)
            self.bridge.set(f"{self.node_id}_Stdout", result.stdout, self.name)
            self.bridge.set(f"{self.node_id}_Stderr", result.stderr, self.name)
            self.bridge.set(f"{self.node_id}_ExitCode", result.returncode, self.name)
            self.bridge.set(f"{self.node_id}_ActivePorts", ["Finished"], self.name)
            return True
        except Exception as e:
            self.logger.error(f"Error: {e}")
            return False

    def terminate(self):
        if self.process:
            try:
                if self.process.poll() is None:
                    self.logger.info("Terminating shell process...")
                    self.process.terminate()
                    try:
                        self.process.wait(timeout=1.0)
                    except subprocess.TimeoutExpired:
                        self.logger.info("Force killing shell process...")
                        self.process.kill()
                        self.process.wait()
            except Exception as e:
                self.logger.error(f"Error terminating process: {e}")
        super().terminate()
