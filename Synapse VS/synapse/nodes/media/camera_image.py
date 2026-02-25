from synapse.core.super_node import SuperNode
from synapse.nodes.registry import NodeRegistry
from synapse.core.types import DataType
import synapse.nodes.media.camera as camera

@NodeRegistry.register("Camera Image", "Media/Video")
class CameraImageNode(SuperNode):
    """
    Retrieves the most recent frame from an active Camera Provider.
    This node acts as a consumer, pulling frames published by a capture service.
    
    Inputs:
    - Flow: Trigger the frame retrieval.
    
    Outputs:
    - Flow: Pulse triggered after the image is retrieved.
    - Image: The captured image object.
    """
    version = "2.1.0"

    def __init__(self, node_id, name, bridge):
        super().__init__(node_id, name, bridge)
        self.is_native = True
        self.define_schema()
        self.register_handlers()

    def register_handlers(self):
        self.register_handler("Flow", self.get_frame)

    def define_schema(self):
        self.input_schema = {
            "Flow": DataType.FLOW
        }
        self.output_schema = {
            "Flow": DataType.FLOW,
            "Image": DataType.IMAGE
        }

    def get_frame(self, **kwargs):
        provider_id = self.get_provider_id("CAMERA")
            
        if not provider_id:
            self.logger.error("No CAMERA Provider found.")
            self.bridge.set(f"{self.node_id}_ActivePorts", ["Flow"], self.name)
            return True

        # Read the published frame from the bridge
        # CameraCaptureNode publishes frames as ImageObject to "{node_id}_CurrentFrame"
        import time
        img_obj = None
        for _ in range(10):
            img_obj = self.bridge.get(f"{provider_id}_CurrentFrame")
            if img_obj is not None:
                break
            time.sleep(0.1)

        if img_obj is not None:
            self.bridge.set(f"{self.node_id}_Image", img_obj, self.name)
        else:
            self.logger.warning(f"No frame available from provider {provider_id}.")
            self.bridge.set(f"{self.node_id}_Image", None, self.name)

        self.bridge.set(f"{self.node_id}_ActivePorts", ["Flow"], self.name)
        return True