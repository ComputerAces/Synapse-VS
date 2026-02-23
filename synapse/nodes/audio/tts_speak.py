from synapse.core.super_node import SuperNode
from synapse.nodes.registry import NodeRegistry
from synapse.core.types import DataType

@NodeRegistry.register("TTS Speak", "Media/Audio")
class TTSSpeakNode(SuperNode):
    """
    Synthesizes speech from text using a registered TTS Provider.
    
    Acts as a consumer node that sends text to a 'TTS System', 'Parler', 
    or 'KaniTTS' engine and returns the resulting audio data.
    
    Inputs:
    - Flow: Trigger the synthesis.
    - Text: The text string to speak.
    - Voice Reference: Optional audio sample or embedding for voice cloning.
    - Save Path: Optional file path to save the resulting .wav file.
    
    Outputs:
    - Flow: Pulse triggered after synthesis completion.
    - Audio: Raw audio data or numpy array.
    - Sample Rate: The sample rate of the generated audio.
    """
    version = "2.1.0"

    def __init__(self, node_id, name, bridge):
        super().__init__(node_id, name, bridge)
        self.is_native = True
        self.properties["Text"] = ""
        self.properties["Save Path"] = ""
        self.define_schema()
        self.register_handlers()

    def register_handlers(self):
        self.register_handler("Flow", self.do_work)

    def define_schema(self):
        self.input_schema = {
            "Flow": DataType.FLOW,
            "Text": DataType.STRING,
            "Voice Reference": DataType.ANY,
            "Save Path": DataType.STRING
        }
        self.output_schema = {
            "Flow": DataType.FLOW,
            "Audio": DataType.ANY,
            "Sample Rate": DataType.NUMBER
        }

    def do_work(self, **kwargs):
        provider = kwargs.get("Provider")
        text = kwargs.get("Text") or self.properties.get("Text", "") or self.properties.get("Text", "")
        voice_ref = kwargs.get("Voice Reference")
        save_path = kwargs.get("Save Path") or self.properties.get("SavePath", "") or self.properties.get("Save Path", "")

        # Auto-discover provider from scope
        if not provider:
            provider_id = self.get_provider_id("TTS Provider")
            if provider_id:
                provider = self.bridge.get(f"{provider_id}_Provider")

        if not provider:
            raise RuntimeError(f"[{self.name}] No TTS Provider found in scope.")

        if not hasattr(provider, 'synthesize'):
            raise RuntimeError(f"[{self.name}] Provider does not support synthesis.")

        # Handle cloning
        if voice_ref is not None and not getattr(provider, 'supports_cloning', False):
            self.logger.warning(
                f"Voice Reference provided but {provider.__class__.__name__} "
                f"does not support cloning. Ignoring reference."
            )
            voice_ref = None

        if not text:
            self.bridge.set(f"{self.node_id}_ActivePorts", ["Flow"], self.name)
            return True

        try:
            audio = provider.synthesize(text, voice_ref=voice_ref)
            sample_rate = getattr(provider, 'sample_rate', 22050)

            self.bridge.set(f"{self.node_id}_Audio", audio, self.name)
            self.bridge.set(f"{self.node_id}_Sample Rate", sample_rate, self.name)

            # Save to file if requested
            if save_path and audio is not None:
                self._save_audio(audio, sample_rate, save_path)

            self.bridge.set(f"{self.node_id}_ActivePorts", ["Flow"], self.name)
            return True
        except Exception as e:
            self.logger.error(f"TTS Synthesis Error: {e}")
            self.bridge.set(f"{self.node_id}_ActivePorts", ["Flow"], self.name)
            return True

    def _save_audio(self, audio, sample_rate, path):
        """Write audio data to a WAV file."""
        import os
        os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)

        if isinstance(audio, (bytes, bytearray)):
            # Already WAV bytes (from System TTS)
            with open(path, "wb") as f:
                f.write(audio)
        else:
            # Numpy array — use soundfile or wave
            try:
                import soundfile as sf
                sf.write(path, audio, sample_rate)
            except ImportError:
                import wave
                import numpy as np
                audio_int16 = (audio * 32767).astype(np.int16)
                with wave.open(path, 'w') as wf:
                    wf.setnchannels(1)
                    wf.setsampwidth(2)
                    wf.setframerate(sample_rate)
                    wf.writeframes(audio_int16.tobytes())

        self.logger.info(f"Saved audio to {os.path.basename(path)}")
