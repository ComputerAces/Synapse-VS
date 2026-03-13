import urllib.request
import json
import os
import base64
import mimetypes
from axonpulse.nodes.registry import NodeRegistry
from axonpulse.core.types import DataType
from axonpulse.nodes.lib.provider_node import ProviderNode
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
        
        contents = []
        text_context = ""
        parts = [{"text": user_prompt}]
        
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
                        text_context += f"\n--- File: {os.path.basename(f)} ---\n{tf.read()}\n"

        if text_context: parts[0]["text"] += f"\n\nContext Files:{text_context}"
        contents.append({"role": "user", "parts": parts})

        payload = {"contents": contents}
        if system_prompt:
            payload["system_instruction"] = {"parts": [{"text": system_prompt}]}
            
        req = urllib.request.Request(url, data=json.dumps(payload).encode('utf-8'))
        req.add_header('Content-Type', 'application/json')
        
        with urllib.request.urlopen(req) as response:
            # Gemini returns a JSON array of candidates in chunks
            # Note: For simplicity and since we are using standard urllib, we read the whole response
            # then yield chunks. Real-time streaming would require a different approach for chunks.
            # But the logic below follows the yielding pattern expected by AskAINode.
            raw_data = response.read().decode('utf-8')
            try:
                data_list = json.loads(raw_data)
                for chunk in data_list:
                    for candidate in chunk.get("candidates", []):
                        for part in candidate.get("content", {}).get("parts", []):
                            text = part.get("text", "")
                            if "thought" in part:
                                yield {"type": "thinking", "text": part["thought"]}
                            
                            if text:
                                if "<think>" in text and "</think>" in text:
                                    parts = text.split("<think>")
                                    if parts[0]: yield {"type": "content", "text": parts[0]}
                                    mid = parts[1].split("</think>")
                                    yield {"type": "thinking", "text": mid[0]}
                                    if mid[1]: yield {"type": "content", "text": mid[1]}
                                elif "<think>" in text:
                                    parts = text.split("<think>")
                                    if parts[0]: yield {"type": "content", "text": parts[0]}
                                    yield {"type": "thinking", "text": parts[1]}
                                elif "</think>" in text:
                                    parts = text.split("</think>")
                                    yield {"type": "thinking", "text": parts[0]}
                                    if parts[1]: yield {"type": "content", "text": parts[1]}
                                else:
                                    yield {"type": "content", "text": text}
            except Exception as e:
                self.logger.error(f"Gemini Streaming Parse Error: {e}")
                try:
                    data = json.loads(raw_data)
                    text = data['candidates'][0]['content']['parts'][0]['text']
                    yield {"type": "content", "text": text}
                except:
                    pass

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

    def get_capabilities(self, model_override=None):
        model = (model_override if model_override else self.model).lower()
        caps = {"completion": True, "vision": False, "tools": True, "thinking": False}
        
        # Gemini 1.5+ generally all support vision
        if "gemini-1.5" in model or "gemini-pro-vision" in model or "gemini-2.0" in model:
            caps["vision"] = True
        
        if "thinking" in model:
            caps["thinking"] = True
            
        return caps

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
    version = "2.3.0"

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

