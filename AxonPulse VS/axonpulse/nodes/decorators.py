import functools
import inspect
import re
from typing import Any, List, Dict, Optional, Callable, Union
from axonpulse.core.super_node import SuperNode
from axonpulse.core.types import DataType, TypeCaster

def _py_type_to_axon(py_type) -> DataType:
    if py_type == int: return DataType.INTEGER
    if py_type == float: return DataType.NUMBER
    if py_type == str: return DataType.STRING
    if py_type == bool: return DataType.BOOLEAN
    if py_type == list: return DataType.LIST
    if py_type == dict: return DataType.DICT
    return DataType.ANY

class DecoratedNode(SuperNode):
    """Dynamic wrapper for functions decorated with @axon_node."""
    def __init__(self, node_id, name, bridge, func, category, version, outputs=None, is_native=True, is_async=False):
        self.func = func
        self.category = category
        self.version = version
        self.custom_outputs = outputs or ["Result"]
        self.is_native = is_native
        self.is_async = is_async
        
        # Analyze function signature for inputs and properties
        self.sig = inspect.signature(func)
        self.input_params = []
        self.input_mapping = {} # sanitized -> original
        self.property_defaults = {}
        
        for name, param in self.sig.parameters.items():
            if name in ["_bridge", "_node", "_node_id", "kwargs"] or name.startswith("_"):
                continue
            
            # Map underscores back to spaces if needed (heuristic)
            original_name = name.replace("_", " ")
            self.input_params.append(name)
            self.input_mapping[name] = original_name
            
            if param.default != inspect.Parameter.empty:
                self.property_defaults[name] = param.default

        super().__init__(node_id, name, bridge)
        # Restore execution flags after SuperNode/BaseNode init
        self.is_native = is_native
        self.is_async = is_async
        self.name = self.func.__name__.replace("_", " ").title()

    def define_schema(self):
        # Build Inputs
        inputs = {"Flow": DataType.FLOW}
        for name in self.input_params:
            param = self.sig.parameters[name]
            original_name = self.input_mapping[name]
            inputs[original_name] = _py_type_to_axon(param.annotation)
        self.input_schema = inputs

        # Build Outputs
        outputs = {"Flow": DataType.FLOW}
        ret_annotation = self.sig.return_annotation
        
        if isinstance(self.custom_outputs, list):
            for port in self.custom_outputs:
                outputs[port] = DataType.ANY
        else:
            outputs["Result"] = _py_type_to_axon(ret_annotation)
        
        self.output_schema = outputs

        # Initialize properties
        for name, value in self.property_defaults.items():
            original_name = self.input_mapping[name]
            if original_name not in self.properties:
                self.properties[original_name] = value

    def register_handlers(self):
        self.register_handler("Flow", self.run_decorated_func)

    def run_decorated_func(self, **kwargs):
        # Build arguments for the function
        args = {}
        for name in self.input_params:
            original_name = self.input_mapping[name]
            # Check dynamic inputs first, then properties
            val = kwargs.get(original_name)
            if val is None:
                val = self.properties.get(original_name)
            args[name] = val

        # Inject context if requested
        if "_bridge" in self.sig.parameters:
            args["_bridge"] = self.bridge
        if "_node" in self.sig.parameters:
            args["_node"] = self
        if "_node_id" in self.sig.parameters:
            args["_node_id"] = self.node_id
        
        # Handle **kwargs if the function accepts it
        if any(p.kind == inspect.Parameter.VAR_KEYWORD for p in self.sig.parameters.values()):
            # Pass all remaining data_io inputs
            args.update({k: v for k, v in kwargs.items() if k not in args})

        try:
            result = self.func(**args)
            
            # Map result to outputs
            if result is False:
                return False
                
            if isinstance(result, dict) and len(self.custom_outputs) > 1:
                for k, v in result.items():
                    if k in self.output_schema:
                        self.set_output(k, v)
            elif len(self.custom_outputs) == 1:
                # If there's only one output (excluding Flow), set it
                port = self.custom_outputs[0]
                if port != "Flow":
                    self.set_output(port, result)
            
            return True
        except Exception as e:
            self.logger.error(f"Error in decorated node {self.name}: {e}")
            return False

def axon_node(category: str, version: str = "1.0.0", outputs: List[str] = None, node_label: str = None, is_native: bool = True, is_async: bool = False):
    """Decorator to transform a Python function into an AxonPulse node."""
    def decorator(func: Callable):
        from axonpulse.nodes.registry import NodeRegistry
        
        # Determine the label
        if node_label:
            label = node_label
        else:
            # Fallback: handle CamelCase and underscores
            raw_name = func.__name__
            # Insert spaces before capital letters
            label = re.sub(r'([a-z])([A-Z])', r'\1 \2', raw_name)
            # Replace underscores with spaces
            label = label.replace("_", " ").title()
            # Remove "Node" suffix if it exists after conversion
            if label.endswith(" Node"):
                label = label[:-5]

        # Create a dynamic wrapper class with a unique name for pickling
        class_name = f"Node_{func.__name__}"
        
        class DynamicNode(DecoratedNode):
            def __init__(self, node_id, name, bridge):
                super().__init__(node_id, name, bridge, func, category, version, outputs, is_native, is_async)

        # Fix __name__ and __module__ for pickling compatibility on Windows
        DynamicNode.__name__ = class_name
        DynamicNode.__qualname__ = class_name
        mod = inspect.getmodule(func)
        if mod:
            DynamicNode.__module__ = mod.__name__
            setattr(mod, class_name, DynamicNode)

        # Preserve docstring and metadata
        DynamicNode.__doc__ = func.__doc__
        
        # Register the node
        NodeRegistry.register(label, category)(DynamicNode)
        
        return func
    return decorator
