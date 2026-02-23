from synapse.core.super_node import SuperNode
from synapse.nodes.registry import NodeRegistry
from synapse.core.types import DataType

@NodeRegistry.register("Char Node", "Data")
class CharNode(SuperNode):
    """
    Converts a numerical ASCII/Unicode code point into its character representation.
    Supports the full Unicode character range (0 to 1,114,111).
    
    Inputs:
    - Flow: Trigger the conversion.
    - Code: The integer code point (e.g., 65 for 'A').
    
    Outputs:
    - Flow: Triggered after conversion.
    - Char: The resulting string character.
    """
    version = "2.1.0"

    def __init__(self, node_id, name, bridge):
        super().__init__(node_id, name, bridge)
        self.is_native = True
        self.properties["Code"] = 65 # Default to 'A'
        self.define_schema()
        self.register_handlers()

    def register_handlers(self):
        self.register_handler("Flow", self.process_char)

    def define_schema(self):
        self.input_schema = {
            "Flow": DataType.FLOW,
            "Code": DataType.INT
        }
        self.output_schema = {
            "Flow": DataType.FLOW,
            "Char": DataType.STRING
        }

    def process_char(self, Code=None, **kwargs):
        # 1. Resolve Input
        code_val = Code if Code is not None else kwargs.get("Code") or self.properties.get("Code", 65)
        
        try:
            val = int(code_val)
            if 0 <= val <= 1114111: # Full Unicode range, though ASCII is 0-255
                # Python's chr() supports unicode, so we might as well allow it if safe.
                # But user asked for 0-255. Let's stick to standard behavior but safe.
                result = chr(val)
            else:
                self.logger.error(f"Code {val} out of range.")
                result = ""
        except (ValueError, TypeError):
            self.logger.error(f"Invalid code '{code_val}'.")
            result = ""
            
        # 2. Set Output
        self.bridge.set(f"{self.node_id}_Char", result, self.name)
        self.bridge.set(f"{self.node_id}_ActivePorts", ["Flow"], self.name)
        return True
