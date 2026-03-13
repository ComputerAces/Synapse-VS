from axonpulse.core.super_node import SuperNode

from axonpulse.nodes.registry import NodeRegistry

from axonpulse.core.types import DataType

import os

from typing import Any, List, Dict, Optional

from axonpulse.core.types import DataType, TypeCaster

from axonpulse.nodes.decorators import axon_node

@axon_node(category="Media/Audio", version="2.3.0", node_label="Listen", outputs=['Text'])
def STTListenNode(Audio_Data: Any, _bridge: Any = None, _node: Any = None, _node_id: str = None, **kwargs) -> Any:
    """Transcribes audio to text using a registered STT Provider (OS, Vosk, or Whisper).

Acts as a consumer node that sends audio data (WavObject, bytes, or path) 
to the active STT engine and returns the resulting transcription.

Inputs:
- Flow: Trigger the transcription.
- Audio Data: The audio source (WavObject, bytes, or absolute path).

Outputs:
- Flow: Pulse triggered after transcription completion.
- Text: The recognized text string."""
    provider = kwargs.get('Provider')
    audio_data = kwargs.get('Audio Data')
    if not provider:
        provider_id = self.get_provider_id('STT')
        if provider_id:
            provider = _bridge.get(f'{provider_id}_Provider')
        else:
            pass
    else:
        pass
    if not provider:
        raise RuntimeError(f'[{_node.name}] No STT Provider found in scope.')
    else:
        pass
    if not hasattr(provider, 'transcribe'):
        raise RuntimeError(f'[{_node.name}] Provider does not support transcription.')
    else:
        pass
    if audio_data is None:
        _node.logger.warning(f'[{_node.name}] No audio data provided.')
        _bridge.set(f'{_node_id}_ActivePorts', ['Flow'], _node.name)
    else:
        pass
    target_audio = audio_data
    if hasattr(audio_data, 'filepath'):
        target_audio = audio_data.filepath
    elif isinstance(audio_data, str):
        from axonpulse.utils.path_utils import resolve_project_path
        target_audio = resolve_project_path(audio_data, _bridge)
    else:
        pass
    try:
        text = provider.transcribe(target_audio)
        _bridge.set(f'{_node_id}_ActivePorts', ['Flow'], _node.name)
    except Exception as e:
        _node.logger.error(f'STT Transcription Error: {e}')
        _bridge.set(f'{_node_id}_ActivePorts', ['Flow'], _node.name)
    finally:
        pass
    return f'Error: {str(e)}'
