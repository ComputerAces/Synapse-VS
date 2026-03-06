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
        
        # Default Handlers
        self.register_handler("Flow", self.main)
        
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
        _ = self.default_inputs
        _ = self.default_outputs

    def set_output(self, port_name, value):
        """
        Write an output value using the PortRegistry's UUID-based bridge key.
        Also writes the legacy key for backward compatibility.
        
        Usage:  self.set_output("Average", 0.5)
        Replaces: self.bridge.set(f"{self.node_id}_{port_name}", value, self.name)
        """
        # UUID-based key (primary)
        registry = getattr(self.bridge, '_port_registry', None)
        if registry:
            uuid_key = registry.bridge_key(self.node_id, port_name, "output")
            self.bridge.set(uuid_key, value, self.name)
        
        # Legacy key (backward compatibility)
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
        # 1. Start with Class Schema
        final_schema = self.input_schema.copy()
        
        # 2. Merge Custom Schema (from User/UI)
        custom = self.properties.get("CustomInputSchema", {})
        for name, type_str in custom.items():
            try:
                final_schema[name] = DataType(type_str)
            except:
                final_schema[name] = DataType.ANY

        # [NEW] Merge "Additional Inputs" (GUI-specific dynamic ports)
        # Type fallback order: 'input_types' -> 'custom_input_schema'
        type_map = self.properties.get("input_types", {})
        if not type_map: type_map = self.properties.get("custom_input_schema", {})
        
        for key in ["Additional Inputs", "additional_inputs"]:
            if key in self.properties and isinstance(self.properties[key], list):
                for name in self.properties[key]:
                    if name not in final_schema:
                        t_val = type_map.get(name)
                        try:
                            final_schema[name] = DataType(t_val) if t_val else DataType.ANY
                        except Exception:
                            final_schema[name] = DataType.ANY

        # 3. Generate Ports
        ports = []
        for name, dtype_val in final_schema.items():
            dtype = dtype_val.get("type", DataType.ANY) if isinstance(dtype_val, dict) else dtype_val
            ports.append((name, dtype))
            # Also register with BaseNode mechanism for checking
            self.add_input(name, dtype)
        
        # Ensure 'Flow' is present if handled
        if "Flow" in self.handlers and "Flow" not in final_schema:
            ports.insert(0, ("Flow", DataType.FLOW))
            self.add_input("Flow", DataType.FLOW)
            
        return ports

    @property
    def default_outputs(self):
        # 1. Start with Class Schema
        final_schema = self.output_schema.copy()
        
        # 2. Merge Custom Schema
        custom = self.properties.get("CustomOutputSchema", {})
        for name, type_str in custom.items():
            try:
                final_schema[name] = DataType(type_str)
            except:
                final_schema[name] = DataType.ANY

        # [NEW] Merge "Additional Outputs" (GUI-specific dynamic ports)
        # Type fallback order: 'output_types' -> 'custom_output_schema'
        type_map = self.properties.get("output_types", {})
        if not type_map: type_map = self.properties.get("custom_output_schema", {})
        
        for key in ["Additional Outputs", "additional_outputs"]:
            if key in self.properties and isinstance(self.properties[key], list):
                for name in self.properties[key]:
                    if name not in final_schema:
                        t_val = type_map.get(name)
                        try:
                            final_schema[name] = DataType(t_val) if t_val else DataType.ANY
                        except Exception:
                            final_schema[name] = DataType.ANY

        # 3. Generate Ports
        ports = []
        for name, dtype_val in final_schema.items():
            dtype = dtype_val.get("type", DataType.ANY) if isinstance(dtype_val, dict) else dtype_val
            ports.append((name, dtype))
            self.add_output(name, dtype)
            
        # Ensure 'Flow' is present (standard convention)
        if "Flow" not in final_schema:
            ports.insert(0, ("Flow", DataType.FLOW))
            self.add_output("Flow", DataType.FLOW)
            
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
            # Handle Async handlers in Sync Context
            if inspect.iscoroutinefunction(handler):
                # We are in a sync execute, but handler is async.
                # If we are here, likely the node was not flagged as is_async=True properly or engine called sync.
                # Try to run it.
                import asyncio
                try:
                    loop = asyncio.get_event_loop()
                except RuntimeError:
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
                
                if loop.is_running():
                    # This is tricky if loop is running. 
                    # But usually execute() is called in a separate process without a loop yet?
                    # Or inside a thread.
                    # For safety, we should probably warn or try run_until_complete if possible.
                    self.logger.warning(f"Async handler called in sync execute for {trigger}")
                    return asyncio.run_coroutine_threadsafe(handler(**clean_args), loop).result()
                else:
                     return loop.run_until_complete(handler(**clean_args))
            
            return handler(**clean_args)
        else:
            self.logger.warning(f"No handler registered for trigger: {trigger}")
            return True

    def main(self, **kwargs):
        """Default handler for 'Flow'."""
        pass
        
    def lifecycle_on_create(self):
        """Called when node is created."""
        pass

    def lifecycle_on_destroy(self):
        """Called when node is deleted."""
        pass
