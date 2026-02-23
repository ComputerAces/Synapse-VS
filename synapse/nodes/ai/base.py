from synapse.core.node import BaseNode
from synapse.core.types import DataType
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
