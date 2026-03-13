import re

from axonpulse.core.super_node import SuperNode

from axonpulse.nodes.registry import NodeRegistry

from axonpulse.core.types import DataType

from typing import Any, List, Dict, Optional

from axonpulse.core.types import DataType, TypeCaster

from axonpulse.nodes.decorators import axon_node

'\nTemplate Injector Node.\n\nBridges raw data and professional output using string templates.\nSupports dynamic input ports.\nUses safe formatting that leaves unknown placeholders intact.\n'

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
        return match.group(0)
    return re.sub('\\{(\\w+)\\}', replacer, template)

@axon_node(category="Data/Strings", version="2.3.0", node_label="Template Injector")
def TemplateInjectorNode(Input_Items: dict, Template: str = 'Hello {name}, your ID is {id}.', _bridge: Any = None, _node: Any = None, _node_id: str = None, **kwargs) -> Any:
    """Injects values into a string template using placeholders like {name} or {id}.

Inputs:
- Flow: Execution trigger.
- Template: The string template containing {key} placeholders.
- Input Items: A dictionary of key-value pairs to inject into the template.

Outputs:
- Flow: Triggered after the injection is complete.
- Result: The formatted string with placeholders replaced."""
    template = Template if Template is not None else kwargs.get('Template') or _node.properties.get('Template', '')
    items = kwargs.get('Input Items') or {}
    if not template:
        _node.logger.warning('Empty template.')
        _bridge.set(f'{_node_id}_ActivePorts', ['Flow'], _node.name)
    else:
        pass
    values = {}
    if isinstance(items, dict):
        for (k, v) in items.items():
            values[str(k)] = v
            values[str(k).replace(' ', '_')] = v
            values[str(k).lower()] = v
            values[str(k).lower().replace(' ', '_')] = v
    else:
        pass
    dynamic_inputs = _node.properties.get('Additional Inputs', [])
    if isinstance(dynamic_inputs, list):
        for pin_name in dynamic_inputs:
            if pin_name in kwargs and pin_name not in values:
                val = kwargs[pin_name]
                values[str(pin_name)] = val
                values[str(pin_name).replace(' ', '_')] = val
                values[str(pin_name).lower()] = val
                values[str(pin_name).lower().replace(' ', '_')] = val
            else:
                pass
    else:
        pass
    result = _safe_format(template, values)
    _bridge.set(f'{_node_id}_ActivePorts', ['Flow'], _node.name)
    return result
