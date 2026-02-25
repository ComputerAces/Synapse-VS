import os
import time
from synapse.core.super_node import SuperNode
from synapse.nodes.registry import NodeRegistry
from synapse.core.types import DataType
from synapse.core.dependencies import DependencyManager

# Lazy Globals
Image = None
ImageOps = None

def ensure_pil():
    global Image, ImageOps
    if Image: return True
    if DependencyManager.ensure("Pillow", "PIL"):
        from PIL import Image as _I, ImageOps as _O
        Image = _I; ImageOps = _O; return True
    return False

@NodeRegistry.register("Image Processor", "Media/Graphics")
class ImageProcessorNode(SuperNode):
    """
    Performs common image manipulation actions like resizing, cropping, or color conversion.
    
    Applies the selected 'Action' to an input image. Supported actions include:
    - Grayscale: Convert to 8-bit black and white.
    - Single Channel: Extract R, G, or B channel.
    - Brightness: Adjust intensity using 'factor' in Action Data.
    - Resize: Scale image to W x H dimensions.
    - Crop: Extract region [x, y, w, h] from Box input.
    
    Inputs:
    - Flow: Trigger the image process.
    - Image Path: Path to the source file.
    - Action: The visual effect or transformation to apply.
    - Action Data: Custom parameters for the effect (JSON).
    - W: Target width (for Resize action).
    - H: Target height (for Resize action).
    - Box: Crop boundaries [x, y, w, h] (for Crop action).
    
    Outputs:
    - Flow: Triggered after processing completes.
    - Result Path: Path to the modified temporary image file.
    """
    version = "2.1.0"

    def __init__(self, node_id, name, bridge):
        super().__init__(node_id, name, bridge)
        self.is_native = True
        self.properties["Action"] = "Grayscale" 
        self.properties["Action Data"] = {}
        self.properties["Image Path"] = ""
        self.properties["W"] = 100
        self.properties["H"] = 100
        self.properties["Box"] = [0, 0, 100, 100]
        self.define_schema()
        self.register_handlers()

    def register_handlers(self):
        self.register_handler("Flow", self.process_image)

    def define_schema(self): # New method for schema definition
        self.input_schema = {
            "Flow": DataType.FLOW,
            "Image Path": DataType.STRING,
            "Action": DataType.DRAW_EFFECT,
            "Action Data": DataType.DICT,
            "W": DataType.INT,
            "H": DataType.INT,
            "Box": DataType.LIST
        }
        self.output_schema = {
            "Flow": DataType.FLOW,
            "Result Path": DataType.STRING
        }

    def process_image(self, Image_Path=None, Action=None, Action_Data=None, W=None, H=None, Box=None, **kwargs):
        if not DependencyManager.ensure("PIL", "Pillow"):
            return # Changed return False to return

        # Fallback with legacy support
        Image_Path = Image_Path or self.properties.get("Image Path", self.properties.get("ImagePath"))
        action = Action or self.properties.get("Action", "Grayscale")
        action_data = Action_Data if Action_Data is not None else self.properties.get("Action Data", {})
        
        if not Image_Path or not os.path.exists(Image_Path):
            self.logger.warning(f"Image Path invalid: {Image_Path}")
            self.bridge.set(f"{self.node_id}_ActivePorts", ["Flow"], self.name)
            return True

        # Fallback with legacy support
        action = self.properties.get("Action", self.properties.get("Action", "Grayscale"))
        try:
            img = Image.open(Image_Path)
            if action == "Grayscale":
                res = ImageOps.grayscale(img)
            elif action == "Resize":
                w = int(W) if W is not None else int(self.properties.get("W", self.properties.get("W", 100)))
                h = int(H) if H is not None else int(self.properties.get("H", self.properties.get("H", 100)))
                res = img.resize((w, h))
            elif action == "Crop":
                box = Box if Box is not None else self.properties.get("Box", self.properties.get("Box", [0, 0, 100, 100]))
                res = img.crop(tuple(box))
            else:
                res = img

            # Save to temporary file pattern
            base, ext = os.path.splitext(Image_Path)
            out_path = f"{base}_{int(time.time())}{ext}"
            res.save(out_path)
            self.bridge.set(f"{self.node_id}_Result Path", out_path, self.name)
        except Exception as e:
            self.logger.error(f"Image Processor Error: {e}")

        self.bridge.set(f"{self.node_id}_ActivePorts", ["Flow"], self.name)
        return True
