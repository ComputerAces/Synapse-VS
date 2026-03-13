import os

import base64

from io import BytesIO

from axonpulse.core.super_node import SuperNode

from axonpulse.nodes.registry import NodeRegistry

from axonpulse.core.types import DataType

from axonpulse.core.dependencies import DependencyManager

from typing import Any, List, Dict, Optional

from axonpulse.core.types import DataType, TypeCaster

from axonpulse.nodes.decorators import axon_node

Image = None

cv2 = None

def ensure_pil():
    global Image
    if Image:
        return True
    if DependencyManager.ensure('Pillow', 'PIL'):
        from PIL import Image as _I
        Image = _I
        return True
    return False

def ensure_cv2():
    global cv2
    if cv2:
        return True
    if DependencyManager.ensure('opencv-python', 'cv2'):
        import cv2 as _cv2
        cv2 = _cv2
        return True
    return False

@axon_node(category="Media/Graphics", version="2.3.0", node_label="Image Preview")
def ImagePreviewNode(Image_Data: Any = '', _bridge: Any = None, _node: Any = None, _node_id: str = None, **kwargs) -> Any:
    """Visualizes image and video data directly within the node interface.

Generates a high-performance thumbnail from local file paths, video frames, 
or memory-resident PIL objects. Displays the preview on the node canvas 
for immediate feedback.

Inputs:
- Flow: Trigger the preview generation.
- Image Data: The source path or image object to preview.

Outputs:
- Flow: Triggered after the thumbnail is generated.
- Image Path: The resolved absolute path to the previewed resource."""
    if not ensure_pil():
        _node.logger.error('Pillow (PIL) not installed.')
        _bridge.set(f'{_node_id}_ActivePorts', ['Flow'], _node.name)
        return True
    else:
        pass
    data = Image_Data if Image_Data is not None else _node.properties.get('Image Data', _node.properties.get('ImageData'))
    if not data:
        _node.logger.warning('No Image Data provided.')
        _bridge.set(f'{_node_id}_ActivePorts', ['Flow'], _node.name)
        return True
    else:
        pass
    img = None
    path_out = ''
    try:
        if isinstance(data, str):
            if os.path.exists(data):
                ext = os.path.splitext(data)[1].lower()
                video_exts = ['.mp4', '.avi', '.mov', '.mkv', '.wmv']
                if ext in video_exts:
                    if ensure_cv2():
                        try:
                            cap = cv2.VideoCapture(data)
                            (ret, frame) = cap.read()
                            if ret:
                                frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                                img = Image.fromarray(frame_rgb)
                                path_out = data
                            else:
                                pass
                            cap.release()
                        except Exception as e:
                            _node.logger.error(f'Failed to capture frame from video: {e}')
                        finally:
                            pass
                    else:
                        _node.logger.warning('OpenCV not available for video preview.')
                else:
                    pass
                if not img:
                    try:
                        img = Image.open(data)
                        path_out = data
                    except Exception as e:
                        _node.logger.error(f'Failed to open image path: {e}')
                        _bridge.set(f'{_node_id}_ActivePorts', ['Flow'], _node.name)
                        return True
                    finally:
                        pass
                else:
                    pass
            else:
                _node.logger.warning(f'Image path not found: {data}')
                _bridge.set(f'{_node_id}_ActivePorts', ['Flow'], _node.name)
                return True
        elif hasattr(data, 'copy') and hasattr(data, 'thumbnail'):
            img = data
        else:
            _node.logger.warning(f'Unsupported image data type: {type(data)}')
            _bridge.set(f'{_node_id}_ActivePorts', ['Flow'], _node.name)
            return True
        if img:
            thumb = img.copy()
            thumb.thumbnail((220, 160))
            buffered = BytesIO()
            fmt = 'PNG' if hasattr(img, 'mode') and img.mode == 'RGBA' else 'JPEG'
            thumb.save(buffered, format=fmt)
            img_str = base64.b64encode(buffered.getvalue()).decode('utf-8')
            print(f'[NODE_PREVIEW] {_node_id} | square | {img_str}', flush=True)
        else:
            pass
    except Exception as e:
        _node.logger.error(f'Preview Error: {e}')
    finally:
        pass
    _bridge.set(f'{_node_id}_ActivePorts', ['Flow'], _node.name)
    return True
