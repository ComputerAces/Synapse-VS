from synapse.core.super_node import SuperNode
from synapse.nodes.registry import NodeRegistry
from synapse.core.constants import IS_NT
import sys
import os
import subprocess
import threading
import tempfile
from synapse.core.types import DataType

@NodeRegistry.register("Python Script", "Logic/Scripting")
class PythonNode(SuperNode):
    """
    Executes a Python script either synchronously or as a background service.
    
    Allows for custom logic extension using the bridge API. Scripts can 
    be loaded from a file or written directly in the node. Supports 
    dynamic inputs and outputs, and automatic dependency installation 
    via 'Requirements'.
    
    Inputs:
    - Flow: Trigger the script.
    - Env: Optional path to a Python executable or virtual environment.
    - Script Path: Path to a .py file to execute.
    - Script Body: Inline Python code to execute.
    - Requirements: New-line separated list of pip packages to ensure.
    - Use Current Env: Whether to use the system environment if no 'Env' is provided.
    
    Outputs:
    - Flow: Pulse triggered immediately (Service) or after completion (Sync).
    - Finished Flow: Pulse triggered after the script finishes execution.
    - Error Flow: Pulse triggered if the script crashes or fails to start.
    - Std Out: Pulse triggered for each printed line from the script.
    - Text Out: The string content of the printed line.
    """
    version = "2.1.0"
    allow_dynamic_inputs = True
    allow_dynamic_outputs = True

    def __init__(self, node_id, name, bridge):
        super().__init__(node_id, name, bridge)
        self.is_native = True # Run in native thread for bridge access
        self.properties["Script Path"] = ""
        self.properties["Script Body"] = "### Auto-Input Vars ###\nname = bridge.get(f'{node_id}_Name')\n### End of Auto-Input Vars ###\n\nprint(f'Hello {name}!')\nbridge.set(f'{node_id}_Message', f'Hello {name}!', 'PythonScript')"
        self.properties["Requirements"] = "" 
        self.properties["Use Current Env"] = True
        
        # Interactive State
        self.service_input_queue = None # Set at runtime if needed
        
        # Runtime Cache
        # Shared across all instances to avoid re-checking in loops
        if not hasattr(PythonNode, "_global_installed_requirements"):
            PythonNode._global_installed_requirements = set()

        self.define_schema()
        self.register_handlers()

    def register_handlers(self):
        self.register_handler("Flow", self.run_script)
        self.register_handler("Std In", self.handle_stdin)

    def define_schema(self):
        # Base Inputs
        self.input_schema = {
            "Flow": DataType.FLOW,
            "Env": DataType.ANY,
            "Script Path": DataType.STRING,
            "Script Body": DataType.STRING,
            "Requirements": DataType.STRING,
            "Use Current Env": DataType.BOOLEAN,
            "Run As Service": DataType.BOOLEAN,
            "Std In": DataType.FLOW,
            "Text In": DataType.STRING
        }

        # Base Outputs
        self.output_schema = {
            "Flow": DataType.FLOW,
            "Finished Flow": DataType.FLOW,
            "Error Flow": DataType.FLOW,
            "Std Out": DataType.FLOW,
            "Text Out": DataType.STRING,
            "Final Env": DataType.ANY
        }

    def handle_stdin(self, **kwargs):
        # Handle Std In trigger
        text_in = self.bridge.get(f"{self.node_id}_Text In")
        run_as_service = self.properties.get("Run As Service", False)
        
        if run_as_service and hasattr(self, 'service_input_queue') and self.service_input_queue:
            self.service_input_queue.put(text_in)
            
    def run_script(self, Env=None, **kwargs):
        # Environment Handling
        env_path = Env if Env is not None else kwargs.get("Env") or self.properties.get("Env")

        if env_path is None:
            # Check for active VENV Provider in context stack
            provider_id = self.get_provider_id("VENV Provider")
            if provider_id:
                env_path = self.bridge.get(f"{provider_id}_VENV Path")
                
        if env_path:
             # Standardize path
             if os.path.isdir(env_path):
                 if IS_NT:
                     self.python_executable = os.path.join(env_path, "Scripts", "python.exe")
                 else:
                     self.python_executable = os.path.join(env_path, "bin", "python")
             else:
                 self.python_executable = env_path
        
        # Pass Env to output (Resolved or original? Passing original path is more flexible for downstream)
        if env_path:
             self.bridge.set(f"{self.node_id}_Final Env", env_path, self.name)

        is_service = kwargs.get("Run As Service", False)
            
        reqs = kwargs.get("Requirements") or self.properties.get("Requirements", "").strip()
        if reqs:
            self._setup_micro_env(reqs)

        script_body = kwargs.get("Script Body") or self.properties.get("Script Body", "").strip()
        if not script_body:
            # Check script path fallback
            script_path = kwargs.get("Script Path") or self.properties.get("Script Path")
            if script_path and os.path.isfile(script_path):
                try:
                    with open(script_path, "r", encoding="utf-8") as f:
                        script_body = f.read()
                except Exception as e:
                    self.logger.error(f"Failed to read script path '{script_path}': {e}")
            
        if not script_body:
            self.logger.warning("No script body found.")
            self.bridge.set(f"{self.node_id}_ActivePorts", ["Flow"], self.name)
            return True
            
        # Update flag for Engine cleanup tracking
        self.is_service = is_service

        if is_service:
            # Async: Flow continues immediately, Finished fires later
            # Use Process for Services so we can terminate them
            import multiprocessing
            from synapse.nodes.lib.python_node import run_python_service
            
            # Create a queue for Stdin injection
            self.service_input_queue = multiprocessing.Queue()
            
            p = multiprocessing.Process(
                target=run_python_service,
                args=(script_body, self.node_id, self.name, self.bridge, self.service_input_queue),
                daemon=True,
                name=f"Service-{self.name}"
            )
            self.process = p
            p.start()
            
            # Notify UI
            self.bridge.set(f"{self.node_id}_IsServiceRunning", True, self.name)
            self.logger.info(f"[SERVICE_START] {self.node_id}")
            
            # Service started, flow continues
            self.bridge.set(f"{self.node_id}_ActivePorts", ["Flow"], self.name)
            
        else:
            # Sync: Finished fires BEFORE Done triggers
            success = self._run_script_task(script_body, False)
            # Active ports are set inside _run_script_task if successful
            
        return True

    def _setup_micro_env(self, reqs):
        # Use class-level cache
        installed = PythonNode._global_installed_requirements
        
        reqs_to_install = []
        for req in reqs.split("\n"):
            req = req.strip()
            if req and req not in installed:
                reqs_to_install.append(req)
        
        if not reqs_to_install:
            return

        self.logger.info(f"Ensuring dependencies: {', '.join(reqs_to_install)}")
        
        for req in reqs_to_install:
            try:
                # Pip install with quiet flags
                executable = getattr(self, 'python_executable', sys.executable)
                subprocess.check_call([
                    executable, "-m", "pip", "install", 
                    "--quiet", "--disable-pip-version-check", 
                    req
                ])
                installed.add(req)
            except Exception as e:
                self.logger.error(f"Pip fail for '{req}': {e}")


    def _run_script_task(self, script_body, is_async):
        # [Fix Encoding] Force UTF-8 for this process / thread execution
        if sys.platform == "win32":
            try:
                if sys.stdout.encoding.lower() != 'utf-8':
                    sys.stdout.reconfigure(encoding='utf-8')
                if sys.stderr.encoding.lower() != 'utf-8':
                    sys.stderr.reconfigure(encoding='utf-8')
            except Exception as e:
                print(f"[WARN] Failed to force UTF-8: {e}")
        
        try:
            # Define local scope for the script
            local_scope = {
                "bridge": self.bridge,
                "node_id": self.node_id,
                "name": self.name,
                "self": self,
                "print": print,
                "os": os,
                "sys": sys
            }
            
            exec(script_body, {}, local_scope)
            
            # Fire Finished Flow (and Done for tracing)
            self.bridge.set(f"{self.node_id}_ActivePorts", ["Finished Flow", "Flow"], self.name)
            
            return True
        except Exception as e:
            import traceback
            error_msg = str(e)
            traceback.print_exc()
            
            # 1. Check for local Error Flow
            is_wired = False
            error_port = "Error Flow"
            for p_name in ["Error Flow", "Error", "Panic"]:
                if self.bridge.get(f"{self.node_id}_{p_name}_Wired"):
                    is_wired = True
                    error_port = p_name
                    break
            
            if is_wired:
                self.bridge.set(f"{self.node_id}_ActivePorts", [error_port], self.name)
                self.bridge.set("_SYSTEM_LAST_ERROR_MESSAGE", error_msg, self.name)
                return True # Handled locally
            
            return False

    def terminate(self):
        """
        Custom termination for Python Service.
        """
        # Close Queue to prevent deadlocks
        if hasattr(self, 'service_input_queue') and self.service_input_queue:
            try:
                self.service_input_queue.close()
            except: pass
            
        # Standard Process Cleanup
        super().terminate()


