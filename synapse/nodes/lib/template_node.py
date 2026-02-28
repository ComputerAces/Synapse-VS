"""
Template Injector Node.

Bridges raw data and professional output using string templates.
Supports dynamic input ports.
Uses safe formatting that leaves unknown placeholders intact.
"""
import re
from synapse.core.super_node import SuperNode
from synapse.nodes.registry import NodeRegistry
from synapse.core.types import DataType


def _safe_format(template, values):
    """
    Safe string formatting that leaves unknown placeholders intact.
    
    If {date} is in the template but not in values, it stays as "{date}"
    instead of raising a KeyError.
    
    Args:
        template: String with {key} placeholders.
        values:   Dict of key->value mappings.
    
    Returns:
        Formatted string with known placeholders replaced.
    """
    def replacer(match):
        key = match.group(1)
        if key in values:
            return str(values[key])
        # Leave unknown placeholders as-is
        return match.group(0)

    # Match {word} patterns, but not {{escaped}}
    return re.sub(r'\{(\w+)\}', replacer, template)


@NodeRegistry.register("Template Injector", "Data/Strings")
class TemplateInjectorNode(SuperNode):
    """
    Injects values into a string template using placeholders like {name} or {id}.
    
    Inputs:
    - Flow: Execution trigger.
    - Template: The string template containing {key} placeholders.
    - Input Items: A dictionary of key-value pairs to inject into the template.
    
    Outputs:
    - Flow: Triggered after the injection is complete.
    - Result: The formatted string with placeholders replaced.
    """
    version = "2.1.0"

    def __init__(self, node_id, name, bridge):
        super().__init__(node_id, name, bridge)
        self.is_native = True
        self.properties["Template"] = "Hello {name}, your ID is {id}."
        self.define_schema()
        self.register_handlers()

    def define_schema(self):
        self.input_schema = {
            "Flow": DataType.FLOW,
            "Template": DataType.STRING,
            "Input Items": DataType.DICT
        }
        self.output_schema = {
            "Flow": DataType.FLOW,
            "Result": DataType.STRING
        }

    def register_handlers(self):
        self.register_handler("Flow", self.inject_template)

    def inject_template(self, Template=None, **kwargs):
        template = Template if Template is not None else kwargs.get("Template") or self.properties.get("Template", "")
        items = kwargs.get("Input Items") or {}

        if not template:
            self.logger.warning("Empty template.")
            self.bridge.set(f"{self.node_id}_Result", "", self.name)
            self.bridge.set(f"{self.node_id}_ActivePorts", ["Flow"], self.name)
            return True

        # Gather values
        values = {}
        if isinstance(items, dict):
            for k, v in items.items():
                values[str(k)] = v
                values[str(k).replace(" ", "_")] = v
                values[str(k).lower()] = v
                values[str(k).lower().replace(" ", "_")] = v
                
        # [NEW] Also check explicit dynamic inputs added via the context menu
        # This handles legacy "Additional Inputs" arrays and auto-wires them if present
        dynamic_inputs = self.properties.get("additional_inputs") or self.properties.get("Additional Inputs", [])
        if isinstance(dynamic_inputs, list):
            for pin_name in dynamic_inputs:
                if pin_name in kwargs and pin_name not in values:
                    val = kwargs[pin_name]
                    values[str(pin_name)] = val
                    values[str(pin_name).replace(" ", "_")] = val
                    values[str(pin_name).lower()] = val
                    values[str(pin_name).lower().replace(" ", "_")] = val

        # Apply safe formatting
        result = _safe_format(template, values)

        self.bridge.set(f"{self.node_id}_Result", result, self.name)
        self.bridge.set(f"{self.node_id}_ActivePorts", ["Flow"], self.name)
        return True
