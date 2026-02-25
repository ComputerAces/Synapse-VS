import urllib.request
import json
import os
import base64
import mimetypes
from synapse.nodes.registry import NodeRegistry
from synapse.core.types import DataType
from synapse.nodes.lib.provider_node import ProviderNode
from .base import AIProvider

class OpenAIProvider(AIProvider):
    """
    Internal abstraction for OpenAI model communication.
    Handles text generation, image context processing, and token counting.
    """
    def __init__(self, api_key, model, base_url):
        super().__init__()
        self.api_key = api_key
        self.model = model
        self.base_url = base_url

    def generate(self, system_prompt, user_prompt, files, model_override=None, **kwargs):
        model = model_override if model_override else self.model
        url = f"{self.base_url}/chat/completions"
        
        content_block = [{"type": "text", "text": user_prompt}]
        text_context = ""
        if isinstance(files, str): files = [files]
        if files:
            for f in files:
                if not f or not os.path.exists(f): continue
                mime, _ = mimetypes.guess_type(f)
                if mime and mime.startswith("image"):
                     with open(f, "rb") as im:
                         b64_data = base64.b64encode(im.read()).decode('utf-8')
                         data_url = f"data:{mime};base64,{b64_data}"
                         content_block.append({"type": "image_url", "image_url": {"url": data_url}})
                else:
                    with open(f, "r", encoding="utf-8", errors="ignore") as tf:
                        text_context += f"\n--- File: {os.path.basename(f)} ---\n{tf.read()}\n"
        
        if text_context: content_block[0]["text"] += f"\n\nContext Files:{text_context}"

        messages = []
        if system_prompt: messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": content_block})
        
        payload = {"model": model, "messages": messages, "stream": False}
        
        req = urllib.request.Request(url, data=json.dumps(payload).encode('utf-8'))
        req.add_header('Content-Type', 'application/json')
        req.add_header('Authorization', f'Bearer {self.api_key}')
        
        with urllib.request.urlopen(req) as response:
            res = json.loads(response.read().decode('utf-8'))
            return res['choices'][0]['message']['content']

    def stream(self, system_prompt, user_prompt, files, model_override=None, **kwargs):
        yield "OpenAI streaming implementation..."

    def count_tokens(self, text, model_override=None):
        try:
            import tiktoken
            model = model_override if model_override else self.model
            encoding = tiktoken.encoding_for_model(model)
            return len(encoding.encode(text))
        except:
            return super().count_tokens(text)

    def get_models(self):
        url = f"{self.base_url}/models"
        req = urllib.request.Request(url)
        req.add_header('Authorization', f'Bearer {self.api_key}')
        with urllib.request.urlopen(req) as response:
            data = json.loads(response.read().decode('utf-8'))
            return [m['id'] for m in data.get('data', [])]

@NodeRegistry.register("OpenAI Provider", "AI/Providers")
class OpenAIProviderNode(ProviderNode):
    """
    Service provider for OpenAI's GPT models (or OpenAI-compatible APIs).
    Registers an AI capability scope for 'Ask AI' and other consumer nodes.
    
    Inputs:
    - Flow: Start the provider service and enter the AI scope.
    - Provider End: Close the provider service and exit the scope.
    - API Key: Your OpenAI API Key.
    - Model: The GPT model ID to use (default: gpt-4o).
    - Base URL: The API endpoint URL (allows usage with local models like LM Studio).
    
    Outputs:
    - Provider Flow: Active while the provider service is running.
    - Provider ID: Unique ID for this specific provider instance.
    - Flow: Triggered when the service is stopped.
    """
    version = "2.1.0"

    def __init__(self, node_id, name, bridge):
        super().__init__(node_id, name, bridge)
        self.provider_type = "AI"
        self.properties["API Key"] = ""
        self.properties["Model"] = "gpt-4o"
        self.properties["Base URL"] = "https://api.openai.com/v1"
        self.define_schema()
        self.register_handlers()

    def define_schema(self):
        super().define_schema()
        self.input_schema.update({
            "API Key": DataType.STRING,
            "Model": DataType.STRING,
            "Base URL": DataType.STRING
        })

    def start_scope(self, **kwargs):
        api_key = kwargs.get("API Key") or self.properties.get("API Key", os.environ.get("OPENAI_API_KEY"))
        model = kwargs.get("Model") or self.properties.get("Model")
        base_url = kwargs.get("Base URL") or self.properties.get("Base URL", "https://api.openai.com/v1")
        
        provider = OpenAIProvider(api_key, model, base_url)
        self.bridge.set(f"{self.node_id}_Provider", provider, self.name)
        self.bridge.set(f"{self.node_id}_Provider ID", self.node_id, self.name)
        
        # Call base start_scope to handle flow
        return super().start_scope(**kwargs)

