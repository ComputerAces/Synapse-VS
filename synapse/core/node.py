import multiprocessing
import abc
from synapse.utils.logger import setup_logger

from synapse.core.types import DataType, TypeCaster

class BaseNode(abc.ABC):
    """
    Abstract Base Class for all Synapse Nodes.
    Wrapper for process isolation.
    """
    version = "0.0.1"

    def __init__(self, node_id, name, bridge):
        self.node_id = node_id
        self.name = name
        self.bridge = bridge
        self.logger = setup_logger(f"Node-{name}")
        self.inputs = {}
        self.context_stack = []
        self.required_providers = getattr(self, "required_providers", []) # runtime dependency check
        self._hijack_provider_id = None # Set by Dispatcher if node is hijacked
        
        # Type Metadata
        self.input_types = {} 
        self.output_types = {}
        
        self.outputs = {}
        self.properties = {}
        self.process = None
        self.is_native = False 
        self.is_debug = False 
        self.is_service = False 
        self.hidden_ports = ["Provider ID", "Provider Id", "Provider_Flow_ID", "Provider_Flow_Id"] # Ports to hide from UI Properties
        self.hidden_fields = [] # Properties to hide from UI Properties
        
        # Caching
        self._provider_cache = {} # type -> (stack_hash, provider_id)
        
    @property
    def is_hijacked(self):
        """Returns True if this node's execution is currently being overridden by a provider."""
        return self._hijack_provider_id is not None

    def get_provider_id(self, provider_type):
        """
        Optimized provider lookup that caches results based on the current context stack.
        """
        if not self.context_stack:
            return None
            
        stack_hash = hash(tuple(self.context_stack))
        
        # Check cache
        if provider_type in self._provider_cache:
            c_hash, c_id = self._provider_cache[provider_type]
            if c_hash == stack_hash:
                return c_id
        
        # Cache miss or stack changed: Query bridge
        provider_id = self.bridge.get_provider_id(self.context_stack, provider_type)
        
        # Update cache
        self._provider_cache[provider_type] = (stack_hash, provider_id)
        return provider_id

    def _parse_legacy_ports(self):
        """Backwards compatibility for default_inputs/outputs properties."""
        if hasattr(self, "default_inputs"):
            for item in self.default_inputs:
                if isinstance(item, tuple):
                    self.add_input(item[0], item[1])
                else:
                    self.add_input(item, DataType.ANY)

        if hasattr(self, "default_outputs"):
            for item in self.default_outputs:
                if isinstance(item, tuple):
                    self.add_output(item[0], item[1])
                else:
                    self.add_output(item, DataType.ANY)

    def add_input(self, name, data_type="any"):
        """Defines an input port with a type. Also syncs to properties."""
        # Handle string types if passed ("string" -> DataType.STRING)
        if isinstance(data_type, str):
            try:
                data_type = DataType(data_type.lower())
            except:
                data_type = DataType.ANY
        self.input_types[name] = data_type
        
        # [NEW] Sync Input to Properties for UI editing
        if name not in ["Flow", "Exec", "Loop", "In", "Try", "Catch", "Return", "Exit", "Provider End"]:
            if name not in self.properties:
                # Default values based on type
                defaults = {
                    DataType.STRING: "",
                    DataType.NUMBER: 0,
                    DataType.BOOLEAN: False,
                    DataType.LIST: [],
                    DataType.DICT: {},
                    DataType.COLOR: [255, 255, 255, 255]
                }
                self.properties[name] = defaults.get(data_type, None)

    def add_output(self, name, data_type="any"):
        """Defines an output port with a type."""
        if isinstance(data_type, str):
            try:
                data_type = DataType(data_type.lower())
            except:
                data_type = DataType.ANY
        self.output_types[name] = data_type

    def start(self, **kwargs):
        """
        Starts the node execution in a separate process.
        """
        self.process = multiprocessing.Process(
            target=self._run_wrapper,
            kwargs=kwargs,
            name=f"SynapseNode-{self.name}"
        )
        self.process.start()
        return self.process

    def prepare_execution_args(self, runtime_inputs):
        """
        Merges properties with runtime inputs, normalizing keys to match registered Inputs.
        Also handles Type Validation/Casting and AUTOMATIC HIJACKING for missing inputs.
        """
        final_args = {}
        
        # [FIX] Prefer context from arguments for thread safety
        runtime_context = runtime_inputs.get("_context_stack", self.context_stack)

        # 1. Normalize Properties (Case-Insensitive Match)
        for k, v in self.properties.items():
            if k in self.inputs or k in self.input_types: 
                final_args[k] = v
                continue
            
            matched = False
            for input_name in self.input_types:
                if k.lower() == input_name.lower():
                    final_args[input_name] = v
                    matched = True
                    break
            
            if not matched:
                final_args[k] = v

        # 2. Override with Runtime Inputs
        final_args.update(runtime_inputs)
        
        # 3. [AUTOMATIC HIJACKING] 
        # If a required input is missing, check the context_stack for a provider that can supply it.
        if runtime_context:
            for input_name, input_type in self.input_types.items():
                if final_args.get(input_name) is None:
                    # Look for provider context matching this input name or type
                    for ctx in reversed(runtime_context):
                        if isinstance(ctx, str):
                            provider_id = ctx
                            provider_type = "Generic"
                        else:
                            provider_id = ctx.get("provider_id")
                            provider_type = ctx.get("type", "")
                        
                        # Direct Handle Discovery
                        potential_key = f"{provider_id}_{input_name}"
                        val = self.bridge.get(potential_key)
                        if val is not None:
                            final_args[input_name] = val
                            break
        
        # 4. Auto-Cast Inputs
        for name, val in final_args.items():
            if name in self.input_types:
                target_type = self.input_types[name]
                try:
                    final_args[name] = TypeCaster.cast(val, target_type)
                except Exception as e:
                     self.logger.warning(f"TypeCast failed for '{name}': {e}")
        
        return final_args

    def _run_wrapper(self, **kwargs):
        """
        Internal wrapper to catch exceptions and ensure safe exit.
        """
        try:
            self.logger.info(f"Starting execution...")
            
            # [FIX] Restore context_stack for this pulse thread-safely
            self.context_stack = kwargs.get("_context_stack", self.context_stack)

            # Use shared preparation logic
            exec_args = self.prepare_execution_args(kwargs)
            
            # Store inputs snapshot for error reporting
            self.inputs = exec_args
            
            # [NEW] Provider-Based Execution Hijacking
            # Check if any provider in our context_stack overrides this node's main function
            hijack_node_id = None
            if self.context_stack:
                # We check for an override of either the node's specific name (e.g. "Add") 
                hijack_node_id = self.bridge.get_hijack_handler(self.context_stack, self.name)
            
            if hijack_node_id:
                # [HIJACKED] Push execution to the provider's logic
                self.logger.info(f"Execution hijacked by Provider: {hijack_node_id}")
                # We use the bridge to invoke the hijack synchronously
                # The data passed is the merged execution args.
                result = self.bridge.invoke_hijack(hijack_node_id, self.name, exec_args)
            else:
                # [NATIVE] Run standard execute
                result = self.execute(**exec_args)
            self.logger.info(f"Finished. Result: {result}")
            return result
            
        except Exception as e:
            self.logger.error(f"CRITICAL FAILURE: {e}", exc_info=True)
            
            # --- Enhanced Error Handling ---
            from synapse.core.data import ErrorObject
            
            # Capture Context
            project_name = self.properties.get("project_name", "Unknown Project")
            
            # Create Error Object
            err_obj = ErrorObject(project_name, self.name, self.inputs, str(e))
            
            # Store in Bridge (Node-specific and Global for Panic Handler)
            self.bridge.set(f"{self.node_id}_LastError", err_obj, self.name)
            self.bridge.set("_SYSTEM_LAST_ERROR_OBJECT", err_obj, self.name)
            
            # Auto-Trigger 'Error' flow port if it exists
            self.bridge.set(f"{self.node_id}_ActivePorts", ["Error"], self.name)
            
            # Re-raise so engine can trigger global panic routing
            raise
            
        finally:
            pass

    @abc.abstractmethod
    def execute(self, **kwargs):
        pass

    def join(self):
        if self.process:
            self.process.join()

    def terminate(self):
        if self.process and self.process.is_alive():
            self.logger.warning(f"Terminating node process...")
            self.process.terminate()
            self.process.join()
            
        # [NEW] Lifecycle Teardown hook
        if hasattr(self, 'lifecycle_on_destroy'):
            self.lifecycle_on_destroy()

Node = BaseNode