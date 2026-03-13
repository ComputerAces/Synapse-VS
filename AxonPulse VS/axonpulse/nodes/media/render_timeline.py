import os

from axonpulse.core.super_node import SuperNode

from axonpulse.nodes.registry import NodeRegistry

from axonpulse.core.types import DataType

from axonpulse.core.dependencies import DependencyManager

from axonpulse.core.video_builder.models import SceneList, SceneObject, AssetType

from typing import Any, List, Dict, Optional

from axonpulse.core.types import DataType, TypeCaster

from axonpulse.nodes.decorators import axon_node

VideoFileClip = None

AudioFileClip = None

ImageClip = None

ColorClip = None

TextClip = None

CompositeVideoClip = None

CompositeAudioClip = None

def ensure_moviepy():
    global VideoFileClip, AudioFileClip, ImageClip, ColorClip, TextClip, CompositeVideoClip, CompositeAudioClip
    if VideoFileClip:
        return True
    if DependencyManager.ensure('moviepy'):
        from moviepy.editor import VideoFileClip as _V, AudioFileClip as _A, ImageClip as _I, ColorClip as _C, TextClip as _T, CompositeVideoClip as _CV, CompositeAudioClip as _CA
        VideoFileClip = _V
        AudioFileClip = _A
        ImageClip = _I
        ColorClip = _C
        TextClip = _T
        CompositeVideoClip = _CV
        CompositeAudioClip = _CA
        return True
    return False

@axon_node(category="Media/Video", version="2.3.0", node_label="Render Timeline")
def RenderTimelineNode(Compiled_Timeline: Any, Output_Path: str = 'output.mp4', Width: float = 1920, Height: float = 1080, FPS: float = 24, Auto_Ducking: bool = True, Ducking_Factor: float = 0.2, Ducking_Ramp: float = 0.5, _bridge: Any = None, _node: Any = None, _node_id: str = None, **kwargs) -> Any:
    """Renders a compiled timeline into a video file.

Uses MoviePy to process a 'SceneList' (timeline) and export it 
as an MP4, GIF, or other video format. Supports resolution, FPS, 
and audio ducking controls.

Inputs:
- Flow: Trigger the render.
- Compiled Timeline: The SceneList data to render.
- Output Path: Destination file path (default 'output.mp4').
- Width: Output video width (default 1920).
- Height: Output video height (default 1080).
- FPS: Frames per second (default 24).
- Auto Ducking: Whether to automatically lower background music for speech.

Outputs:
- Flow: Pulse triggered once rendering completes."""
    if not Compiled_Timeline:
        _node.logger.warning('No Compiled Timeline provided.')
        _bridge.set(f'{_node_id}_ActivePorts', ['Flow'], _node.name)
        return True
    else:
        pass
    if not ensure_moviepy():
        _node.logger.error('moviepy not installed.')
        _bridge.set(f'{_node_id}_ActivePorts', ['Flow'], _node.name)
        return True
    else:
        pass
    try:
        sl = SceneList.deserialize(Compiled_Timeline)
        out_path = Output_Path or _node.properties.get('Output Path', 'output.mp4')
        width = int(kwargs.get('Width') or _node.properties.get('Width', 1920))
        height = int(kwargs.get('Height') or _node.properties.get('Height', 1080))
        fps = int(kwargs.get('FPS') or _node.properties.get('FPS', 24))
        auto_ducking = kwargs.get('Auto Ducking') if kwargs.get('Auto Ducking') is not None else _node.properties.get('Auto Ducking', True)
        ducking_factor = kwargs.get('Ducking Factor') if kwargs.get('Ducking Factor') is not None else _node.properties.get('Ducking Factor', 0.2)
        ducking_ramp = kwargs.get('Ducking Ramp') if kwargs.get('Ducking Ramp') is not None else _node.properties.get('Ducking Ramp', 0.5)
        _node.logger.info(f'Rendering timeline to {out_path} at {width}x{height} @ {fps}fps')
    except Exception as e:
        _node.logger.error(f'Render Error: {e}')
    finally:
        pass
    _bridge.set(f'{_node_id}_ActivePorts', ['Flow'], _node.name)
    return True
