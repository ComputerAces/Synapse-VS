from typing import List, Dict, Any, Optional, Union
from enum import Enum

class AssetType(Enum):
    VIDEO = "video"
    AUDIO = "audio"
    IMAGE = "image"
    SHAPE = "shape"
    TEXT = "text"

class SceneObject:
    """
    Represents a single media instruction in the timeline.
    No heavy media is loaded here, only reference paths and parameters.
    """
    def __init__(self, 
                 asset_path: str, 
                 asset_type: AssetType,
                 start_time: float = 0.0,
                 duration: Optional[float] = None,
                 z_index: int = 0):
        self.asset_path = asset_path
        self.asset_type = asset_type
        self.start_time = start_time
        self.duration = duration
        self.z_index = z_index
        
        # Transform properties
        self.position = [0.0, 0.0] # x,y
        self.scale = [1.0, 1.0] # w,h
        self.rotation = 0.0
        self.opacity = 1.0
        
        # Additional metadata (Shape properties, Text content, etc.)
        self.meta: Dict[str, Any] = {}
        
    def to_dict(self) -> Dict[str, Any]:
        return {
            "path": self.asset_path,
            "type": self.asset_type.value,
            "start": self.start_time,
            "duration": self.duration,
            "z": self.z_index,
            "pos": self.position,
            "scale": self.scale,
            "rot": self.rotation,
            "opacity": self.opacity,
            "meta": self.meta
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'SceneObject':
        obj = cls(
            asset_path=data.get("path", ""),
            asset_type=AssetType(data.get("type", "video")),
            start_time=data.get("start", 0.0),
            duration=data.get("duration"),
            z_index=data.get("z", 0)
        )
        obj.position = data.get("pos", [0.0, 0.0])
        obj.scale = data.get("scale", [1.0, 1.0])
        obj.rotation = data.get("rot", 0.0)
        obj.opacity = data.get("opacity", 1.0)
        obj.meta = data.get("meta", {})
        return obj

class SceneList:
    """
    A collection of SceneObjects representing a complete timeline.
    """
    def __init__(self, objects: Optional[List[SceneObject]] = None):
        self.objects = objects or []
        
    def add(self, obj: SceneObject):
        self.objects.append(obj)
        
    def sort(self):
        """Sort by Layer (Z) then by Time."""
        self.objects.sort(key=lambda x: (x.z_index, x.start_time))
        
    def get_duration(self) -> float:
        """Calculates the total duration of the timeline."""
        if not self.objects: return 0.0
        max_end = 0.0
        for obj in self.objects:
            end = obj.start_time + (obj.duration or 0)
            if end > max_end: max_end = end
        return max_end
        
    def serialize(self) -> List[Dict[str, Any]]:
        return [obj.to_dict() for obj in self.objects]
        
    @classmethod
    def deserialize(cls, data: List[Dict[str, Any]]) -> 'SceneList':
        return cls([SceneObject.from_dict(d) for d in data])
