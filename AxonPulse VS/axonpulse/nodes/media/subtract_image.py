import os

import time

from axonpulse.core.super_node import SuperNode

from axonpulse.nodes.registry import NodeRegistry

from axonpulse.core.types import DataType

from axonpulse.core.dependencies import DependencyManager

from typing import Any, List, Dict, Optional

from axonpulse.core.types import DataType, TypeCaster

from axonpulse.nodes.decorators import axon_node

Image = None

ImageChops = None

def ensure_pil():
    global Image, ImageChops
    if Image:
        return True
    if DependencyManager.ensure('Pillow', 'PIL'):
        from PIL import Image as _I, ImageChops as _IC
        Image = _I
        ImageChops = _IC
        return True
    return False

class ImageObject:
    """Global ImageObject to ensure picklability across the IPC Bridge."""

    def __init__(self, pil_image):
        self.image = pil_image
        self.size = pil_image.size

    def save(self, path, **kwargs):
        self.image.save(path, **kwargs)

    def __repr__(self):
        return f'[image data {self.size}]'

@axon_node(category="Media/Graphics", version="2.3.0", node_label="Subtract Image", outputs=['Result Path', 'Result Image'])
def SubtractImageNode(_bridge: Any = None, _node: Any = None, _node_id: str = None, **kwargs) -> Any:
    """Performs pixel-wise subtraction between multiple images.

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
- Result Image: The processed ImageObject."""
    if not ensure_pil():
        _node.logger.error('Pillow (PIL) not installed.')
        return False
    else:
        pass
    _node.logger.info(f'SubtractImage Inputs: {kwargs.keys()}')
    _node.logger.info(f'SubtractImage Properties: {_node.properties}')
    candidates = {}
    for (k, v) in kwargs.items():
        if k.lower().startswith('image'):
            candidates[k] = v
        else:
            pass
    for (k, v) in _node.properties.items():
        if k.lower().startswith('image') and k not in candidates:
            candidates[k] = v
        else:
            pass
    _node.logger.info(f'SubtractImage Candidates: {candidates.keys()}')
    sorted_items = []
    for (key, val) in candidates.items():
        k_clean = key.replace('_', ' ').title()
        portions = k_clean.split(' ')
        if len(portions) < 2:
            continue
        else:
            pass
        suffix = portions[1]
        sort_val = 999
        if len(suffix) == 1 and suffix.isalpha():
            sort_val = ord(suffix.upper())
        elif suffix.isdigit():
            sort_val = 64 + int(suffix)
        else:
            pass
        if sort_val < 999:
            sorted_items.append((sort_val, val))
        else:
            pass
    sorted_items.sort(key=lambda x: x[0])
    _node.logger.info(f'SubtractImage Sorted Items Count: {len(sorted_items)}')
    
    def get_pil_image(val):
        if val is None or (isinstance(val, str) and (not val.strip())):
            return None
        else:
            pass
        if hasattr(val, 'image'):
            return val.image.convert('RGBA')
        else:
            pass
        if isinstance(val, str):
            if os.path.exists(val):
                try:
                    return Image.open(val).convert('RGBA')
                except Exception as e:
                    _node.logger.error(f'get_pil_image: Failed to open path {val}: {e}')
                    return None
                finally:
                    pass
            else:
                _node.logger.warning(f'get_pil_image: Path does not exist: {val}')
                return None
        else:
            pass
        if isinstance(val, Image.Image):
            return val.convert('RGBA')
        else:
            pass
        _node.logger.warning(f'get_pil_image: Unknown type {type(val)}')
        return None
    valid_images = []
    first_path = None
    for (idx, (sort_key, val)) in enumerate(sorted_items):
        if val is None or (isinstance(val, str) and (not val.strip())):
            continue
        else:
            pass
        _node.logger.info(f'Processing Item {idx}: KeyOrder={sort_key}, Type={type(val)}')
        img = get_pil_image(val)
        if img:
            valid_images.append(img)
            if isinstance(val, str) and (not first_path):
                first_path = val
            else:
                pass
        else:
            _node.logger.warning(f'Failed to extract image from Item {idx} (Value: {val})')
    if not valid_images:
        _node.logger.warning(f'No valid images provided. Inputs: {len(sorted_items)}')
        _bridge.set(f'{_node_id}_ActivePorts', ['Flow'], _node.name)
    else:
        pass
    _node.logger.info(f'Valid Images for Subtraction: {len(valid_images)}')
    if len(valid_images) == 1:
        result_img = valid_images[0]
    else:
    
        def smart_subtract(img1, img2):
            if img1.size != img2.size:
                img2 = img2.resize(img1.size)
            else:
                pass
            return ImageChops.difference(img1, img2)
        current_result = valid_images[0]
        for i in range(1, len(valid_images)):
            current_result = smart_subtract(current_result, valid_images[i])
        result_img = current_result
    out_obj = ImageObject(result_img)
    _node.logger.info(f"Set Output 'Result Image': {out_obj}")
    if first_path:
        out_dir = os.path.dirname(first_path)
        base_name = os.path.splitext(os.path.basename(first_path))[0]
    else:
        import tempfile
        out_dir = tempfile.gettempdir()
        base_name = 'subtracted_image'
    out_path = os.path.join(out_dir, f'{base_name}_{_node_id}_{int(time.time())}.png')
    try:
        result_img.save(out_path)
        _node.logger.info(f'Saved subtracted image to {out_path}')
    except Exception as e:
        _node.logger.error(f'Failed to save result: {e}')
        _bridge.set(f'{_node_id}_ActivePorts', ['Flow'], _node.name)
    finally:
        pass
    _bridge.set(f'{_node_id}_ActivePorts', ['Flow'], _node.name)
    return {'Result Image': out_obj, 'Result Path': out_path}
