import os
import subprocess
import venv
import shutil
from synapse.nodes.registry import NodeRegistry
from synapse.core.types import DataType
from synapse.nodes.lib.provider_node import ProviderNode
from synapse.core.super_node import SuperNode

@NodeRegistry.register("VENV Provider", "System/VENV")
class VENVProviderNode(ProviderNode):
    """
    Establishes a Virtual Environment (VENV) context for downstream nodes.
    Automatically creates the environment if it does not exist and can 
    install a list of required pip packages upon initialization.
    
    Inputs:
    - Flow: Start the VENV provider.
    - Path: The directory where the VENV should be located (default: ./venv).
    - Requirements: A list of pip packages to ensure are installed.
    
    Outputs:
    - Flow: Pulse triggered after the scope successfully closes.
    - Provider Flow: Active pulse for nodes running within this VENV context.
    - VENV Path: The absolute path to the virtual environment directory.
    """
    version = "2.1.0"
    provider_type = "VENV Provider"

    def __init__(self, node_id, name, bridge):
        super().__init__(node_id, name, bridge)
        self.properties["Path"] = "./venv"
        self.properties["Requirements"] = []

    def define_schema(self):
        super().define_schema()
        # super already has Done and Provider Flow
        self.input_schema["Path"] = DataType.STRING
        self.input_schema["Requirements"] = DataType.LIST
        self.output_schema["VENV Path"] = DataType.STRING

    def start_scope(self, **kwargs):
        path = kwargs.get("Path") or self.properties.get("Path", "./venv")
        requirements = kwargs.get("Requirements") or self.properties.get("Requirements", [])

        if not path:
            self.logger.error("No VENV path provided.")
            return super().start_scope(**kwargs)

        abs_path = os.path.abspath(path)
        
        if not os.path.exists(abs_path):
            self.logger.info(f"Creating VENV at {abs_path}...")
            venv.create(abs_path, with_pip=True)

        python_exe = os.path.join(abs_path, "Scripts", "python.exe") if os.name == 'nt' else os.path.join(abs_path, "bin", "python")
        
        if not os.path.exists(python_exe):
            self.logger.error(f"Failed to locate python in {abs_path}")
            return super().start_scope(**kwargs)

        if requirements:
            self.logger.info(f"Installing requirements: {requirements}")
            try:
                subprocess.check_call([python_exe, "-m", "pip", "install"] + list(requirements))
            except Exception as e:
                self.logger.error(f"Failed to install requirements: {e}")
                return super().start_scope(**kwargs)

        self.bridge.set(f"{self.node_id}_Provider ID", self.node_id, self.name)
        self.bridge.set(f"{self.node_id}_Provider Type", self.provider_type, self.name)
        self.bridge.set(f"{self.node_id}_VENV_Python", python_exe, self.name)
        self.bridge.set(f"{self.node_id}_VENV Path", abs_path, self.name)
        
        return super().start_scope(**kwargs)

@NodeRegistry.register("VENV Create", "System/VENV")
class VENVCreateNode(SuperNode):
    """
    Creates a new Python Virtual Environment at the specified path.
    Includes pip by default to allow for immediate package installation.
    
    Inputs:
    - Flow: Trigger the creation process.
    - Path: The target directory for the new VENV.
    
    Outputs:
    - Flow: Pulse triggered after the operation finishes.
    - Success: True if the environment was created successfully.
    """
    version = "2.1.0"

    def __init__(self, node_id, name, bridge):
        super().__init__(node_id, name, bridge)
        self.properties["Path"] = "./venv"
        self.define_schema()
        self.register_handlers()

    def register_handlers(self):
        self.register_handler("Flow", self.do_work)

    def define_schema(self):
        self.input_schema = {
            "Flow": DataType.FLOW,
            "Path": DataType.STRING
        }
        self.output_schema = {
            "Flow": DataType.FLOW,
            "Success": DataType.BOOLEAN
        }

    def do_work(self, **kwargs):
        path = kwargs.get("Path") or self.properties.get("Path", "./venv")
        try:
            abs_path = os.path.abspath(path)
            self.logger.info(f"Creating VENV at {abs_path}...")
            venv.create(abs_path, with_pip=True)
            self.bridge.set(f"{self.node_id}_Success", True, self.name)
            self.bridge.set(f"{self.node_id}_ActivePorts", ["Flow"], self.name)
        except Exception as e:
            self.logger.error(f"VENV Create Error: {e}")
            self.bridge.set(f"{self.node_id}_Success", False, self.name)
            self.bridge.set(f"{self.node_id}_ActivePorts", ["Flow"], self.name)
        return True

