from axonpulse.core.super_node import SuperNode

from axonpulse.nodes.registry import NodeRegistry

from axonpulse.core.types import DataType

import axonpulse.nodes.media.camera as camera

from typing import Any, List, Dict, Optional

from axonpulse.core.types import DataType, TypeCaster

from axonpulse.nodes.decorators import axon_node

@axon_node(category="Media/Video", version="2.3.0", node_label="Camera Image", outputs=['Image'])
def CameraImageNode(_bridge: Any = None, _node: Any = None, _node_id: str = None, **kwargs) -> Any:
    """Retrieves the most recent frame from an active Camera Provider.
This node acts as a consumer, pulling frames published by a capture service.

Inputs:
- Flow: Trigger the frame retrieval.

Outputs:
- Flow: Pulse triggered after the image is retrieved.
- Image: The captured image object."""
    provider_id = self.get_provider_id('CAMERA')
    if not provider_id:
        _node.logger.error('No CAMERA Provider found.')
        _bridge.set(f'{_node_id}_ActivePorts', ['Flow'], _node.name)
    else:
        pass
    import time
    img_obj = None
    for _ in range(10):
        img_obj = _bridge.get(f'{provider_id}_CurrentFrame')
        if img_obj is not None:
            break
        else:
            pass
        time.sleep(0.1)
    if img_obj is not None:
        pass
    else:
        _node.logger.warning(f'No frame available from provider {provider_id}.')
    _bridge.set(f'{_node_id}_ActivePorts', ['Flow'], _node.name)
    return None
