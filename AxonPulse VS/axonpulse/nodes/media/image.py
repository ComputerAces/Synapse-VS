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

ImageOps = None

def ensure_pil():
    global Image, ImageOps
    if Image:
        return True
    if DependencyManager.ensure('Pillow', 'PIL'):
        from PIL import Image as _I, ImageOps as _O
        Image = _I
        ImageOps = _O
        return True
    return False

@axon_node(category="Media/Graphics", version="2.3.0", node_label="Image Processor", outputs=['Result Path'])
def ImageProcessorNode(Image_Path: str = '', Action: Any = 'Grayscale', Action_Data: dict = {}, W: Any = 100, H: Any = 100, Box: list = [0, 0, 100, 100], _bridge: Any = None, _node: Any = None, _node_id: str = None, **kwargs) -> Any:
    """Performs common image manipulation actions like resizing, cropping, or color conversion.

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
- Result Path: Path to the modified temporary image file."""
    if not DependencyManager.ensure('PIL', 'Pillow'):
        return
    else:
        pass
    Image_Path = Image_Path or _node.properties.get('Image Path', _node.properties.get('ImagePath'))
    action = Action or _node.properties.get('Action', 'Grayscale')
    action_data = Action_Data if Action_Data is not None else _node.properties.get('Action Data', {})
    if not Image_Path or not os.path.exists(Image_Path):
        _node.logger.warning(f'Image Path invalid: {Image_Path}')
        _bridge.set(f'{_node_id}_ActivePorts', ['Flow'], _node.name)
    else:
        pass
    action = _node.properties.get('Action', _node.properties.get('Action', 'Grayscale'))
    try:
        img = Image.open(Image_Path)
        if action == 'Grayscale':
            res = ImageOps.grayscale(img)
        elif action == 'Resize':
            w = int(W) if W is not None else int(_node.properties.get('W', _node.properties.get('W', 100)))
            h = int(H) if H is not None else int(_node.properties.get('H', _node.properties.get('H', 100)))
            res = img.resize((w, h))
        elif action == 'Crop':
            box = Box if Box is not None else _node.properties.get('Box', _node.properties.get('Box', [0, 0, 100, 100]))
            res = img.crop(tuple(box))
        else:
            res = img
        (base, ext) = os.path.splitext(Image_Path)
        out_path = f'{base}_{int(time.time())}{ext}'
        res.save(out_path)
    except Exception as e:
        _node.logger.error(f'Image Processor Error: {e}')
    finally:
        pass
    _bridge.set(f'{_node_id}_ActivePorts', ['Flow'], _node.name)
    return out_path
