import os
import time
from synapse.core.super_node import SuperNode
from synapse.nodes.registry import NodeRegistry
from synapse.core.types import DataType
from synapse.core.dependencies import DependencyManager

# Lazy Globals
Image = None
ImageChops = None

def ensure_pil():
    global Image, ImageChops
    if Image: return True
    if DependencyManager.ensure("Pillow", "PIL"):
        from PIL import Image as _I, ImageChops as _IC
        Image = _I; ImageChops = _IC; return True
    return False

class ImageObject:
    """Global ImageObject to ensure picklability across the IPC Bridge."""
    def __init__(self, pil_image):
        self.image = pil_image
        self.size = pil_image.size
        
    def save(self, path, **kwargs):
        self.image.save(path, **kwargs)
        
    def __repr__(self):
        return f"[image data {self.size}]"

@NodeRegistry.register("Subtract Image", "Media/Graphics")
class SubtractImageNode(SuperNode):
    """
    Performs pixel-wise subtraction between multiple images.
    
    Takes 'Image A' and subtracts 'Image B', 'Image C', etc., from it. 
    Useful for motion detection, background removal, or graphical effects. 
    Supports dynamic image inputs.
    
    Inputs:
    - Flow: Trigger the subtraction.
    - Image A: The base image to subtract from.
    - Image B, Image C...: Images to subtract.
    
    Outputs:
    - Flow: Pulse triggered after subtraction.
    - Result Path: Path where the resulting image is saved.
    - Result Image: The processed ImageObject.
    """
    version = "2.1.0"
    allow_dynamic_inputs = True

    def __init__(self, node_id, name, bridge):
        super().__init__(node_id, name, bridge)
        self.is_native = True
            
        # Initialize Architecture Components
        self.define_schema()
        self.register_handlers()

    def define_schema(self):
        self.input_schema = {
            "Flow": DataType.FLOW
        }

        self.output_schema = {
            "Flow": DataType.FLOW,
            "Result Path": DataType.STRING,
            "Result Image": DataType.ANY 
        }

    def register_handlers(self):
        self.register_handler("Flow", self.subtract_images)

    def subtract_images(self, **kwargs):
        if not ensure_pil():
            self.logger.error("Pillow (PIL) not installed.")
            return False
        
        # Debug: Log received inputs
        self.logger.info(f"SubtractImage Inputs: {kwargs.keys()}")
        self.logger.info(f"SubtractImage Properties: {self.properties}")

        # Collect Image Inputs
        candidates = {}
        for k, v in kwargs.items():
            if k.lower().startswith("image"):
                candidates[k] = v
        # Fallback with legacy support for specific keys if needed, 
        # but here we iterate over all properties starting with 'image'
        for k, v in self.properties.items():
            if k.lower().startswith("image") and k not in candidates:
                candidates[k] = v
        
        self.logger.info(f"SubtractImage Candidates: {candidates.keys()}")

        # Sort keys: Image A, Image B, Image C...
        sorted_items = []
        for key, val in candidates.items():
            k_clean = key.replace("_", " ").title() # Handle image_a -> Image A
            portions = k_clean.split(" ")
            if len(portions) < 2: continue
            suffix = portions[1]
            
            sort_val = 999
            if len(suffix) == 1 and suffix.isalpha():
                sort_val = ord(suffix.upper())
            elif suffix.isdigit():
                sort_val = 64 + int(suffix) 
            
            if sort_val < 999:
                sorted_items.append((sort_val, val))
            
        sorted_items.sort(key=lambda x: x[0]) 
        self.logger.info(f"SubtractImage Sorted Items Count: {len(sorted_items)}")

        # Helper to extract PIL Image
        def get_pil_image(val):
            if val is None: 
                self.logger.warning("get_pil_image: Value is None")
                return None
            # Case 1: ImageObject (has .image attribute)
            if hasattr(val, "image"):
                # self.logger.info("get_pil_image: Found ImageObject")
                return val.image.convert("RGBA")
            # Case 2: File Path (str)
            if isinstance(val, str):
                if os.path.exists(val):
                    # self.logger.info(f"get_pil_image: Found Path {val}")
                    try:
                        return Image.open(val).convert("RGBA")
                    except Exception as e:
                        self.logger.error(f"get_pil_image: Failed to open path {val}: {e}")
                        return None
                else:
                     self.logger.warning(f"get_pil_image: Path does not exist: {val}")
                     return None
            # Case 3: PIL Image directly
            if isinstance(val, Image.Image):
                # self.logger.info("get_pil_image: Found PIL Image")
                return val.convert("RGBA")
            
            self.logger.warning(f"get_pil_image: Unknown type {type(val)}")
            return None

        valid_images = []
        first_path = None
        
        for idx, (sort_key, val) in enumerate(sorted_items):
            self.logger.info(f"Processing Item {idx}: KeyOrder={sort_key}, Type={type(val)}")
            img = get_pil_image(val)
            if img:
                valid_images.append(img)
                if isinstance(val, str) and not first_path:
                    first_path = val
            else:
                self.logger.warning(f"Failed to extract image from Item {idx}")

        if not valid_images:
            self.logger.warning(f"No valid images provided. Inputs: {len(sorted_items)}")
            self.bridge.set(f"{self.node_id}_ActivePorts", ["Flow"], self.name)
            return True

        self.logger.info(f"Valid Images for Subtraction: {len(valid_images)}")

        if len(valid_images) == 1:
            # Pass-through
            result_img = valid_images[0]
        else:
            # Helper for subtraction
            def smart_subtract(img1, img2):
                if img1.size != img2.size:
                    img2 = img2.resize(img1.size)
                return ImageChops.difference(img1, img2)

            current_result = valid_images[0]
            for i in range(1, len(valid_images)):
                current_result = smart_subtract(current_result, valid_images[i])
            result_img = current_result

        out_obj = ImageObject(result_img)
        self.bridge.set(f"{self.node_id}_Result Image", out_obj, self.name)
        self.logger.info(f"Set Output 'Result Image': {out_obj}")

        # Output Path (Save to temp if we don't have a source path to base on)
        if first_path:
            out_dir = os.path.dirname(first_path)
            base_name = os.path.splitext(os.path.basename(first_path))[0]
        else:
            import tempfile
            out_dir = tempfile.gettempdir()
            base_name = "subtracted_image"
            
        out_path = os.path.join(out_dir, f"{base_name}_{self.node_id}_{int(time.time())}.png")
        try:
            result_img.save(out_path)
            self.bridge.set(f"{self.node_id}_Result Path", out_path, self.name)
            self.logger.info(f"Saved subtracted image to {out_path}")
        except Exception as e:
            self.logger.error(f"Failed to save result: {e}")
            self.bridge.set(f"{self.node_id}_ActivePorts", ["Flow"], self.name)
            return True

        self.bridge.set(f"{self.node_id}_ActivePorts", ["Flow"], self.name)
        
        # Signal success to the execution engine
        return True