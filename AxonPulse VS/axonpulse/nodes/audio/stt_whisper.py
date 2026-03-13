from axonpulse.core.super_node import SuperNode
from axonpulse.nodes.lib.provider_node import ProviderNode
from axonpulse.nodes.registry import NodeRegistry
from axonpulse.core.types import DataType
from axonpulse.core.dependencies import DependencyManager
import os

# Lazy Globals
whisper = None

def ensure_whisper():
    global whisper
    if whisper: return True
    if DependencyManager.ensure("faster-whisper"):
        from faster_whisper import WhisperModel
        whisper = WhisperModel
        return True
    return False

class WhisperSpeechEngine:
    """Internal wrapper around faster-whisper for high accuracy."""
    
    def __init__(self, model_size="tiny", device="cpu", compute_type="int8"):
        self.model = whisper(model_size, device=device, compute_type=compute_type)

    def transcribe(self, wav_data):
        """
        Transcribes audio bytes or path to text using Whisper.
        wav_data: Bytes or path
        """
        try:
            # faster-whisper can take a path or binary stream
            segments, info = self.model.transcribe(wav_data, beam_size=5)
            
            text_segments = [segment.text for segment in segments]
            return "".join(text_segments).strip()
        except Exception as e:
            return f"Error: {str(e)}"

@NodeRegistry.register("STT Whisper Provider", "Media/Audio")
class STTWhisperProviderNode(ProviderNode):
    """
    Registers the Whisper Speech-To-Text provider for high-accuracy transcription.
    Uses 'faster-whisper' for optimized CPU/GPU execution.
    
    Inputs:
    - Flow: Start Provider Scope.
    - Model Size: Whisper model size (tiny, base, small, medium, large-v3). Default: 'tiny'.
    - Device: Execution device (cpu, cuda). Default: 'cpu'.
    
    Outputs:
    - Flow: Active pulse.
    - Provider Flow: Active Provider pulse.
    """
    version = "2.3.0"

    def __init__(self, node_id, name, bridge):
        super().__init__(node_id, name, bridge)
        self.provider_type = "STT"
        self.properties["Model Size"] = "tiny"
        self.properties["Device"] = "cpu"

    def define_schema(self):
        super().define_schema()
        self.input_schema.update({
            "Model Size": DataType.STRING,
            "Device": DataType.STRING
        })

    def start_scope(self, **kwargs):
        if not ensure_whisper():
            raise RuntimeError(f"[{self.name}] faster-whisper dependency not installed.")

        model_size = kwargs.get("Model Size") or self.properties.get("Model Size", "tiny")
        device = kwargs.get("Device") or self.properties.get("Device", "cpu")
        
        engine = WhisperSpeechEngine(model_size=model_size, device=device)
        self.bridge.set(f"{self.node_id}_Provider", engine, self.name)
        return super().start_scope(**kwargs)
