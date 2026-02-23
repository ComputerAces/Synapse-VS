import os
import base64
from io import BytesIO
from synapse.core.super_node import SuperNode
from synapse.nodes.registry import NodeRegistry
from synapse.core.types import DataType
from synapse.core.dependencies import DependencyManager

# Lazy Globals
Image = None
cv2 = None

def ensure_pil():
    global Image
    if Image: return True
    if DependencyManager.ensure("Pillow", "PIL"):
        from PIL import Image as _I
        Image = _I; return True
    return False

def ensure_cv2():
    global cv2
    if cv2: return True
    if DependencyManager.ensure("opencv-python", "cv2"):
        import cv2 as _cv2
        cv2 = _cv2; return True
    return False

@NodeRegistry.register("Image Preview", "Media/Graphics")
class ImagePreviewNode(SuperNode):
    """
    Visualizes image and video data directly within the node interface.
    
    Generates a high-performance thumbnail from local file paths, video frames, 
    or memory-resident PIL objects. Displays the preview on the node canvas 
    for immediate feedback.
    
    Inputs:
    - Flow: Trigger the preview generation.
    - Image Data: The source path or image object to preview.
    
    Outputs:
    - Flow: Triggered after the thumbnail is generated.
    - Image Path: The resolved absolute path to the previewed resource.
    """
    version = "2.1.0"

    def __init__(self, node_id, name, bridge):
        super().__init__(node_id, name, bridge)
        self.is_native = True
        self.properties["Image Data"] = ""
        self.define_schema()
        self.register_handlers()

    def register_handlers(self):
        self.register_handler("Flow", self.show_preview)

    def define_schema(self): # New method for schema definition
        self.input_schema = {
            "Flow": DataType.FLOW,
            "Image Data": DataType.ANY
        }
        self.output_schema = {
            "Flow": DataType.FLOW
        }

    # Removed default_inputs and default_outputs properties

    def show_preview(self, Image_Data=None, **kwargs): # Renamed from execute
        if not ensure_pil():
            self.logger.error("Pillow (PIL) not installed.")
            self.bridge.set(f"{self.node_id}_ActivePorts", ["Flow"], self.name)
            return True
            
        # Fallback with legacy support
        data = Image_Data if Image_Data is not None else self.properties.get("Image Data", self.properties.get("ImageData"))
        
        if not data:
            self.logger.warning("No Image Data provided.")
            self.bridge.set(f"{self.node_id}_ActivePorts", ["Flow"], self.name)
            return True

        img = None
        path_out = ""

        try:
            # 1. Resolve Input Type
            if isinstance(data, str):
                if os.path.exists(data):
                    ext = os.path.splitext(data)[1].lower()
                    video_exts = ['.mp4', '.avi', '.mov', '.mkv', '.wmv']
                    
                    if ext in video_exts:
                        if ensure_cv2():
                            try:
                                cap = cv2.VideoCapture(data)
                                ret, frame = cap.read()
                                if ret:
                                    # Convert BGR to RGB
                                    frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                                    img = Image.fromarray(frame_rgb)
                                    path_out = data
                                cap.release()
                            except Exception as e:
                                self.logger.error(f"Failed to capture frame from video: {e}")
                        else:
                            self.logger.warning("OpenCV not available for video preview.")
                    
                    if not img: # Not a video or video capture failed
                        try:
                            img = Image.open(data)
                            path_out = data
                        except Exception as e:
                            self.logger.error(f"Failed to open image path: {e}")
                            self.bridge.set(f"{self.node_id}_ActivePorts", ["Flow"], self.name)
                            return True
                else:
                    self.logger.warning(f"Image path not found: {data}")
                    self.bridge.set(f"{self.node_id}_ActivePorts", ["Flow"], self.name)
                    return True
            # Check for PIL Image
            elif hasattr(data, "copy") and hasattr(data, "thumbnail"): 
                img = data
            else:
                self.logger.warning(f"Unsupported image data type: {type(data)}")
                self.bridge.set(f"{self.node_id}_ActivePorts", ["Flow"], self.name)
                return True
            
            # 2. Generate Thumbnail
            if img:
                # Create a copy to resize (don't modify original if it's an object)
                thumb = img.copy()
                thumb.thumbnail((220, 160)) # Match node preview max size
                
                # Convert to Base64
                buffered = BytesIO()
                # Save as JPEG for size efficiency, or PNG if alpha needed
                fmt = "PNG" if hasattr(img, 'mode') and img.mode == 'RGBA' else "JPEG" # More robust mode check
                thumb.save(buffered, format=fmt)
                img_str = base64.b64encode(buffered.getvalue()).decode("utf-8")
                
                # 3. Send to UI via Special Protocol
                # Format: [NODE_PREVIEW] {node_id} | {mode: square|16:9} | {img_str}
                print(f"[NODE_PREVIEW] {self.node_id} | square | {img_str}", flush=True)
                
                # Update property for persistence (optional, might be large)
                # self.properties["PreviewData"] = img_str 

        except Exception as e:
            self.logger.error(f"Preview Error: {e}")
            
        self.bridge.set(f"{self.node_id}_ActivePorts", ["Flow"], self.name)
        return True
