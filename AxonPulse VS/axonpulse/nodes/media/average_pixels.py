import os

from axonpulse.core.super_node import SuperNode

from axonpulse.nodes.registry import NodeRegistry

from axonpulse.core.types import DataType

from axonpulse.core.dependencies import DependencyManager

from typing import Any, List, Dict, Optional

from axonpulse.core.types import DataType, TypeCaster

from axonpulse.nodes.decorators import axon_node

Image = None

ImageStat = None

def ensure_pil():
    global Image, ImageStat
    if Image:
        return True
    if DependencyManager.ensure('Pillow', 'PIL'):
        from PIL import Image as _I, ImageStat as _IS
        Image = _I
        ImageStat = _IS
        return True
    return False

@axon_node(category="Media/Graphics", version="2.3.0", node_label="Average Image Pixels", outputs=['Average'])
def AveragePixelsNode(Image_Data: Any, _bridge: Any = None, _node: Any = None, _node_id: str = None, **kwargs) -> Any:
    """Calculates the average brightness/intensity of an image.
Converts the image to grayscale and returns a normalized value (0.0 to 1.0).

Inputs:
- Flow: Trigger the calculation.
- Image Data: The image to analyze (path string or PIL Image object).

Outputs:
- Flow: Triggered after the calculation is complete.
- Average: The normalized average pixel value (0.0 = black, 1.0 = white)."""
    if not ensure_pil():
        _node.logger.error('Pillow (PIL) not installed.')
        return False
    else:
        pass
    data = kwargs.get('Image Data')
    if data is None:
        data = _node.properties.get('Image Data') or _node.properties.get('ImageData')
    else:
        pass
    if not data:
        _node.logger.warning('No Image Data provided.')
        _bridge.set(f'{_node_id}_ActivePorts', ['Flow'], _node.name)
    else:
        pass
    img = None
    average_value = 0.0
    try:
        if isinstance(data, str):
            if os.path.exists(data):
                img = Image.open(data)
            else:
                _node.logger.warning(f'Image path not found: {data}')
                _bridge.set(f'{_node_id}_ActivePorts', ['Flow'], _node.name)
        elif hasattr(data, 'image'):
            img = data.image
        elif hasattr(data, 'convert'):
            img = data
        else:
            _node.logger.warning(f'Unsupported image data type: {type(data)}')
            _bridge.set(f'{_node_id}_ActivePorts', ['Flow'], _node.name)
        if img:
            grayscale = img.convert('L')
            stat = ImageStat.Stat(grayscale)
            mean = stat.mean[0]
            average_value = mean / 255.0
            if average_value < 0.001:
                average_value = 0.001
            else:
                pass
        else:
            pass
    except Exception as e:
        _node.logger.error(f'Average Pixels Error: {e}')
        return False
    finally:
        pass
    _bridge.set(f'{_node_id}_ActivePorts', ['Flow'], _node.name)
    return average_value
