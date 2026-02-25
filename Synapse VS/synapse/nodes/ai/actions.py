import json
import math
import time
from synapse.core.super_node import SuperNode # Changed from BaseNode to SuperNode
from synapse.nodes.registry import NodeRegistry
from synapse.core.types import DataType
from .base import AIProvider

@NodeRegistry.register("Ask AI", "AI")
class AskNode(SuperNode):
    """
    Sends a prompt to a connected AI Provider and retrieves the generated response.
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
    - Error Flow: Triggered if the AI request or logic fails.
    """
    version = "2.1.0"

    def __init__(self, node_id, name, bridge):
        super().__init__(node_id, name, bridge)
        self.is_service = True 
        self.required_providers = ["AI"]
        
        self.properties["User Prompt"] = ""
        self.properties["System Prompt"] = ""
        self.properties["Files"] = []
        self.properties["Model"] = ""
        self.properties["Return As JSON"] = False
        
        self.define_schema()
        self.register_handlers()

    def define_schema(self):
        self.input_schema = {
            "Flow": DataType.FLOW,
            "User Prompt": DataType.STRING,
            "System Prompt": DataType.STRING,
            "Files": DataType.LIST,
            "Model": DataType.STRING,
            "Return As JSON": DataType.BOOLEAN
        }
        self.output_schema = {
            "Flow": DataType.FLOW,
            "Text": DataType.STRING,
            "JSON": DataType.DICT,
            "JSON Error": DataType.STRING,
            "Error Flow": DataType.FLOW
        }

    def register_handlers(self):
        self.register_handler("Flow", self.do_work)

    def do_work(self, **kwargs):
        user_prompt = kwargs.get("User Prompt") or self.properties.get("User Prompt", "")
        system_prompt = kwargs.get("System Prompt") or self.properties.get("System Prompt", "")
        files = kwargs.get("Files") or self.properties.get("Files", [])
        model = kwargs.get("Model") or self.properties.get("Model", "")
        return_as_json = kwargs.get("Return As JSON", self.properties.get("Return As JSON", False))

        provider_id = self.get_provider_id("AI")
        provider = self.bridge.get(f"{provider_id}_Provider") if provider_id else None

        if not provider or not isinstance(provider, AIProvider):
            raise RuntimeError(f"[{self.name}] No valid AI Provider connected.")

        try:
            response_text = provider.generate(
                system_prompt=system_prompt,
                user_prompt=user_prompt,
                files=files,
                model_override=model,
                return_json=return_as_json
            )
            
            self.bridge.set(f"{self.node_id}_Text", response_text, self.name)
            
            if return_as_json:
                try:
                    # JSON Extraction logic
                    start = response_text.find('{')
                    end = response_text.rfind('}') + 1
                    if start != -1 and end != 0:
                        json_str = response_text[start:end]
                        data = json.loads(json_str)
                        self.bridge.set(f"{self.node_id}_JSON", data, self.name)
                    else:
                         self.bridge.set(f"{self.node_id}_JSON Error", "No JSON object found", self.name)
                except Exception as je:
                    self.bridge.set(f"{self.node_id}_JSON Error", str(je), self.name)

            self.bridge.set(f"{self.node_id}_ActivePorts", ["Flow"], self.name)
        except Exception as e:
            self.logger.error(f"AI Error: {e}")
            self.bridge.set(f"{self.node_id}_ActivePorts", ["Error Flow", "Flow"], self.name)
        
        return True


@NodeRegistry.register("AI Models", "AI")
class AIModelsNode(SuperNode):
    """
    Retrieves the list of available models from the connected AI Provider.
    
    Inputs:
    - Flow: Trigger execution.
    
    Outputs:
    - Flow: Triggered after models are retrieved.
    - Models: A list containing the names or IDs of available models.
    - Count: The total number of available models found.
    """
    version = "2.1.0"

    def __init__(self, node_id, name, bridge):
        super().__init__(node_id, name, bridge)
        self.required_providers = ["AI"]
        self.define_schema()
        self.register_handlers()

    def register_handlers(self):
        self.register_handler("Flow", self.do_work)

    def define_schema(self):
        self.input_schema = {
            "Flow": DataType.FLOW
        }
        self.output_schema = {
            "Flow": DataType.FLOW,
            "Models": DataType.LIST,
            "Count": DataType.INTEGER
        }

    def do_work(self, **kwargs):
        provider_id = self.get_provider_id("AI")
        provider = self.bridge.get(f"{provider_id}_Provider") if provider_id else None

        if not provider or not isinstance(provider, AIProvider):
            raise RuntimeError(f"[{self.name}] No valid AI Provider connected.")

        models = provider.get_models()
        self.bridge.set(f"{self.node_id}_Models", models, self.name)
        self.bridge.set(f"{self.node_id}_Count", len(models), self.name)
        self.bridge.set(f"{self.node_id}_ActivePorts", ["Flow"], self.name)
        return True

@NodeRegistry.register("Token Counter", "AI")
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
    version = "2.1.0"

    def __init__(self, node_id, name, bridge):
        super().__init__(node_id, name, bridge)
        self.required_providers = ["AI"]
        self.properties["String"] = ""
        self.define_schema()
        self.register_handlers()

    def register_handlers(self):
        self.register_handler("Flow", self.do_work)

    def define_schema(self):
        self.input_schema = {
            "Flow": DataType.FLOW,
            "String": DataType.STRING
        }
        self.output_schema = {
            "Flow": DataType.FLOW,
            "Count": DataType.INTEGER
        }

    def do_work(self, **kwargs):
        string_val = kwargs.get("String") or self.properties.get("String") or ""
        
        provider_id = self.get_provider_id("AI")
        provider = self.bridge.get(f"{provider_id}_Provider") if provider_id else None
        
        count = 0
        
        if provider:
            if not hasattr(provider, 'count_tokens'):
                raise RuntimeError(f"[{self.name}] AI Provider does not support token counting.")
            try:
                count = provider.count_tokens(str(string_val))
            except:
                count = self.fallback_heuristic(str(string_val))
        else:
            count = self.fallback_heuristic(str(string_val))

        self.bridge.set(f"{self.node_id}_Count", count, self.name)
        self.bridge.set(f"{self.node_id}_ActivePorts", ["Flow"], self.name)
        return True

    def fallback_heuristic(self, text):
        if not text: return 0
        spaces = text.count(' ')
        tabs = text.count('\t')
        newlines = text.count('\n') + text.count('\r')
        symbols = sum(1 for char in text if not char.isalnum() and char not in ' \t\n\r')
        char_logic_count = spaces + tabs + newlines + symbols
        estimated_tokens = math.ceil(len(text) / 3.5)
        return max(char_logic_count, estimated_tokens)

