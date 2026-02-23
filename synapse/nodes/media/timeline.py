import os
import base64
import io
from synapse.core.super_node import SuperNode
from synapse.nodes.registry import NodeRegistry
from synapse.core.types import DataType
from synapse.nodes.lib.provider_node import ProviderNode
from synapse.core.video_builder.models import SceneList, SceneObject, AssetType
from synapse.core.dependencies import DependencyManager

# Lazy Globals
Image = None
ImageDraw = None

def ensure_pil():
    global Image, ImageDraw
    if Image: return True
    if DependencyManager.ensure("Pillow", "PIL"):
        from PIL import Image as _I, ImageDraw as _D
        Image = _I; ImageDraw = _D; return True
    return False

@NodeRegistry.register("Timeline Start", "Media/Video")
class TimelineStartNode(ProviderNode):
    """
    Initiates a new video timeline session.
    
    Creates an empty 'SceneList' object that can be populated with 
    clips, graphics, and audio by downstream nodes. Acts as a 
    provider for video building tasks.
    
    Inputs:
    - Flow: Trigger the timeline start.
    
    Outputs:
    - Flow: Pulse triggered once the timeline is initialized.
    - SceneList: The empty SceneList object.
    """
    version = "2.1.0"

    def __init__(self, node_id, name, bridge):
        super().__init__(node_id, name, bridge)
        self.is_native = True
        self.provider_type = "Timeline Provider"
        self.hidden_ports = ["Provider End", "Exit"]
        self.define_schema()
        self.register_handlers()

    def register_handlers(self):
        self.register_handler("Flow", self.start_timeline)

    def define_schema(self):
        self.input_schema = {
            "Flow": DataType.FLOW
        }
        self.output_schema = {
            "Flow": DataType.FLOW,
            "SceneList": DataType.SCENELIST
        }

    def start_timeline(self, **kwargs):
        sl = SceneList()
        self.bridge.set(f"{self.node_id}_SceneList", sl.serialize(), self.name)
        # For Hijacking
        self.bridge.set(f"{self.node_id}_Provider ID", self.node_id, self.name)
        self.bridge.set(f"{self.node_id}_Provider Type", self.provider_type, self.name)
        
        self.bridge.set(f"{self.node_id}_ActivePorts", ["Flow"], self.name)
        return True
