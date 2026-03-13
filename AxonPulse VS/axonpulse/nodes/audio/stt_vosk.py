from axonpulse.core.super_node import SuperNode
from axonpulse.nodes.lib.provider_node import ProviderNode
from axonpulse.nodes.registry import NodeRegistry
from axonpulse.core.types import DataType
from axonpulse.core.dependencies import DependencyManager
from axonpulse.nodes.audio.stt_utils import ensure_vosk_model
import io
import json
import wave

# Lazy Globals
vosk = None

def ensure_vosk():
    global vosk
    if vosk: return True
    if DependencyManager.ensure("vosk"):
        import vosk as _v; vosk = _v; return True
    return False

class VoskSpeechEngine:
    """Internal wrapper around Vosk for the offline provider."""
    
    def __init__(self, model_path):
        self.model = vosk.Model(model_path)
        self.recognizer = None

    def transcribe(self, wav_data):
        """
        Transcribes audio bytes to text using Vosk.
        wav_data: Bytes or path
        """
        try:
            if isinstance(wav_data, str):
                wf = wave.open(wav_data, "rb")
            else:
                wf = wave.open(io.BytesIO(wav_data), "rb")

            if wf.getnchannels() != 1 or wf.getsampwidth() != 2 or wf.getcomptype() != "NONE":
                # Vosk prefers mono 16-bit PCM
                pass # In a production scenario, we should convert here if needed

            rec = vosk.KaldiRecognizer(self.model, wf.getframerate())
            rec.SetWords(True)

            while True:
                data = wf.readframes(4000)
                if len(data) == 0:
                    break
                rec.AcceptWaveform(data)

            result = json.loads(rec.FinalResult())
            return result.get("text", "")
        except Exception as e:
            return f"Error: {str(e)}"

@NodeRegistry.register("STT Vosk Provider", "Media/Audio")
class STTVoskProviderNode(ProviderNode):
    """
    Registers the Vosk Speech-To-Text provider for high-speed offline transcription.
    Automatically downloads the ~50MB English model on first use.
    
    Inputs:
    - Flow: Start Provider Scope.
    - Model Name: Vosk model to use (default: 'vosk-model-small-en-us-0.15').
    
    Outputs:
    - Flow: Active pulse.
    - Provider Flow: Active Provider pulse.
    """
    version = "2.3.0"

    def __init__(self, node_id, name, bridge):
        super().__init__(node_id, name, bridge)
        self.provider_type = "STT"
        self.properties["Model Name"] = "vosk-model-small-en-us-0.15"

    def define_schema(self):
        super().define_schema()
        self.input_schema.update({
            "Model Name": DataType.STRING
        })

    def start_scope(self, **kwargs):
        if not ensure_vosk():
            raise RuntimeError(f"[{self.name}] Vosk dependency not installed.")

        model_name = kwargs.get("Model Name") or self.properties.get("Model Name", "vosk-model-small-en-us-0.15")
        
        model_path = ensure_vosk_model(model_name)
        if not model_path:
            raise RuntimeError(f"[{self.name}] Failed to download/ensure Vosk model: {model_name}")

        engine = VoskSpeechEngine(model_path=model_path)
        self.bridge.set(f"{self.node_id}_Provider", engine, self.name)
        return super().start_scope(**kwargs)
