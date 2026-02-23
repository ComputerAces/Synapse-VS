import os
from synapse.core.super_node import SuperNode
from synapse.nodes.registry import NodeRegistry
from synapse.core.types import DataType
from synapse.core.dependencies import DependencyManager

# Lazy Globals
Image = None
ImageStat = None

def ensure_pil():
    global Image, ImageStat
    if Image: return True
    if DependencyManager.ensure("Pillow", "PIL"):
        from PIL import Image as _I, ImageStat as _IS
        Image = _I; ImageStat = _IS; return True
    return False

@NodeRegistry.register("Average Image Pixels", "Media/Graphics")
class AveragePixelsNode(SuperNode):
    """
    Calculates the average brightness/intensity of an image.
    Converts the image to grayscale and returns a normalized value (0.0 to 1.0).
    
    Inputs:
    - Flow: Trigger the calculation.
    - Image Data: The image to analyze (path string or PIL Image object).
    
    Outputs:
    - Flow: Triggered after the calculation is complete.
    - Average: The normalized average pixel value (0.0 = black, 1.0 = white).
    """
    version = "2.1.0"

    def __init__(self, node_id, name, bridge):
        super().__init__(node_id, name, bridge)
        self.is_native = True
        self.define_schema()
        self.register_handlers()

    def register_handlers(self):
        self.register_handler("Flow", self.calculate_average)

    def define_schema(self):
        self.input_schema = {
            "Flow": DataType.FLOW,
            "Image Data": DataType.IMAGE
        }
        self.output_schema = {
            "Flow": DataType.FLOW,
            "Average": DataType.NUMBER
        }

    def calculate_average(self, **kwargs):
        if not ensure_pil():
            self.logger.error("Pillow (PIL) not installed.")
            return False

        # Resolve Image Data — wire value takes priority, then properties
        data = kwargs.get("Image Data")
        if data is None:
            data = self.properties.get("Image Data") or self.properties.get("ImageData")
        
        if not data:
            self.logger.warning("No Image Data provided.")
            self.bridge.set(f"{self.node_id}_Average", 0.0, self.name)
            self.bridge.set(f"{self.node_id}_ActivePorts", ["Flow"], self.name)
            return True

        img = None
        average_value = 0.0
        
        try:
            # 1. Resolve Input
            if isinstance(data, str):
                if os.path.exists(data):
                    img = Image.open(data)
                else:
                    self.logger.warning(f"Image path not found: {data}")
                    self.bridge.set(f"{self.node_id}_ActivePorts", ["Flow"], self.name)
                    return True
            # ImageObject (has .image attribute)
            elif hasattr(data, "image"):
                img = data.image
            # PIL Image check
            elif hasattr(data, "convert"): 
                img = data
            else:
                self.logger.warning(f"Unsupported image data type: {type(data)}")
                self.bridge.set(f"{self.node_id}_ActivePorts", ["Flow"], self.name)
                return True
            
            # 2. Calculate Average
            if img:
                # Convert to Grayscale for simple brightness average
                grayscale = img.convert("L")
                stat = ImageStat.Stat(grayscale)
                mean = stat.mean[0] # List, so take first element
                
                # Normalize 0-255 to 0.0-1.0
                average_value = mean / 255.0
                
                # Epsilon floor — prevent exact 0.0 to avoid zeroing downstream math
                if average_value < 0.001:
                    average_value = 0.001
                
        except Exception as e:
            self.logger.error(f"Average Pixels Error: {e}")
            return False
            
        self.bridge.set(f"{self.node_id}_Average", average_value, self.name)
        self.bridge.set(f"{self.node_id}_ActivePorts", ["Flow"], self.name)
        return True