import urllib.request
import json
import os
import base64
import mimetypes
from synapse.nodes.registry import NodeRegistry
from synapse.core.types import DataType
from synapse.nodes.lib.provider_node import ProviderNode
from .base import AIProvider

class GeminiProvider(AIProvider):
    """
    Internal abstraction for Google Gemini model communication.
    Handles multi-modal content generation and token estimation.
    """
    def __init__(self, api_key, model):
        super().__init__()
        self.api_key = api_key
        self.model = model

    def generate(self, system_prompt, user_prompt, files, model_override=None, **kwargs):
        model = model_override if model_override else self.model
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={self.api_key}"
        
        parts = []
        if system_prompt:
             parts.append({"text": f"System Instruction: {system_prompt}\n\n"})

        if isinstance(files, str): files = [files]
        if files:
            for f in files:
                if not f or not os.path.exists(f): continue
                mime, _ = mimetypes.guess_type(f)
                if mime and mime.startswith("image"):
                     with open(f, "rb") as im:
                         b64_data = base64.b64encode(im.read()).decode('utf-8')
                         parts.append({"inline_data": {"mime_type": mime, "data": b64_data}})
                else:
                    with open(f, "r", encoding="utf-8", errors="ignore") as tf:
                        parts.append({"text": f"\n--- File: {os.path.basename(f)} ---\n{tf.read()}\n"})

        parts.append({"text": user_prompt})
        payload = {"contents": [{"parts": parts}]}
        
        if "VALID JSON object" in user_prompt:
            payload["generationConfig"] = {"response_mime_type": "application/json"}
        
        req = urllib.request.Request(url, data=json.dumps(payload).encode('utf-8'))
        req.add_header('Content-Type', 'application/json')
        
        with urllib.request.urlopen(req) as response:
            res = json.loads(response.read().decode('utf-8'))
            try:
                return res['candidates'][0]['content']['parts'][0]['text']
            except:
                return str(res)

    def stream(self, system_prompt, user_prompt, files, model_override=None, **kwargs):
        model = model_override if model_override else self.model
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:streamGenerateContent?key={self.api_key}"
        yield "Gemini streaming implementation..."

    def count_tokens(self, text, model_override=None):
        model = model_override if model_override else self.model
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:countTokens?key={self.api_key}"
        try:
            payload = {"contents": [{"parts": [{"text": text}]}]}
            req = urllib.request.Request(url, data=json.dumps(payload).encode('utf-8'))
            req.add_header('Content-Type', 'application/json')
            with urllib.request.urlopen(req) as response:
                res = json.loads(response.read().decode('utf-8'))
                return res.get('totalTokens', 0)
        except:
            return super().count_tokens(text)

    def get_models(self):
        url = f"https://generativelanguage.googleapis.com/v1beta/models?key={self.api_key}"
        req = urllib.request.Request(url)
        with urllib.request.urlopen(req) as response:
            data = json.loads(response.read().decode('utf-8'))
            return [m['name'].split('/')[-1] for m in data.get('models', []) if 'generateContent' in m.get('supportedGenerationMethods', [])]

@NodeRegistry.register("Gemini Provider", "AI/Providers")
class GeminiProviderNode(ProviderNode):
    """
    Service provider for Google's Gemini AI models.
    Registers an AI capability scope for 'Ask AI' and other consumer nodes.
    
    Inputs:
    - Flow: Start the provider service and enter the AI scope.
    - Provider End: Close the provider service and exit the scope.
    - API Key: Your Google Gemini API Key.
    - Model: The Gemini model ID to use (default: gemini-1.5-pro).
    
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
        self.properties["Model"] = "gemini-1.5-pro"
        self.define_schema()
        self.register_handlers()
        
    def define_schema(self):
        super().define_schema()
        self.input_schema.update({
            "API Key": DataType.STRING,
            "Model": DataType.STRING
        })

    def start_scope(self, **kwargs):
        api_key = kwargs.get("API Key") or self.properties.get("API Key", os.environ.get("GEMINI_API_KEY"))
        model = kwargs.get("Model") or self.properties.get("Model", self.properties.get("Model"))
        
        provider = GeminiProvider(api_key, model)
        self.bridge.set(f"{self.node_id}_Provider", provider, self.name)
        
        # Register for Ask AI nodes to find
        self.bridge.set(f"{self.node_id}_Provider ID", self.node_id, self.name)
        
        # Call base start_scope to handle flow
        return super().start_scope(**kwargs)