@NodeRegistry.register("VENV Install", "System/VENV")
class VENVInstallNode(SuperNode):
    """
    Installs one or more pip packages into an existing virtual environment.
    
    Inputs:
    - Flow: Trigger the installation.
    - VENV Path: The path to the target virtual environment.
    - Packages: A list or single string of package names to install.
    
    Outputs:
    - Flow: Pulse triggered after the installation process completes.
    """
    version = "2.1.0"

    def __init__(self, node_id, name, bridge):
        super().__init__(node_id, name, bridge)
        self.properties["VENV Path"] = "./venv"
        self.properties["Packages"] = []
        self.define_schema()
        self.register_handlers()

    def register_handlers(self):
        self.register_handler("Flow", self.do_work)

    def define_schema(self):
        self.input_schema = {
            "Flow": DataType.FLOW,
            "VENV Path": DataType.STRING,
            "Packages": DataType.LIST
        }
        self.output_schema = {
            "Flow": DataType.FLOW
        }

    def do_work(self, **kwargs):
        venv_path = kwargs.get("VENV Path") or self.properties.get("VENV Path", "./venv")
        packages = kwargs.get("Packages") or self.properties.get("Packages", [])
        
        if isinstance(packages, str):
            packages = [packages]

        abs_path = os.path.abspath(venv_path)
        python_exe = os.path.join(abs_path, "Scripts", "python.exe") if os.name == 'nt' else os.path.join(abs_path, "bin", "python")

        if not os.path.exists(python_exe):
            self.logger.error(f"VENV not found at {abs_path}")
            self.bridge.set(f"{self.node_id}_ActivePorts", ["Flow"], self.name)
            return True

        try:
            self.logger.info(f"Installing {packages} into {abs_path}...")
            subprocess.check_call([python_exe, "-m", "pip", "install"] + list(packages))
            self.bridge.set(f"{self.node_id}_ActivePorts", ["Flow"], self.name)
        except Exception as e:
            self.logger.error(f"VENV Install Error: {e}")
            self.bridge.set(f"{self.node_id}_ActivePorts", ["Flow"], self.name)
        return True

@NodeRegistry.register("VENV Run", "System/VENV")
class VENVRunNode(SuperNode):
    """
    Executes a Python command or script within the context of a virtual environment.
    Supports running specific modules (via -m) or standalone .py files.
    
    Inputs:
    - Flow: Trigger the execution.
    - Command: The script path or module name to run.
    - Args: A list of command-line arguments to pass.
    
    Outputs:
    - Flow: Pulse triggered after the command finishes.
    - Output: The stdout resulting from the execution.
    - Exit Code: The numerical return code of the process.
    """
    version = "2.1.0"

    def __init__(self, node_id, name, bridge):
        super().__init__(node_id, name, bridge)
        self.required_providers = ["VENV Provider"]
        self.properties["Command"] = ""
        self.properties["Args"] = []
        self.define_schema()
        self.register_handlers()

    def register_handlers(self):
        self.register_handler("Flow", self.do_work)

    def define_schema(self):
        self.input_schema = {
            "Flow": DataType.FLOW,
            "Command": DataType.STRING,
            "Args": DataType.LIST
        }
        self.output_schema = {
            "Flow": DataType.FLOW,
            "Output": DataType.STRING,
            "Exit Code": DataType.INTEGER
        }

    def do_work(self, **kwargs):
        provider_id = self.get_provider_id("VENV Provider")
        if not provider_id:
             self.logger.error("No VENV Provider found for VENV Run.")
             return True
             
        venv_path = self.bridge.get(f"{provider_id}_VENV Path")
        command = kwargs.get("Command") or self.properties.get("Command", "")
        args = kwargs.get("Args") or self.properties.get("Args", [])

        if not venv_path:
             self.logger.error("VENV Path not found in provider.")
             return True

        abs_path = os.path.abspath(venv_path)
        python_exe = os.path.join(abs_path, "Scripts", "python.exe") if os.name == 'nt' else os.path.join(abs_path, "bin", "python")

        if not os.path.exists(python_exe):
            self.logger.error(f"VENV not found at {abs_path}")
            self.bridge.set(f"{self.node_id}_ActivePorts", ["Flow"], self.name)
            return True

        full_cmd = [python_exe]
        if command:
            if command.endswith(".py"):
                full_cmd.append(command)
            else:
                full_cmd = [python_exe, "-m"] + command.split()
        
        if args:
            full_cmd.extend(list(args))

        try:
            self.logger.info(f"Running in VENV: {' '.join(full_cmd)}")
            result = subprocess.run(full_cmd, capture_output=True, text=True)
            self.bridge.set(f"{self.node_id}_Output", result.stdout, self.name)
            self.bridge.set(f"{self.node_id}_Exit Code", result.returncode, self.name)
            self.bridge.set(f"{self.node_id}_ActivePorts", ["Flow"], self.name)
        except Exception as e:
            self.logger.error(f"VENV Run Error: {e}")
            self.bridge.set(f"{self.node_id}_ActivePorts", ["Flow"], self.name)
        return True

