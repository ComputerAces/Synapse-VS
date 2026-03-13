from axonpulse.core.node import BaseNode
from axonpulse.core.types import DataType, TypeCaster
import inspect

class SuperNode(BaseNode):
    """
    Advanced Base Node with Strict Typing, Event Handlers, and Lifecycle Hooks.
    
    Schema:
    - input_schema: { "PortName": DataType }
    - output_schema: { "PortName": DataType }
    
    Handlers:
    - register_handler("PortName", callback)
    """

    def __init__(self, node_id, name, bridge):
        super().__init__(node_id, name, bridge)
        
        # Schema Definitions
        self.input_schema = {}
        self.output_schema = {}
        
        # Event Handlers { "TriggerPort": method }
        self.handlers = {}
        
        # Metadata Persistence
        self.node_type = getattr(self.__class__, "node_label", "Unknown")
        
        # Default Handlers
        self.register_handler("Flow", self.main)
        
        # Schema Versioning
        self.node_version = getattr(self.__class__, "node_version", 1)
        self.loaded_version = 1 # Set by loader if different
        self.is_legacy = False # Set by loader if mismatch
        self.latest_version = self.node_version # Reference for UI
        
        # Standard Lifecycle Triggers
        self.define_schema()
        self.register_handlers()
        
        # [FIX] Sync schemas to BaseNode internal maps immediately
        self.sync_schema()

    def sync_schema(self):
        """
        Explicitly refresh input_types and output_types from the current 
        schema and properties. Should be called after properties are loaded.
        """
        self._build_ports()

    def _get_composed_input_schema(self):
        """Calculates the full input schema by merging class, custom, and dynamic ports."""
        # 1. Start with Class Schema
        final_schema = self.input_schema.copy()
        
        # 2. Merge Custom Schema (from User/UI)
        custom = self.properties.get("CustomInputSchema", {})
        for name, type_str in custom.items():
            try:
                final_schema[name] = DataType(type_str)
            except:
                final_schema[name] = DataType.ANY

        # 3. Merge "Additional Inputs" (GUI-specific dynamic ports)
        type_map = self.properties.get("input_types", {})
        if not type_map: type_map = self.properties.get("custom_input_schema", {})
        
        if "Additional Inputs" in self.properties and isinstance(self.properties["Additional Inputs"], list):
            for name in self.properties["Additional Inputs"]:
                if name not in final_schema:
                    t_val = type_map.get(name)
                    try:
                        final_schema[name] = DataType(t_val) if t_val else DataType.ANY
                    except Exception:
                        final_schema[name] = DataType.ANY
        
        # 4. Handle Flow trigger override
        if "Flow" in self.handlers and "Flow" not in final_schema:
            final_schema["Flow"] = DataType.FLOW
            
        return final_schema

    def _get_composed_output_schema(self):
        """Calculates the full output schema."""
        # 1. Start with Class Schema
        final_schema = self.output_schema.copy()
        
        # 2. Merge Custom Schema
        custom = self.properties.get("CustomOutputSchema", {})
        for name, type_str in custom.items():
            try:
                final_schema[name] = DataType(type_str)
            except:
                final_schema[name] = DataType.ANY

        # 3. Merge "Additional Outputs" (GUI-specific dynamic ports)
        type_map = self.properties.get("output_types", {})
        if not type_map: type_map = self.properties.get("custom_output_schema", {})
        
        if "Additional Outputs" in self.properties and isinstance(self.properties["Additional Outputs"], list):
            for name in self.properties["Additional Outputs"]:
                if name not in final_schema:
                    t_val = type_map.get(name)
                    try:
                        final_schema[name] = DataType(t_val) if t_val else DataType.ANY
                    except Exception:
                        final_schema[name] = DataType.ANY
                        
        # 4. Standard Flow convention
        if "Flow" not in final_schema:
            final_schema["Flow"] = DataType.FLOW
            
        return final_schema

    def _build_ports(self):
        """
        [FIX] Dedicated initialization method to register ports in the BaseNode maps.
        This provides a single place for the 'side-effects' of registering ports.
        """
        # Build Inputs
        in_schema = self._get_composed_input_schema()
        for name, dtype_val in in_schema.items():
            dtype = dtype_val.get("type", DataType.ANY) if isinstance(dtype_val, dict) else dtype_val
            self.add_input(name, dtype)
            
        # Build Outputs
        out_schema = self._get_composed_output_schema()
        for name, dtype_val in out_schema.items():
            dtype = dtype_val.get("type", DataType.ANY) if isinstance(dtype_val, dict) else dtype_val
            self.add_output(name, dtype)

    def set_output(self, port_name, value):
        """
        Write an output value using the PortRegistry's UUID-based bridge key.
        Also writes the legacy key for backward compatibility.
        """
        # UUID-based key (primary)
        registry = getattr(self.bridge, '_port_registry', None)
        if registry:
            uuid_key = registry.bridge_key(self.node_id, port_name, "output")
            self.bridge.set(uuid_key, value, self.name)
        
        # Legacy key (backward compatibility)
        if hasattr(self, "is_legacy") and self.is_legacy:
            self.bridge.set(f"{self.node_id}_{port_name}", value, self.name)

    def define_schema(self):
        """
        Override to define input/output schema. 
        Called during init.
        """
        # Ensure properties exist for custom extensions
        if "CustomInputSchema" not in self.properties:
            self.properties["CustomInputSchema"] = {}
        if "CustomOutputSchema" not in self.properties:
            self.properties["CustomOutputSchema"] = {}

    def register_handler(self, port_name, callback):
        """Registers a method to be called when a specific input Flow port is triggered."""
        self.handlers[port_name] = callback

    def register_handlers(self):
        """
        Override to bind multiple triggers.
        Called during init.
        """
        pass

    @property
    def default_inputs(self):
        """Idempotent getter for the UI to discover input ports."""
        schema = self._get_composed_input_schema()
        ports = []
        # Ensure Flow is first if present
        if "Flow" in schema:
            ports.append(("Flow", schema.pop("Flow")))
            
        for name, dtype_val in schema.items():
            dtype = dtype_val.get("type", DataType.ANY) if isinstance(dtype_val, dict) else dtype_val
            ports.append((name, dtype))
        return ports

    @property
    def default_outputs(self):
        """Idempotent getter for the UI to discover output ports."""
        schema = self._get_composed_output_schema()
        ports = []
        # Ensure Flow is first if present
        if "Flow" in schema:
            ports.append(("Flow", schema.pop("Flow")))
            
        for name, dtype_val in schema.items():
            dtype = dtype_val.get("type", DataType.ANY) if isinstance(dtype_val, dict) else dtype_val
            ports.append((name, dtype))
        return ports

    async def execute_async(self, **kwargs):
        """
        Async execution wrapper.
        1. Identifies Trigger.
        2. Casts Inputs based on Schema.
        3. Routes to Handler (awaiting if async).
        """
        trigger = kwargs.get("_trigger", "Flow")
        
        # 1. Strict Type Casting & Defensive Data Resolution (Fallback Rule)
        clean_args = {}
        
        # First, copy all internal arguments (_trigger, _context, etc.)
        for k, v in kwargs.items():
            if k.startswith("_"):
                clean_args[k] = v

        # Priority resolution for defined inputs: Wire (kwargs) > Property (static)
        for name, schema_val in self.input_schema.items():
            target_type = schema_val.get("type", DataType.ANY) if isinstance(schema_val, dict) else schema_val
            
            # Skip triggers for data resolution
            if target_type == DataType.FLOW:
                continue

            # Apply Fallback: Use wire if available, else check node property
            val = kwargs.get(name)
            if val is None:
                val = self.properties.get(name)
            
            if val is not None:
                try:
                    clean_args[name] = TypeCaster.cast(val, target_type)
                except Exception as e:
                    self.logger.warning(f"TypeCast error for {name}: {e}")
                    clean_args[name] = val

        # Capture any dynamic wires not in schema (Additional Inputs)
        for name, val in kwargs.items():
            if not name.startswith("_") and name not in clean_args:
                clean_args[name] = val

        # 2. Route to Handler
        handler = self.handlers.get(trigger)
        if handler:
            # Check if handler is async
            if inspect.iscoroutinefunction(handler):
                return await handler(**clean_args)
            else:
                return handler(**clean_args)
        else:
            self.logger.warning(f"No handler registered for trigger: {trigger}")
            return True

    def execute(self, **kwargs):
        """
        Standard execution wrapper.
        1. Identifies Trigger.
        2. Casts Inputs based on Schema.
        3. Routes to Handler.
        """
        trigger = kwargs.get("_trigger", "Flow")
        
        # 1. Strict Type Casting & Defensive Data Resolution (Fallback Rule)
        clean_args = {}
        
        # Copy internal arguments
        for k, v in kwargs.items():
            if k.startswith("_"):
                clean_args[k] = v

        # Fallback Resolution: Wire (kwargs) > Property (static)
        for name, schema_val in self.input_schema.items():
            target_type = schema_val.get("type", DataType.ANY) if isinstance(schema_val, dict) else schema_val
            if target_type == DataType.FLOW:
                continue

            val = kwargs.get(name)
            if val is None:
                val = self.properties.get(name)
            
            if val is not None:
                try:
                    clean_args[name] = TypeCaster.cast(val, target_type)
                except Exception as e:
                    self.logger.warning(f"TypeCast error for {name}: {e}")
                    clean_args[name] = val

        # Capture dynamics
        for name, val in kwargs.items():
            if not name.startswith("_") and name not in clean_args:
                clean_args[name] = val

        # 2. Route to Handler
        handler = self.handlers.get(trigger)
        if handler:
            # [FIX] Optimized Async-in-Sync Fallback
            # Modern nodes (Ollama/MCP/Playwright) often use async handlers. 
            # If triggered in a sync context (e.g. via ThreadPool or direct call),
            # we must bridge the gap without deadlocking the event loop.
            if inspect.iscoroutinefunction(handler):
                try:
                    import asyncio
                    try:
                        loop = asyncio.get_running_loop()
                        # CRITICAL: If we are calling .result() on the same thread as the loop, we DEADLOCK.
                        # Instead of blocking, we log an error and refuse to hang the system.
                        self.logger.error(f"DEADLOCK RISK: Async handler '{trigger}' triggered on the Event Loop thread for {self.name}. Execution refused.")
                        return False
                    except RuntimeError:
                        # No loop running in this thread - safe to use asyncio.run (blocks worker thread, not loop)
                        self.logger.info(f"Async-in-Sync fallback: Executing '{trigger}' via asyncio.run for {self.name}")
                        return asyncio.run(handler(**clean_args))
                except Exception as e:
                    self.logger.error(f"Async-in-Sync fallback failed for {self.name}: {e}")
                    raise e
            
            return handler(**clean_args)
        else:
            self.logger.warning(f"No handler registered for trigger: {trigger}")
            return True

    def is_handler_async(self, trigger):
        """Checks if the method registered for the trigger is a coroutine."""
        handler = self.handlers.get(trigger)
        return inspect.iscoroutinefunction(handler)

    def main(self, **kwargs):
        """Default handler for 'Flow'."""
        pass
        
    def lifecycle_on_create(self):
        """Called when node is created."""
        pass

    def lifecycle_on_destroy(self):
        """Called when node is deleted."""
        pass
