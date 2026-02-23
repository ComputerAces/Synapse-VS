from synapse.nodes.lib.provider_node import ProviderNode
from synapse.nodes.registry import NodeRegistry
from synapse.core.types import DataType
from synapse.core.dependencies import DependencyManager

# Lazy Globals
kani_tts_mod = None
speaker_embedder_mod = None

def ensure_kanitts():
    global kani_tts_mod, speaker_embedder_mod
    if kani_tts_mod: return True
    if DependencyManager.ensure("kani-tts-2", "kani_tts"):
        from kani_tts import KaniTTS, SpeakerEmbedder
        kani_tts_mod = KaniTTS
        speaker_embedder_mod = SpeakerEmbedder
        return True
    return False

class KaniTTSEngine:
    """Internal wrapper around KaniTTS-2 with voice cloning support."""
    supports_cloning = True

    def __init__(self, model_name, temperature=1.0, top_p=0.95,
                 repetition_penalty=1.1, device=None):
        self.model = kani_tts_mod(
            model_name,
            suppress_logs=True,
            show_info=False
        )
        self.embedder = speaker_embedder_mod(device=device or "cpu")
        self.temperature = temperature
        self.top_p = top_p
        self.repetition_penalty = repetition_penalty
        self.sample_rate = 24000  # KaniTTS2 default

    def synthesize(self, text, voice_ref=None):
        """
        Generate speech, optionally cloning a reference voice.

        Args:
            text: The text to synthesize.
            voice_ref: Path to a WAV file, raw numpy array, or a saved 
                       .pt embedding file for voice cloning. None for default voice.
        Returns:
            numpy float32 array of PCM audio at self.sample_rate.
        """
        speaker_emb = None

        if voice_ref is not None:
            if isinstance(voice_ref, str):
                if voice_ref.endswith(".pt"):
                    speaker_emb = self.model.load_speaker_embedding(voice_ref)
                else:
                    speaker_emb = self.embedder.embed_audio_file(voice_ref)
            else:
                # Assume numpy array
                speaker_emb = self.embedder.embed_audio(voice_ref, sample_rate=16000)

        audio, _ = self.model(
            text,
            speaker_emb=speaker_emb,
            temperature=self.temperature,
            top_p=self.top_p,
            repetition_penalty=self.repetition_penalty
        )
        return audio


@NodeRegistry.register("TTS KaniTTS2", "Media/Audio")
class TTSKaniTTSProvider(ProviderNode):
    """
    Registers the KaniTTS-2 engine for speech synthesis.
    
    Initializes a provider context for KaniTTS-2, which supports high-quality 
    voice cloning. Other 'Speak' nodes can use this provider by specifying 
    the 'TTS Provider' relationship.
    
    Inputs:
    - Flow: Trigger the provider initialization.
    - Model: The HuggingFace model ID or local path for KaniTTS.
    - Temperature: Generation temperature (default 1.0).
    - TopP: Top-P sampling threshold (default 0.95).
    - Repetition Penalty: Penalty for repeating tokens (default 1.1).
    
    Outputs:
    - Done: Pulse triggered once the engine is ready.
    """
    version = "2.1.0"
    required_libraries = ["kanitts", "torch"]

    def __init__(self, node_id, name, bridge):
        super().__init__(node_id, name, bridge)
        self.provider_type = "TTS Provider"
        self.properties["Model"] = ""
        self.properties["Temperature"] = 1.0
        self.properties["TopP"] = 0.95

    def define_schema(self):
        super().define_schema()
        self.input_schema.update({
            "Model": DataType.STRING,
            "Temperature": DataType.NUMBER,
            "TopP": DataType.NUMBER
        })

    def start_scope(self, **kwargs):
        if not ensure_kanitts():
            raise RuntimeError(f"[{self.name}] kani-tts-2 dependency not installed.")

        model_input = kwargs.get("Model")
        model_name = model_input or self.properties.get("Model", "")

        if not model_name:
            raise RuntimeError(f"[{self.name}] No model name specified. Set the 'model' property to a HuggingFace model ID.")

        try:
            engine = KaniTTSEngine(
                model_name=model_name,
                temperature=self.properties.get("Temperature", 1.0),
                top_p=self.properties.get("TopP", 0.95),
                repetition_penalty=1.1
            )
            self.bridge.set(f"{self.node_id}_Provider", engine, self.name)
        except Exception as e:
            raise RuntimeError(f"[{self.name}] Failed to load KaniTTS-2 model: {e}")

        return super().start_scope(**kwargs)