# Static worker for Service Processes (Avoids pickling 'self')
def run_python_service(script_body, node_id, name, bridge, input_queue=None):
    import os
    import sys
    import traceback
    
    # [Fix Encoding] Force UTF-8 for this process
    if sys.platform == "win32":
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
    
    try:
        local_scope = {
            "bridge": bridge,
            "node_id": node_id,
            "name": name,
            "print": lambda *args, **kwargs: _proxied_print(bridge, node_id, name, *args, **kwargs),
            "input": lambda prompt="": _proxied_input(bridge, node_id, name, input_queue, prompt),
            "os": os,
            "sys": sys
        }

        exec(script_body, {}, local_scope)
        
        # When service finishes naturally
        bridge.set(f"{node_id}_ActivePorts", ["Finished Flow"], name)
        
    except Exception as e:
        print(f"[SERVICE ERROR] {name}: {e}")
        traceback.print_exc()
    finally:
        bridge.set(f"{node_id}_IsServiceRunning", False, name)
        print(f"[SERVICE_STOP] {node_id}", flush=True)

def _proxied_print(bridge, node_id, name, *args, **kwargs):
    # original print to stdout for logging
    import builtins
    builtins.print(*args, **kwargs)
    
    # Construct string
    sep = kwargs.get('sep', ' ')
    end = kwargs.get('end', '\n')
    text = sep.join(map(str, args)) + end
    
    # Send to Synapse
    bridge.set(f"{node_id}_Text Out", text, name)
    bridge.set(f"{node_id}_ActivePorts", ["Std Out"], name)

def _proxied_input(bridge, node_id, name, input_queue, prompt=""):
    import builtins
    if prompt:
        _proxied_print(bridge, node_id, name, prompt, end="")
        
    if input_queue:
        # Blocking wait for input from "Std In" trigger
        return input_queue.get()
    return ""
  