@NodeRegistry.register("VENV List", "System/VENV")
class VENVListNode(SuperNode):
    """
    Lists all pip packages currently installed in a specified virtual environment.
    
    Inputs:
    - Flow: Trigger the listing process.
    - VENV Path: The path to the virtual environment to audit.
    
    Outputs:
    - Flow: Pulse triggered after the list is retrieved.
    - Packages: A list of installed packages and their versions (pip freeze format).
    """
    version = "2.1.0"

    def __init__(self, node_id, name, bridge):
        super().__init__(node_id, name, bridge)
        self.properties["VENV Path"] = "./venv"
        self.define_schema()
        self.register_handlers()

    def register_handlers(self):
        self.register_handler("Flow", self.do_work)

    def define_schema(self):
        self.input_schema = {
            "Flow": DataType.FLOW,
            "VENV Path": DataType.STRING
        }
        self.output_schema = {
            "Flow": DataType.FLOW,
            "Packages": DataType.LIST
        }

    def do_work(self, **kwargs):
        venv_path = kwargs.get("VENV Path") or self.properties.get("VENV Path", "./venv")
        abs_path = os.path.abspath(venv_path)
        python_exe = os.path.join(abs_path, "Scripts", "python.exe") if os.name == 'nt' else os.path.join(abs_path, "bin", "python")

        if not os.path.exists(python_exe):
            self.logger.error(f"VENV not found at {abs_path}")
            self.bridge.set(f"{self.node_id}_ActivePorts", ["Flow"], self.name)
            return True

        try:
            result = subprocess.run([python_exe, "-m", "pip", "freeze"], capture_output=True, text=True)
            packages = result.stdout.splitlines()
            self.bridge.set(f"{self.node_id}_Packages", packages, self.name)
            self.bridge.set(f"{self.node_id}_ActivePorts", ["Flow"], self.name)
        except Exception as e:
            self.logger.error(f"VENV List Error: {e}")
            self.bridge.set(f"{self.node_id}_ActivePorts", ["Flow"], self.name)
        return True

@NodeRegistry.register("VENV Remove", "System/VENV")
class VENVRemoveNode(SuperNode):
    """
    Deletes an entire virtual environment directory from the disk.
    
    Inputs:
    - Flow: Trigger the removal process.
    - VENV Path: The path to the virtual environment to delete.
    
    Outputs:
    - Flow: Pulse triggered after the deletion attempt.
    - Success: True if the directory was successfully removed.
    """
    version = "2.1.0"

    def __init__(self, node_id, name, bridge):
        super().__init__(node_id, name, bridge)
        self.properties["VENV Path"] = "./venv"
        self.define_schema()
        self.register_handlers()

    def register_handlers(self):
        self.register_handler("Flow", self.do_work)

    def define_schema(self):
        self.input_schema = {
            "Flow": DataType.FLOW,
            "VENV Path": DataType.STRING
        }
        self.output_schema = {
            "Flow": DataType.FLOW,
            "Success": DataType.BOOLEAN
        }

    def do_work(self, **kwargs):
        venv_path = kwargs.get("VENV Path") or self.properties.get("VENV Path", "./venv")
        abs_path = os.path.abspath(venv_path)
        
        if not os.path.exists(abs_path):
            self.logger.warning(f"VENV path {abs_path} does not exist.")
            self.bridge.set(f"{self.node_id}_Success", False, self.name)
            self.bridge.set(f"{self.node_id}_ActivePorts", ["Flow"], self.name)
            return True

        try:
            self.logger.info(f"Removing VENV at {abs_path}...")
            shutil.rmtree(abs_path)
            self.bridge.set(f"{self.node_id}_Success", True, self.name)
            self.bridge.set(f"{self.node_id}_ActivePorts", ["Flow"], self.name)
        except Exception as e:
            self.logger.error(f"VENV Remove Error: {e}")
            self.bridge.set(f"{self.node_id}_Success", False, self.name)
            self.bridge.set(f"{self.node_id}_ActivePorts", ["Flow"], self.name)
        return True
