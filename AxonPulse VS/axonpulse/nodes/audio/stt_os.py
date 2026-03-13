from axonpulse.core.super_node import SuperNode
from axonpulse.nodes.lib.provider_node import ProviderNode
from axonpulse.nodes.registry import NodeRegistry
from axonpulse.core.types import DataType
from axonpulse.core.dependencies import DependencyManager
import io

# Lazy Globals
sr = None

def ensure_sr():
    global sr
    if sr: return True
    if DependencyManager.ensure("SpeechRecognition"):
        import speech_recognition as _sr; sr = _sr; return True
    return False

class OSSpeechEngine:
    """Internal wrapper around SpeechRecognition for the OS provider."""
    
    def __init__(self, language="en-US"):
        self.language = language
        self.recognizer = sr.Recognizer()

    def transcribe(self, wav_data):
        """
        Transcribes audio bytes to text using Google Web Speech API.
        wav_data: Bytes or path
        """
        try:
            if isinstance(wav_data, str):
                with sr.AudioFile(wav_data) as source:
                    audio = self.recognizer.record(source)
            else:
                # Assume bytes (WAV format)
                audio_data = io.BytesIO(wav_data)
                with sr.AudioFile(audio_data) as source:
                    audio = self.recognizer.record(source)
            
            # Google Web Speech API (free, no key required for low volume)
            text = self.recognizer.recognize_google(audio, language=self.language)
            return text
        except Exception as e:
            return f"Error: {str(e)}"

@NodeRegistry.register("STT OS Provider", "Media/Audio")
class STTOSProviderNode(ProviderNode):
    """
    Registers the default system/OS Speech-To-Text provider.
    Uses the 'SpeechRecognition' library which acts as a wrapper for Various APIs.
    By default, uses Google Web Speech API (requires internet).
    
    Inputs:
    - Flow: Start Provider Scope.
    - Language: BCP-47 language tag (default: 'en-US').
    
    Outputs:
    - Flow: Active pulse.
    - Provider Flow: Active Provider pulse.
    """
    version = "2.3.0"

    def __init__(self, node_id, name, bridge):
        super().__init__(node_id, name, bridge)
        self.provider_type = "STT"
        self.properties["Language"] = "en-US"

    def define_schema(self):
        super().define_schema()
        self.input_schema.update({
            "Language": DataType.STRING
        })

    def start_scope(self, **kwargs):
        if not ensure_sr():
            raise RuntimeError(f"[{self.name}] SpeechRecognition dependency not installed.")

        language = kwargs.get("Language") or self.properties.get("Language", "en-US")
        
        engine = OSSpeechEngine(language=language)
        self.bridge.set(f"{self.node_id}_Provider", engine, self.name)
        return super().start_scope(**kwargs)
