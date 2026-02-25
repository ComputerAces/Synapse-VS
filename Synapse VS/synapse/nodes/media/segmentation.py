from synapse.core.super_node import SuperNode
from synapse.nodes.registry import NodeRegistry
from synapse.core.types import DataType
from synapse.core.dependencies import DependencyManager
import os

# Lazy Globals
sam_build = None
sam_predictor_cls = None
sam_auto_mask_cls = None
np = None
pil_image = None

def ensure_sam():
    global sam_build, sam_predictor_cls, sam_auto_mask_cls, np, pil_image
    if sam_build: return True

    deps_ok = (
        DependencyManager.ensure("segment-anything", "segment_anything",
                                  pip_name="git+https://github.com/facebookresearch/segment-anything.git")
        and DependencyManager.ensure("numpy")
        and DependencyManager.ensure("Pillow", "PIL")
    )
    if not deps_ok:
        return False

    from segment_anything import sam_model_registry, SamPredictor, SamAutomaticMaskGenerator
    import numpy as _np
    from PIL import Image as _I

    sam_build = sam_model_registry
    sam_predictor_cls = SamPredictor
    sam_auto_mask_cls = SamAutomaticMaskGenerator
    np = _np
    pil_image = _I
    return True


@NodeRegistry.register("Image Segmentation Anything", "Media/Graphics")
class ImageSegmentationAnythingNode(SuperNode):
    """
    Automated image segmentation using the Segment Anything Model (SAM).
    
    This node can automatically identify and mask all objects in an image or perform 
    targeted segmentation based on coordinate prompts (points), bounding boxes, or labels.
    
    Inputs:
    - Flow: Trigger the segmentation process.
    - Image: The source image (Path, PIL Object, or Numpy Array).
    - Points: List of [x, y] coordinates for targeted segmentation.
    - Labels: List of labels for the points (1 for foreground, 0 for background).
    - Box: Bounding box for targeted segmentation [x, y, w, h].
    - Model Type: The SAM model variant (vit_b, vit_l, vit_h).
    - Checkpoint: Path to the model's .pth checkpoint file.
    - Points Per Side: Grid density for automatic mask generation (auto mode).
    
    Outputs:
    - Flow: Triggered after segmentation completes.
    - Segments: List of detected mask objects with bbox and compliance data.
    - Count: The total number of identified segments.
    """
    version = "2.1.0"
    required_libraries = ["segment_anything", "torch", "huggingface_hub"]

    def __init__(self, node_id, name, bridge):
        super().__init__(node_id, name, bridge)
        self.is_native = True
        self.properties["Model Type"] = "vit_b"
        self.properties["Checkpoint"] = ""
        self.properties["Points Per Side"] = 32

        self._sam = None
        self._predictor = None
        self._generator = None

        self.define_schema()
        self.register_handlers()

    def register_handlers(self):
        self.register_handler("Flow", self.do_work)

    def define_schema(self):
        self.input_schema = {
            "Flow": DataType.FLOW,
            "Image": DataType.ANY,
            "Points": DataType.LIST,
            "Labels": DataType.LIST,
            "Box": DataType.LIST,
            "Points Per Side": DataType.NUMBER,
            "Model Type": DataType.STRING,
            "Checkpoint": DataType.STRING
        }
        self.output_schema = {
            "Flow": DataType.FLOW,
            "Segments": DataType.LIST,
            "Count": DataType.NUMBER
        }

    def _load_model(self):
        """Lazy-load SAM model on first use."""
        if self._sam is not None:
            return

        import torch
        # Fallback with legacy support
        model_type = kwargs.get("Model Type") or self.properties.get("Model Type", self.properties.get("ModelType", "vit_b"))
        checkpoint = kwargs.get("Checkpoint") or self.properties.get("Checkpoint", self.properties.get("Checkpoint", ""))

        if not checkpoint:
            raise RuntimeError(
                f"[{self.name}] No checkpoint path specified. "
                f"Set the 'checkpoint' property to a SAM .pth file path."
            )

        if not os.path.exists(checkpoint):
            # Try auto-download via huggingface_hub
            try:
                from huggingface_hub import hf_hub_download
                ckpt_map = {
                    "vit_b": "checkpoints/sam_vit_b_01ec64.pth",
                    "vit_l": "checkpoints/sam_vit_l_0b3195.pth",
                    "vit_h": "checkpoints/sam_vit_h_4b8939.pth",
                }
                hf_path = ckpt_map.get(model_type)
                if hf_path:
                    self.logger.info(f"Downloading SAM {model_type} checkpoint...")
                    checkpoint = hf_hub_download("ybelkada/segment-anything", hf_path)
                    self.properties["Checkpoint"] = checkpoint
                else:
                    raise RuntimeError(f"[{self.name}] Unknown model_type '{model_type}'.")
            except ImportError:
                raise RuntimeError(
                    f"[{self.name}] Checkpoint not found at '{checkpoint}' and "
                    f"huggingface_hub not installed for auto-download."
                )

        self._sam = sam_build[model_type](checkpoint=checkpoint).to(device)
        self._predictor = sam_predictor_cls(self._sam)
        self._generator = sam_auto_mask_cls(
            self._sam,
            points_per_side=int(kwargs.get("Points Per Side") or self.properties.get("Points Per Side", self.properties.get("PointsPerSide", 32)))
        )
        self.logger.info(f"SAM {model_type} loaded on {device}.")

    def _load_image(self, image_input):
        """Convert various image inputs to a numpy RGB array."""
        if isinstance(image_input, str):
            if not os.path.exists(image_input):
                raise RuntimeError(f"[{self.name}] Image file not found: {image_input}")
            img = pil_image.open(image_input).convert("RGB")
            return np.array(img)
        elif hasattr(image_input, 'mode'):
            # PIL Image
            return np.array(image_input.convert("RGB"))
        elif isinstance(image_input, np.ndarray):
            return image_input
        else:
            raise RuntimeError(f"[{self.name}] Unsupported image type: {type(image_input)}")

    def do_work(self, **kwargs):
        if not ensure_sam():
            raise RuntimeError(f"[{self.name}] segment-anything dependency not installed.")

        image_input = kwargs.get("Image")
        points = kwargs.get("Points")
        labels = kwargs.get("Labels")
        box = kwargs.get("Box")

        if not image_input:
            raise RuntimeError(f"[{self.name}] No image provided.")

        self._load_model()
        image_array = self._load_image(image_input)

        segments = []

        if points is not None or box is not None:
            # Prompt Mode
            self._predictor.set_image(image_array)

            point_coords = None
            point_labels = None
            box_arr = None

            if points is not None:
                point_coords = np.array(points)
                point_labels = np.array(labels) if labels else np.ones(len(points))

            if box is not None:
                box_arr = np.array(box)

            masks, scores, _ = self._predictor.predict(
                point_coords=point_coords,
                point_labels=point_labels,
                box=box_arr,
                multimask_output=True
            )

            # Sort by score (best first)
            sorted_indices = scores.argsort()[::-1]
            for i in sorted_indices:
                mask = masks[i]
                ys, xs = np.where(mask)
                if len(xs) == 0:
                    continue
                x1, y1 = int(xs.min()), int(ys.min())
                x2, y2 = int(xs.max()), int(ys.max())
                segments.append({
                    "mask": mask,
                    "bbox": [x1, y1, x2 - x1, y2 - y1],
                    "area": int(mask.sum()),
                    "score": float(scores[i])
                })
        else:
            # Auto Mode — segment everything
            raw_masks = self._generator.generate(image_array)

            # sorted by area (largest first)
            raw_masks.sort(key=lambda x: x["area"], reverse=True)

            for m in raw_masks:
                segments.append({
                    "mask": m["segmentation"],
                    "bbox": list(m["bbox"]),
                    "area": int(m["area"]),
                    "score": float(m.get("predicted_iou", m.get("stability_score", 0.0)))
                })

        count = len(segments)
        self.bridge.set(f"{self.node_id}_Segments", segments, self.name)
        self.bridge.set(f"{self.node_id}_Count", count, self.name)
        self.logger.info(f"Found {count} segments.")
        self.bridge.set(f"{self.node_id}_ActivePorts", ["Flow"], self.name)
        return True

    def terminate(self):
        self._sam = None
        self._predictor = None
        self._generator = None
        super().terminate()
