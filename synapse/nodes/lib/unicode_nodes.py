from synapse.core.super_node import SuperNode
from synapse.nodes.registry import NodeRegistry
from synapse.core.types import DataType
import codecs
import re

@NodeRegistry.register("Unicode To Text", "Data/Strings")
class UnicodeToTextNode(SuperNode):
    """
    Converts a string containing literal escaped unicode sequences (e.g. \\u00a0) into standard readable text.
    
    Inputs:
    - Flow: Execution trigger.
    - Text: The string containing escaped unicode sequences.
    
    Outputs:
    - Flow: Triggered after conversion.
    - Error Flow: Triggered if conversion fails.
    - Result: The decoded, human-readable string.
    """
    version = "2.1.0"

    def __init__(self, node_id, name, bridge):
        super().__init__(node_id, name, bridge)
        self.is_native = True
        self.define_schema()
        self.register_handlers()

    def define_schema(self):
        self.input_schema = {
            "Flow": DataType.FLOW,
            "Text": DataType.STRING
        }
        self.output_schema = {
            "Flow": DataType.FLOW,
            "Error Flow": DataType.FLOW,
            "Result": DataType.STRING
        }

    def register_handlers(self):
        self.register_handler("Flow", self.convert)

    def convert(self, Text=None, **kwargs):
        val = Text if Text is not None else kwargs.get("Text", "")
        if val is None:
            val = ""
            
        try:
            # We first try the native Python codecs decoder for clean, entire-string escapes
            result = codecs.decode(str(val), 'unicode_escape')
        except Exception as e:
            self.logger.warning(f"Native unicode decode failed: {e}. Falling back to robust regex matching.")
            try:
                # Fallback: Manually find and replace \uXXXX and basic escapes without failing on trailing slashes
                s = str(val)
                # Handle \uXXXX sequences
                s = re.sub(
                    r'\\u([0-9a-fA-F]{4})',
                    lambda m: chr(int(m.group(1), 16)),
                    s
                )
                # Handle \xXX hexadecimal sequences
                s = re.sub(
                    r'\\x([0-9a-fA-F]{2})',
                    lambda m: chr(int(m.group(1), 16)),
                    s
                )
                # Handle basic textual escapes
                s = s.replace('\\n', '\n').replace('\\t', '\t').replace('\\r', '\r')
                result = s
            except Exception as inner_e:
                self.logger.error(f"Fallback unicode parsing failed: {inner_e}")
                self.bridge.set(f"{self.node_id}_ActivePorts", ["Error Flow"], self.name)
                return True

        self.bridge.set(f"{self.node_id}_Result", result, self.name)
        self.bridge.set(f"{self.node_id}_ActivePorts", ["Flow"], self.name)
        return True

@NodeRegistry.register("Text To Unicode", "Data/Strings")
class TextToUnicodeNode(SuperNode):
    """
    Converts standard readable text into a string containing literal escaped unicode sequences.
    
    Inputs:
    - Flow: Execution trigger.
    - Text: The standard human-readable string.
    
    Outputs:
    - Flow: Triggered after conversion.
    - Error Flow: Triggered if conversion fails.
    - Result: The string containing literal unicode escapes.
    """
    version = "2.1.0"

    def __init__(self, node_id, name, bridge):
        super().__init__(node_id, name, bridge)
        self.is_native = True
        self.define_schema()
        self.register_handlers()

    def define_schema(self):
        self.input_schema = {
            "Flow": DataType.FLOW,
            "Text": DataType.STRING
        }
        self.output_schema = {
            "Flow": DataType.FLOW,
            "Error Flow": DataType.FLOW,
            "Result": DataType.STRING
        }

    def register_handlers(self):
        self.register_handler("Flow", self.convert)

    def convert(self, Text=None, **kwargs):
        val = Text if Text is not None else kwargs.get("Text", "")
        if val is None:
            val = ""
            
        try:
            # We use encode('unicode_escape') to convert literal chars to things like \u00a0
            # Then decode bounds it back into a valid python string format
            result = str(val).encode("unicode_escape").decode("utf-8")
            self.bridge.set(f"{self.node_id}_Result", result, self.name)
            self.bridge.set(f"{self.node_id}_ActivePorts", ["Flow"], self.name)
        except Exception as e:
            self.logger.error(f"Failed to encode unicode: {e}")
            self.bridge.set(f"{self.node_id}_ActivePorts", ["Error Flow"], self.name)
            
        return True
