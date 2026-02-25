from synapse.core.super_node import SuperNode
from synapse.nodes.lib.provider_node import ProviderNode
from synapse.nodes.registry import NodeRegistry
from synapse.core.types import DataType
from synapse.core.dependencies import DependencyManager
import os
import tempfile

# Lazy Globals
pyttsx3 = None

def ensure_tts():
    global pyttsx3
    if pyttsx3: return True
    if DependencyManager.ensure("pyttsx3"):
        import pyttsx3 as _t; pyttsx3 = _t; return True
    return False

class SystemTTSEngine:
    """Internal wrapper around pyttsx3 for the provider pattern."""
    supports_cloning = False
    sample_rate = 22050

    def __init__(self, rate=200, volume=1.0, voice_index=0):
        self.rate = rate
        self.volume = volume
        self.voice_index = voice_index

    def synthesize(self, text, voice_ref=None):
        """
        Speak text and return WAV bytes.

        Uses pyttsx3's save_to_file to capture audio to a temp WAV,
        then reads it back as raw bytes. Also plays through speakers.
        """
        engine = pyttsx3.init()
        engine.setProperty('rate', int(self.rate))
        engine.setProperty('volume', float(self.volume))

        voices = engine.getProperty('voices')
        if voices and 0 <= self.voice_index < len(voices):
            engine.setProperty('voice', voices[self.voice_index].id)

        tmp = tempfile.NamedTemporaryFile(suffix=".wav", delete=False)
        tmp_path = tmp.name
        tmp.close()

        try:
            engine.save_to_file(text, tmp_path)
            engine.runAndWait()
            engine.stop()

            with open(tmp_path, "rb") as f:
                wav_bytes = f.read()
            return wav_bytes
        finally:
            if os.path.exists(tmp_path):
                os.remove(tmp_path)


@NodeRegistry.register("TTS System", "Media/Audio")
class TTSSystemProvider(ProviderNode):
    """
    Registers the system's native Text-to-Speech engine.
    
    Initializes a provider context using pyttsx3. This engine is cross-platform
    and does not require an internet connection. Other 'Speak' nodes use 
    this provider to synthesize audio.
    
    Inputs:
    - Flow: Trigger the provider initialization.
    - Rate: Speech rate in words per minute (default 200).
    - Volume: Speech volume from 0.0 to 1.0 (default 1.0).
    - VoiceIndex: Index of the system voice to use (default 0).
    
    Outputs:
    - Done: Pulse triggered once the engine is ready.
    """
    version = "2.1.0"

    def __init__(self, node_id, name, bridge):
        super().__init__(node_id, name, bridge)
        self.provider_type = "TTS Provider"
        self.properties["Rate"] = 200
        self.properties["Volume"] = 1.0
        self.properties["VoiceIndex"] = 0

    def define_schema(self):
        super().define_schema()
        self.input_schema.update({
            "Rate": DataType.NUMBER,
            "Volume": DataType.NUMBER,
            "VoiceIndex": DataType.NUMBER
        })

    def start_scope(self, **kwargs):
        if not ensure_tts():
            raise RuntimeError(f"[{self.name}] pyttsx3 dependency not installed.")

        rate = kwargs.get("Rate") or self.properties.get("Rate", 200)
        volume = kwargs.get("Volume") or self.properties.get("Volume", 1.0)
        voice_index = kwargs.get("VoiceIndex") or self.properties.get("VoiceIndex", 0)

        engine = SystemTTSEngine(
            rate=rate,
            volume=volume,
            voice_index=voice_index
        )
        self.bridge.set(f"{self.node_id}_Provider", engine, self.name)
        return super().start_scope(**kwargs)
