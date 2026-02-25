import urllib.request
import json
import os
import base64
import mimetypes
from synapse.nodes.registry import NodeRegistry
from synapse.core.types import DataType
from synapse.nodes.lib.provider_node import ProviderNode
from .base import AIProvider

JSON_GBNF = r"""
root   ::= object
value  ::= object | array | string | number | ("true" | "false" | "null") ws

object ::=
  "{" ws (
            string ":" ws value
    ("," ws string ":" ws value)*
  )? "}" ws

array  ::=
  "[" ws (
            value
    ("," ws value)*
  )? "]" ws

string ::=
  "\"" (
    [^"\\] |
    "\\" (["\\/bfnrt] | "u" [0-9a-fA-F] [0-9a-fA-F] [0-9a-fA-F] [0-9a-fA-F]) # escapes
  )* "\"" ws

number ::= ("-"? ([0-9] | [1-9] [0-9]*)) ("." [0-9]+)? ([eE] [-+]? [0-9]+)? ws

# Optional space: by convention, applied in this grammar after literal chars when allowed
ws ::= ([ \t\n] | [ \r])*
"""

class OllamaProvider(AIProvider):
    """
    Internal abstraction for locally hosted Ollama model communication.
    Supports GBNF grammars for structured JSON output and multi-modal image context.
    """
    def __init__(self, host, default_model, temperature):
        super().__init__()
        self.host = host
        self.default_model = default_model
        self.temperature = temperature

    def generate(self, system_prompt, user_prompt, files, model_override=None, **kwargs):
        model = model_override if model_override else self.default_model
        return_json = kwargs.get("return_json", False)
        
        images_b64 = []
        text_context = ""
        if isinstance(files, str): files = [files]
        if files:
            for f in files:
                if not f or not os.path.exists(f): continue
                mime, _ = mimetypes.guess_type(f)
                if mime and mime.startswith("image"):
                    with open(f, "rb") as im:
                        images_b64.append(base64.b64encode(im.read()).decode('utf-8'))
                else:
                    with open(f, "r", encoding="utf-8", errors="ignore") as tf:
                        text_context += f"\n--- File: {os.path.basename(f)} ---\n{tf.read()}\n"

        messages = []
        if system_prompt: messages.append({"role": "system", "content": system_prompt})
        
        content = user_prompt
        if text_context: content += f"\n\nContext Files:{text_context}"
        
        user_msg = {"role": "user", "content": content}
        if images_b64: user_msg["images"] = images_b64
        messages.append(user_msg)

        payload = {
            "model": model,
            "messages": messages,
            "stream": False,
            "options": {"temperature": self.temperature}
        }
        
        if return_json:
            payload["format"] = "json"
            payload["options"]["grammar"] = JSON_GBNF
        
        req = urllib.request.Request(f"{self.host}/api/chat", data=json.dumps(payload).encode('utf-8'))
        req.add_header('Content-Type', 'application/json')
        
        with urllib.request.urlopen(req) as response:
            res = json.loads(response.read().decode('utf-8'))
            return res.get("message", {}).get("content", "")

    def get_models(self):
        url = f"{self.host}/api/tags"
        req = urllib.request.Request(url)
        with urllib.request.urlopen(req) as response:
            data = json.loads(response.read().decode('utf-8'))
            return [m['name'] for m in data.get('models', [])]

@NodeRegistry.register("Ollama Provider", "AI/Providers")
class OllamaProviderNode(ProviderNode):
    """
    Service provider for locally hosted Ollama AI models.
    Registers an AI capability scope for 'Ask AI' and other consumer nodes.
    
    Inputs:
    - Flow: Start the local service connection and enter the AI scope.
    - Provider End: Close the connection and exit the scope.
    - Host: URL of the Ollama API (default: http://localhost:11434).
    - Model: The Ollama model name to use (default: llama3).
    - Temperature: Creativity setting for the model (0.0 to 1.0).
    
    Outputs:
    - Provider Flow: Active while the provider service is running.
    - Provider ID: Unique ID for this specific provider instance.
    - Flow: Triggered when the service is stopped.
    """
    version = "2.1.0"

    def __init__(self, node_id, name, bridge):
        super().__init__(node_id, name, bridge)
        self.provider_type = "AI"
        self.properties["Host"] = "http://localhost:11434"
        self.properties["Model"] = "llama3"
        self.properties["Temperature"] = 0.7
        self.define_schema()
        self.register_handlers()

    def define_schema(self):
        super().define_schema()
        self.input_schema.update({
            "Model": DataType.STRING
        })

    def start_scope(self, **kwargs):
        # Fallback with legacy support
        host = self.properties.get("Host", "http://localhost:11434")
        model = kwargs.get("Model") or self.properties.get("Model", "llama3")
        temp = float(self.properties.get("Temperature", 0.7))
        
        provider = OllamaProvider(host, model, temp)
        
        # Register the provider instance in the bridge so consumers can find it
        self.bridge.set(f"context_provider_{self.provider_type}", provider, self.name)
        
        return super().start_scope(**kwargs)

