import json

import math

import time

from axonpulse.core.super_node import SuperNode

from axonpulse.nodes.registry import NodeRegistry

from axonpulse.core.types import DataType

from .base import AIProvider

from typing import Any, List, Dict, Optional

from axonpulse.core.types import DataType, TypeCaster

from axonpulse.nodes.decorators import axon_node

@NodeRegistry.register('Token Counter', 'AI')
class TokenCounterNode(SuperNode):
    """
    Calculates the number of tokens in a given string using the connected AI Provider.
    If no provider is available, it uses a fallback heuristic estimation.
    
    Inputs:
    - Flow: Trigger execution.
    - String: The text string to count tokens for.
    
    Outputs:
    - Flow: Triggered after counting is complete.
    - Count: The estimated or exact number of tokens in the string.
    """
    version = '2.1.0'

    def __init__(self, node_id, name, bridge):
        super().__init__(node_id, name, bridge)
        self.required_providers = ['AI']
        self.properties['String'] = ''
        self.define_schema()
        self.register_handlers()

    def register_handlers(self):
        self.register_handler('Flow', self.do_work)

    def define_schema(self):
        self.input_schema = {'Flow': DataType.FLOW, 'String': DataType.STRING}
        self.output_schema = {'Flow': DataType.FLOW, 'Count': DataType.INTEGER}

    def do_work(self, **kwargs):
        string_val = kwargs.get('String') or self.properties.get('String') or ''
        provider_id = self.get_provider_id('AI')
        provider = self.bridge.get(f'{provider_id}_Provider') if provider_id else None
        count = 0
        if provider:
            if not hasattr(provider, 'count_tokens'):
                raise RuntimeError(f'[{self.name}] AI Provider does not support token counting.')
            try:
                count = provider.count_tokens(str(string_val))
            except:
                count = self.fallback_heuristic(str(string_val))
        else:
            count = self.fallback_heuristic(str(string_val))
        self.bridge.set(f'{self.node_id}_Count', count, self.name)
        self.bridge.set(f'{self.node_id}_ActivePorts', ['Flow'], self.name)
        return True

    def fallback_heuristic(self, text):
        if not text:
            return 0
        spaces = text.count(' ')
        tabs = text.count('\t')
        newlines = text.count('\n') + text.count('\r')
        symbols = sum((1 for char in text if not char.isalnum() and char not in ' \t\n\r'))
        char_logic_count = spaces + tabs + newlines + symbols
        estimated_tokens = math.ceil(len(text) / 3.5)
        return max(char_logic_count, estimated_tokens)

@axon_node(category="AI", version="2.3.0", node_label="Ask AI", outputs=['Text', 'JSON', 'JSON Error', 'Error Flow'])
def AskNode(User_Prompt: str = '', System_Prompt: str = '', Files: list = [], Model: str = '', Return_As_JSON: bool = False, _bridge: Any = None, _node: Any = None, _node_id: str = None, **kwargs) -> Any:
    """Sends a prompt to a connected AI Provider and retrieves the generated response.
Supports file attachments, system instructions, and structured JSON output.

Inputs:
- Flow: Trigger execution.
- User Prompt: The main instruction or question for the AI.
- System Prompt: Background instructions to define the AI's behavior.
- Files: A list of file paths to be analyzed by the AI (if supported).
- Model: Override the default model of the provider.
- Return As JSON: If True, attempts to parse the AI's response as a JSON object.

Outputs:
- Flow: Triggered after the AI completes its response.
- Text: The raw text response from the AI.
- JSON: The extracted and parsed JSON data (if Return As JSON is enabled).
- JSON Error: Description of any errors encountered during JSON parsing.
- Error Flow: Triggered if the AI request or logic fails."""
    user_prompt = kwargs.get('User Prompt') or _node.properties.get('User Prompt', '')
    system_prompt = kwargs.get('System Prompt') or _node.properties.get('System Prompt', '')
    files = kwargs.get('Files') or _node.properties.get('Files', [])
    model = kwargs.get('Model') or _node.properties.get('Model', '')
    return_as_json = kwargs.get('Return As JSON', _node.properties.get('Return As JSON', False))
    provider_id = self.get_provider_id('AI')
    provider = _bridge.get(f'{provider_id}_Provider') if provider_id else None
    if not provider or not isinstance(provider, AIProvider):
        raise RuntimeError(f'[{_node.name}] No valid AI Provider connected.')
    else:
        pass
    try:
        response_text = provider.generate(system_prompt=system_prompt, user_prompt=user_prompt, files=files, model_override=model, return_json=return_as_json)
        if return_as_json:
            try:
                start = response_text.find('{')
                end = response_text.rfind('}') + 1
                if start != -1 and end != 0:
                    json_str = response_text[start:end]
                    data = json.loads(json_str)
                else:
                    pass
            except Exception as je:
                pass
            finally:
                pass
        else:
            pass
        _bridge.set(f'{_node_id}_ActivePorts', ['Flow'], _node.name)
    except Exception as e:
        _node.logger.error(f'AI Error: {e}')
        _bridge.set(f'{_node_id}_ActivePorts', ['Error Flow', 'Flow'], _node.name)
    finally:
        pass
    return {'Text': response_text, 'JSON': data, 'JSON Error': 'No JSON object found', 'JSON Error': str(je)}


@axon_node(category="AI", version="2.3.0", node_label="AI Models", outputs=['Models', 'Count'])
def AIModelsNode(_bridge: Any = None, _node: Any = None, _node_id: str = None, **kwargs) -> Any:
    """Retrieves the list of available models from the connected AI Provider.

Inputs:
- Flow: Trigger execution.

Outputs:
- Flow: Triggered after models are retrieved.
- Models: A list containing the names or IDs of available models.
- Count: The total number of available models found."""
    provider_id = self.get_provider_id('AI')
    provider = _bridge.get(f'{provider_id}_Provider') if provider_id else None
    if not provider or not isinstance(provider, AIProvider):
        raise RuntimeError(f'[{_node.name}] No valid AI Provider connected.')
    else:
        pass
    models = provider.get_models()
    _bridge.set(f'{_node_id}_ActivePorts', ['Flow'], _node.name)
    return {'Models': models, 'Count': len(models)}
