import re

# Colors for ASCII
class Colors:
    GREEN = '\033[92m'
    CYAN = '\033[96m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    GRAY = '\033[90m'
    MAGENTA = '\033[95m'
    RESET = '\033[0m'
    BOLD = '\033[1m'
    BLACK = '\033[30m'
    BG_YELLOW = '\033[43m'

# TitleCase Validator
NAMING_PATTERN = re.compile(r'^[A-Z][a-zA-Z0-9]*(\s+[A-Z0-9][a-zA-Z0-9\(\)%/]*)*$')

class DummyBridge:
    def __init__(self):
         self._store = {}
    def get(self, key, default=None): return self._store.get(key, default)
    def set(self, key, value, source="System"): self._store[key] = value
    def get_hijack_handler(self, context_stack, node_type): return None

def requires_provider(node_inst):
    for key, typ in node_inst.input_schema.items():
        k = key.lower()
        if "provider" in k or "connection" in k or "client" in k or "session" in k or "sql" in k:
            return True
    return False
