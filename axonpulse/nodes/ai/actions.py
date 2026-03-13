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

import queue
import threading

@NodeRegistry.register('Ask AI', 'AI')
class AskAINode(SuperNode):
    """Sends a prompt to a connected AI Provider and retrieves the generated response.
Supports file attachments, system instructions, and structured JSON output.
Enhanced with "Thinking" and "Stream" flow outputs for real-time feedback.

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
- Error Flow: Triggered if the AI request or logic fails.
- Thinking: Flow pulsed when thinking/reasoning content is available.
- text: The current thinking text.
- Stream: Flow pulsed when a new chunk of the final response is available."""
    node_version = '2.4.0'

    def __init__(self, node_id, name, bridge):
        super().__init__(node_id, name, bridge)
        self.required_providers = ['AI']
        self._streaming_thread = None
        self._output_queue = queue.Queue()
        self._is_running = False
        self._full_response = ""
        self._thinking_content = ""
        self.define_schema()
        self.register_handlers()

    def define_schema(self):
        self.input_schema = {
            'Flow': DataType.FLOW,
            'User Prompt': DataType.STRING,
            'System Prompt': DataType.STRING,
            'Files': DataType.LIST,
            'Model': DataType.STRING,
            'Return As JSON': DataType.BOOLEAN
        }
        self.output_schema = {
            'Flow': DataType.FLOW,
            'Text': DataType.STRING,
            'JSON': DataType.DICT,
            'JSON Error': DataType.STRING,
            'Error Flow': DataType.FLOW,
            'Thinking': DataType.FLOW,
            'text': DataType.STRING,
            'Stream': DataType.FLOW
        }
        # Set defaults
        self.properties.setdefault('User Prompt', '')
        self.properties.setdefault('System Prompt', '')
        self.properties.setdefault('Files', [])
        self.properties.setdefault('Model', '')
        self.properties.setdefault('Return As JSON', False)

    def register_handlers(self):
        self.register_handler('Flow', self.do_work)

    def do_work(self, **kwargs):
        # Check if we are already running (continuation pulse)
        if self._is_running:
            return self._continue_streaming()

        # Initial trigger
        user_prompt = kwargs.get('User Prompt') or self.properties.get('User Prompt', '')
        system_prompt = kwargs.get('System Prompt') or self.properties.get('System Prompt', '')
        files = kwargs.get('Files') or self.properties.get('Files', [])
        model = kwargs.get('Model') or self.properties.get('Model', '')
        return_as_json = kwargs.get('Return As JSON', self.properties.get('Return As JSON', False))

        provider_id = self.get_provider_id('AI')
        provider = self.bridge.get(f'{provider_id}_Provider') if provider_id else None

        if not provider or not isinstance(provider, AIProvider):
            raise RuntimeError(f'[{self.name}] No AI Provider connected.')

        # 1. Capability Check
        caps = provider.get_capabilities(model_override=model)
        if files and not caps.get("vision", False):
            # Check if any of the files are images
            import mimetypes
            for f in (files if isinstance(files, list) else [files]):
                mime, _ = mimetypes.guess_type(str(f))
                if mime and mime.startswith("image"):
                    self.logger.warning(f"Model '{model}' does not support vision. Image ignored: {f}")

        # 2. Start Background Stream
        self._is_running = True
        self._full_response = ""
        self._thinking_content = ""
        while not self._output_queue.empty(): self._output_queue.get() # Clear queue

        self._streaming_thread = threading.Thread(
            target=self._run_at_provider,
            args=(provider, system_prompt, user_prompt, files, model, return_as_json),
            daemon=True
        )
        self._streaming_thread.start()

        # 3. Enter Wait Loop
        return ("_YSWAIT", 0)

    def _run_at_provider(self, provider, system_prompt, user_prompt, files, model, return_json):
        try:
            # We use the 'stream' method if it exists, else fallback to 'generate'
            if hasattr(provider, 'stream'):
                for chunk in provider.stream(system_prompt=system_prompt, user_prompt=user_prompt, files=files, model_override=model, return_json=return_json):
                    # Expecting chunk to be {"type": "thinking"|"content", "text": "..."} or just string
                    if isinstance(chunk, dict):
                        self._output_queue.put(chunk)
                    else:
                        self._output_queue.put({"type": "content", "text": chunk})
            else:
                res = provider.generate(system_prompt=system_prompt, user_prompt=user_prompt, files=files, model_override=model, return_json=return_json)
                self._output_queue.put({"type": "content", "text": res})
        except Exception as e:
            self.logger.error(f"Stream Error: {e}")
            self._output_queue.put({"type": "error", "text": str(e)})
        finally:
            self._is_running = False

    def _continue_streaming(self):
        # Drain the queue for this pulse
        packets = []
        try:
            while True:
                packets.append(self._output_queue.get_nowait())
        except queue.Empty:
            pass

        if not packets:
            if not self._is_running:
                # Thread finished and queue empty -> Finalize
                return self._finalize_response()
            return ("_YSWAIT", 50) # Nothing yet, wait a bit

        # Handle packets
        for pkt in packets:
            p_type = pkt.get("type")
            p_text = pkt.get("text", "")

            if p_type == "error":
                self.bridge.set(f'{self.node_id}_ActivePorts', ['Error Flow', 'Flow'], self.name)
                return True

            if p_type == "thinking":
                self._thinking_content += p_text
                self.set_output("text", self._thinking_content)
                self.bridge.set(f'{self.node_id}_ActivePorts', ['Thinking'], self.name)
                return ("_YSWAIT", 0, True) # Pulse 'Thinking'

            if p_type == "content":
                self._full_response += p_text
                self.set_output("Text", self._full_response)
                self.bridge.set(f'{self.node_id}_ActivePorts', ['Stream'], self.name)
                return ("_YSWAIT", 0, True) # Pulse 'Stream'

        return ("_YSWAIT", 0)

    def _finalize_response(self):
        return_as_json = self.properties.get('Return As JSON', False)
        data = {}
        je_str = "No JSON object found"
        
        if return_as_json:
            try:
                start = self._full_response.find('{')
                end = self._full_response.rfind('}') + 1
                if start != -1 and end != 0:
                    json_str = self._full_response[start:end]
                    data = json.loads(json_str)
                    je_str = ""
            except Exception as je:
                je_str = str(je)

        self.set_output("Text", self._full_response)
        self.set_output("JSON", data)
        self.set_output("JSON Error", je_str)
        self.bridge.set(f'{self.node_id}_ActivePorts', ['Flow'], self.name)
        return True


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
