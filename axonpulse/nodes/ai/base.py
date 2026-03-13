from axonpulse.core.node import BaseNode
from axonpulse.core.types import DataType
import math

class AIProvider:
    """Base interface for AI service objects."""
    def __init__(self):
        import uuid
        self.lock_id = str(uuid.uuid4())

    def generate(self, system_prompt, user_prompt, files, model_override=None, **kwargs):
        """Standard generation method."""
        raise NotImplementedError()

    def stream(self, system_prompt, user_prompt, files, model_override=None, **kwargs):
        """Yields chunks of generated text."""
        raise NotImplementedError()

    def count_tokens(self, text, model_override=None):
        """Calculates token count using fallback heuristic."""
        if not text: return 0
        spaces = text.count(' ')
        tabs = text.count('\t')
        newlines = text.count('\n') + text.count('\r')
        
        symbols = 0
        for char in text:
            if not char.isalnum() and char not in ' \t\n\r':
                symbols += 1

        char_logic_count = spaces + tabs + newlines + symbols
        estimated_tokens = math.ceil(len(text) / 3.5)
        return max(char_logic_count, estimated_tokens)

    def get_models(self):
        """Returns list of available models."""
        return []

    def get_capabilities(self, model_override=None):
        """
        Returns a dictionary of supported features for the selected model.
        Default assumes text completion only.
        """
        return {
            "completion": True,
            "vision": False,
            "tools": False,
            "thinking": False
        }

    def stream(self, system_prompt, user_prompt, files, model_override=None, **kwargs):
        """
        Default streaming implementation that falls back to non-streaming generation.
        Returns a generator yielding a single content chunk.
        """
        res = self.generate(system_prompt, user_prompt, files, model_override, **kwargs)
        yield {"type": "content", "text": res}
