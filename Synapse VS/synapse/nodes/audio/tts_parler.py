from synapse.nodes.lib.provider_node import ProviderNode
from synapse.nodes.registry import NodeRegistry
from synapse.core.types import DataType
from synapse.core.dependencies import DependencyManager

# Lazy Globals
parler_tts_mod = None
auto_tokenizer = None

def ensure_parler():
    global parler_tts_mod, auto_tokenizer
    if parler_tts_mod: return True
    if DependencyManager.ensure("parler-tts", "parler_tts",
                                 pip_name="git+https://github.com/huggingface/parler-tts.git"):
        from parler_tts import ParlerTTSForConditionalGeneration
        from transformers import AutoTokenizer
        parler_tts_mod = ParlerTTSForConditionalGeneration
        auto_tokenizer = AutoTokenizer
        return True
    return False

class ParlerTTSEngine:
    """Internal wrapper around Parler-TTS Mini v1.1."""
    supports_cloning = False

    def __init__(self, model_name="parler-tts/parler-tts-mini-v1.1", description="", device=None):
        import torch
        self.device = device or ("cuda:0" if torch.cuda.is_available() else "cpu")
        self.model = parler_tts_mod.from_pretrained(model_name).to(self.device)
        self.tokenizer = auto_tokenizer.from_pretrained(model_name)
        self.description_tokenizer = auto_tokenizer.from_pretrained(
            self.model.config.text_encoder._name_or_path
        )
        self.description = description
        self.sample_rate = self.model.config.sampling_rate

    def synthesize(self, text, voice_ref=None):
        """
        Generate speech from text using the configured voice description.

        Returns a numpy float32 array of PCM audio at self.sample_rate.
        voice_ref is ignored (Parler does not support cloning).
        """
        import torch

        description = self.description or (
            "A female speaker delivers a slightly expressive and animated speech "
            "with a moderate speed and pitch. The recording is of very high quality, "
            "with the speaker's voice sounding clear and very close up."
        )

        input_ids = self.description_tokenizer(
            description, return_tensors="pt"
        ).input_ids.to(self.device)

        prompt_input_ids = self.tokenizer(
            text, return_tensors="pt"
        ).input_ids.to(self.device)

        with torch.no_grad():
            generation = self.model.generate(
                input_ids=input_ids,
                prompt_input_ids=prompt_input_ids
            )

        audio_arr = generation.cpu().numpy().squeeze()
        return audio_arr


@NodeRegistry.register("TTS Parler", "Media/Audio")
class TTSParlerProvider(ProviderNode):
    """
    Registers the Parler-TTS engine for speech synthesis.
    
    Initializes a provider context for Parler-TTS, which generates 
    highly expressive speech based on text descriptions.
    
    Inputs:
    - Flow: Trigger the provider initialization.
    - Model: The HuggingFace model ID for Parler-TTS.
    - Description: Natural language description of the target voice.
    
    Outputs:
    - Done: Pulse triggered once the engine is ready.
    """
    version = "2.1.0"
    required_libraries = ["parler_tts", "torch", "transformers"]

    def __init__(self, node_id, name, bridge):
        super().__init__(node_id, name, bridge)
        self.provider_type = "TTS Provider"
        self.properties["Model"] = "parler-tts/parler-tts-mini-v1.1"
        self.properties["Description"] = ""

    def define_schema(self):
        super().define_schema()
        self.input_schema.update({
            "Model": DataType.STRING,
            "Description": DataType.STRING
        })

    def start_scope(self, **kwargs):
        if not ensure_parler():
            raise RuntimeError(f"[{self.name}] parler-tts dependency not installed.")

        desc_input = kwargs.get("Description")
        description = desc_input or self.properties.get("Description", "")
        model_name = self.properties.get("Model", "parler-tts/parler-tts-mini-v1.1")

        try:
            engine = ParlerTTSEngine(
                model_name=model_name,
                description=description
            )
            self.bridge.set(f"{self.node_id}_Provider", engine, self.name)
        except Exception as e:
            raise RuntimeError(f"[{self.name}] Failed to load Parler-TTS model: {e}")

        return super().start_scope(**kwargs)
