from synapse.core.super_node import SuperNode
from synapse.nodes.registry import NodeRegistry
from synapse.core.types import DataType

# Lazy load BeautifulSoup
BeautifulSoup = None

def load_bs4():
    global BeautifulSoup
    if BeautifulSoup: return True
    try:
        from bs4 import BeautifulSoup as _B; BeautifulSoup = _B; return True
    except ImportError:
        return False

@NodeRegistry.register("HTML Strip Text", "Text")
class HTMLStripTextNode(SuperNode):
    """
    Strips raw HTML down to its inner plain text content using BeautifulSoup.
    
    Inputs:
    - Flow: Execution trigger.
    - HTML: The raw HTML string to process.
    
    Outputs:
    - Flow: Triggered after processing.
    - Text: The stripped plain text.
    """
    version = "1.0.0"

    def __init__(self, node_id, name, bridge):
        super().__init__(node_id, name, bridge)
        self.is_native = True
        self.define_schema()
        self.register_handlers()

    def define_schema(self):
        self.input_schema = {
            "Flow": DataType.FLOW,
            "HTML": DataType.STRING
        }
        self.output_schema = {
            "Flow": DataType.FLOW,
            "Text": DataType.STRING
        }

    def register_handlers(self):
        self.register_handler("Flow", self.strip_text)

    def strip_text(self, **kwargs):
        html_string = kwargs.get("HTML", "")
        
        if not html_string or not isinstance(html_string, str):
            self.set_output("Text", "")
            self.bridge.bubble_set(f"{self.node_id}_ActivePorts", ["Flow"], self.name)
            return True

        if not load_bs4():
            self.logger.error("BeautifulSoup4 is not installed. Returning original HTML.")
            self.set_output("Text", html_string)
            self.bridge.bubble_set(f"{self.node_id}_ActivePorts", ["Flow"], self.name)
            return True

        try:
            # Parse the HTML
            soup = BeautifulSoup(html_string, "html.parser")
            
            # Extract inner text cleanly:
            # - separator=" " ensures words from adjacent block tags don't mush together.
            # - strip=True removes leading/trailing whitespace around extracted fragments.
            clean_text = soup.get_text(separator=" ", strip=True)
            
            self.set_output("Text", clean_text)
            
        except Exception as e:
            self.logger.error(f"Failed to strip HTML text: {e}")
            self.set_output("Text", "")

        self.bridge.bubble_set(f"{self.node_id}_ActivePorts", ["Flow"], self.name)
        return True
