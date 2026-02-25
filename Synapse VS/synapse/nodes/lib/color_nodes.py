from synapse.core.super_node import SuperNode
from synapse.nodes.registry import NodeRegistry
from synapse.core.types import DataType, TypeCaster
import struct

@NodeRegistry.register("Color Constant", "Media/Color")
class ColorConstantNode(SuperNode):
    """
    Outputs a fixed color value.
    Supports RGBA hex strings (e.g., "#800080FF") and manages the color data type.
    
    Inputs:
    - Flow: Trigger the output.
    - Color: Optional input to override the constant value.
    
    Outputs:
    - Flow: Triggered after output.
    - Result: The specified color in RGBA hex format.
    """
    version = "2.1.0"

    def __init__(self, node_id, name, bridge):
        super().__init__(node_id, name, bridge)
        # Default Purple hex
        self.properties["Color"] = "#800080FF"
        self.define_schema()
        self.register_handlers()

    def register_handlers(self):
        self.register_handler("Flow", self.output_color)

    def define_schema(self):
        self.input_schema = {
            "Flow": DataType.FLOW,
            "Color": DataType.COLOR
        }
        self.output_schema = {
            "Flow": DataType.FLOW,
            "Result": DataType.COLOR
        }

    def output_color(self, Color=None, **kwargs):
        col = Color if Color is not None else self.properties.get("Color", "#800080FF")
        
        # Ensure it's a string hex if it came as a list from legacy nodes
        if isinstance(col, list):
            if len(col) >= 3:
                r, g, b = col[0], col[1], col[2]
                a = col[3] if len(col) > 3 else 255
                col = "#{:02x}{:02x}{:02x}{:02x}".format(r, g, b, a)
            else:
                col = "#800080FF"
            
        self.bridge.set(f"{self.node_id}_Result", col, self.name)
        self.logger.info(f"Outputting color: {col}")
        
        self.bridge.set(f"{self.node_id}_ActivePorts", ["Flow"], self.name)
        return True


@NodeRegistry.register("Split Color", "Media/Color")
class ColorSplitNode(SuperNode):
    """
    Deconstructs a color value into its individual Red, Green, Blue, and Alpha components.
    Supports both RGBA hex strings and list formats.
    
    Inputs:
    - Flow: Trigger the split.
    - Color: The color value to split.
    
    Outputs:
    - Flow: Triggered after split.
    - R, G, B, A: The numerical components (0-255).
    """
    version = "2.1.0"

    def __init__(self, node_id, name, bridge):
        super().__init__(node_id, name, bridge)
        self.properties["Color"] = [128, 0, 128, 255]
        self.define_schema()
        self.register_handlers()

    def register_handlers(self):
        self.register_handler("Flow", self.split_color)

    def define_schema(self):
        self.input_schema = {
            "Flow": DataType.FLOW,
            "Color": DataType.COLOR
        }
        self.output_schema = {
            "Flow": DataType.FLOW,
            "R": DataType.NUMBER,
            "G": DataType.NUMBER,
            "B": DataType.NUMBER,
            "A": DataType.NUMBER
        }

    def split_color(self, Color=None, **kwargs):
        color = Color if Color is not None else kwargs.get("Color") or self.properties.get("Color", "#800080FF")
        
        r, g, b, a = 0, 0, 0, 255
        
        if isinstance(color, str) and color.startswith("#"):
            try:
                hex_val = color.lstrip('#')
                if len(hex_val) == 6: # RGB
                    r, g, b = struct.unpack('BBB', bytes.fromhex(hex_val))
                    a = 255
                elif len(hex_val) == 8: # RGBA
                    r, g, b, a = struct.unpack('BBBB', bytes.fromhex(hex_val))
            except: pass
        elif isinstance(color, list) and len(color) >= 3:
            r = color[0]
            g = color[1]
            b = color[2]
            a = color[3] if len(color) > 3 else 255

        self.bridge.set(f"{self.node_id}_R", r, self.name)
        self.bridge.set(f"{self.node_id}_G", g, self.name)
        self.bridge.set(f"{self.node_id}_B", b, self.name)
        self.bridge.set(f"{self.node_id}_A", a, self.name)
        
        self.bridge.set(f"{self.node_id}_ActivePorts", ["Flow"], self.name)
        return True


@NodeRegistry.register("Merge Color", "Media/Color")
class ColorMergeNode(SuperNode):
    """
    Combines individual Red, Green, Blue, and Alpha components into a single color value.
    Resulting output is an RGBA hex string.
    
    Inputs:
    - Flow: Trigger the merge.
    - R, G, B, A: Numerical components (0-255).
    
    Outputs:
    - Flow: Triggered after merge.
    - Color: The combined color in RGBA hex format.
    """
    version = "2.1.0"

    def __init__(self, node_id, name, bridge):
        super().__init__(node_id, name, bridge)
        self.properties["R"] = 0
        self.properties["G"] = 0
        self.properties["B"] = 0
        self.properties["A"] = 255
        self.define_schema()
        self.register_handlers()

    def register_handlers(self):
        self.register_handler("Flow", self.merge_color)

    def define_schema(self):
        self.input_schema = {
            "Flow": DataType.FLOW,
            "R": DataType.NUMBER,
            "G": DataType.NUMBER,
            "B": DataType.NUMBER,
            "A": DataType.NUMBER
        }
        self.output_schema = {
            "Flow": DataType.FLOW,
            "Color": DataType.COLOR
        }

    def merge_color(self, R=None, G=None, B=None, A=None, **kwargs):
        r_val = R if R is not None else kwargs.get("R") or self.properties.get("R", 0)
        g_val = G if G is not None else kwargs.get("G") or self.properties.get("G", 0)
        b_val = B if B is not None else kwargs.get("B") or self.properties.get("B", 0)
        a_val = A if A is not None else kwargs.get("A") or self.properties.get("A", 255)
        
        try:
            r = max(0, min(255, int(TypeCaster.to_number(r_val))))
            g = max(0, min(255, int(TypeCaster.to_number(g_val))))
            b = max(0, min(255, int(TypeCaster.to_number(b_val))))
            a = max(0, min(255, int(TypeCaster.to_number(a_val))))
            
            hex_color = "#{:02x}{:02x}{:02x}{:02x}".format(r, g, b, a)
            self.bridge.set(f"{self.node_id}_Color", hex_color, self.name)
            
        except Exception as e:
            self.logger.error(f"Error merging color: {e}")
            
        self.bridge.set(f"{self.node_id}_ActivePorts", ["Flow"], self.name)
        return True
