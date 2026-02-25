from synapse.core.node import BaseNode
from synapse.nodes.registry import NodeRegistry
from synapse.core.types import DataType
from synapse.core.dependencies import DependencyManager
import re
import json # for fallback serialization of strategy

# ==============================================================================
# Base Provider
# ==============================================================================

from synapse.core.super_node import SuperNode

@NodeRegistry.register("Chunking Provider", "AI/Chunking")
class ChunkingProvider(SuperNode):
    """
    Base class for nodes that provide text chunking strategies.
    Registers a chunking strategy and optional configuration in the bridge.
    
    Inputs:
    - Flow: Trigger execution to register the provider.
    - Text: Optional text to chunk immediately upon registration.
    
    Outputs:
    - Flow: Triggered after registration (and optional chunking) is complete.
    - Chunks: The result of chunking the input text (if provided).
    """
    version = "2.1.0"
    def __init__(self, node_id, name, bridge):
        super().__init__(node_id, name, bridge)
        self.is_service = True 
        self.is_native = True
        self.define_schema()
        self.register_handlers()

    def register_handlers(self):
        self.register_handler("Flow", self.register_provider)

    def define_schema(self):
        self.input_schema = {
            "Flow": DataType.FLOW,
            "Text": DataType.STRING
        }
        self.output_schema = {
            "Flow": DataType.FLOW,
            "Chunks": DataType.LIST
        }

    def chunk(self, text, **kwargs):
        """Override this! Returns list of strings."""
        return [text]

    def register_provider(self, **kwargs):
        # 1. Register Provider
        self.bridge.set(f"{self.node_id}_Provider Type", "Chunking Provider", self.name)
        strategy_name = self.__class__.__name__
        self.bridge.set(f"{self.node_id}_ChunkStrategy", strategy_name, self.name)
        
        relevant_props = ["ChunkSize", "OverlapSize", "MaxChunkSize"]
        config = {k: self.properties.get(k) for k in relevant_props if k in self.properties}
        self.bridge.set(f"{self.node_id}_ChunkConfig", json.dumps(config), self.name)
        
        # 2. Perform Chunking if Text is provided
        text = kwargs.get("Text") or self.properties.get("Text")
        if text:
            chunks = self.chunk(text, **kwargs)
            self.bridge.set(f"{self.node_id}_Chunks", chunks, self.name)
        
        self.bridge.set(f"{self.node_id}_ActivePorts", ["Flow"], self.name)
        return True

# ==============================================================================
# Concrete Providers
# ==============================================================================

@NodeRegistry.register("Fixed Size Chunking", "AI/Chunking")
class FixedSizeChunkingNode(ChunkingProvider, SuperNode):
    """
    Splits text into chunks of a constant character length, with optional overlap.
    
    Inputs:
    - Flow: Trigger execution and register as a chunking provider.
    - Text: Optional text to chunk immediately.
    - ChunkSize: The desired length of each chunk in characters (default: 1000).
    - OverlapSize: Number of characters to overlap between adjacent chunks (default: 200).
    
    Outputs:
    - Flow: Triggered after registration/chunking.
    - Chunks: List of generated text chunks.
    """
    version = "2.1.0"

    def __init__(self, node_id, name, bridge):
        super().__init__(node_id, name, bridge)
        self.properties["ChunkSize"] = 1000
        self.properties["OverlapSize"] = 200
        self.define_schema()

    def define_schema(self):
        super().define_schema()
        self.input_schema["ChunkSize"] = DataType.INTEGER
        self.input_schema["OverlapSize"] = DataType.INTEGER

    def chunk(self, text, **kwargs):
        chunk_size = kwargs.get("ChunkSize") or self.properties.get("ChunkSize", 1000)
        overlap_size = kwargs.get("OverlapSize") or self.properties.get("OverlapSize", 200)

        if not text:
            return []
        
        chunks = []
        start = 0
        while start < len(text):
            end = min(start + chunk_size, len(text))
            chunks.append(text[start:end])
            start += chunk_size - overlap_size
            if start >= len(text):
                break
            if chunk_size - overlap_size <= 0: # prevent infinite loop
                start += chunk_size
                
        return chunks
    
# ...

@NodeRegistry.register("Sentence Chunking", "AI/Chunking")
class SentenceChunkingNode(ChunkingProvider, SuperNode):
    """
    Splits text into chunks based on sentence boundaries (. ! ?).
    
    Inputs:
    - Flow: Trigger execution and register as a chunking provider.
    - Text: Optional text to chunk immediately.
    
    Outputs:
    - Flow: Triggered after registration/chunking.
    - Chunks: List of generated sentences.
    """
    version = "2.1.0"

    def __init__(self, node_id, name, bridge):
        super().__init__(node_id, name, bridge)
        self.define_schema()

    def define_schema(self):
        super().define_schema()
        self.input_schema["Flow"] = DataType.FLOW
        self.output_schema["Flow"] = DataType.FLOW

    def chunk(self, text, **kwargs):
        if not text:
            return []
        # Basic split by period followed by space
        sentences = re.split(r'(?<=[.!?]) +', text)
        return [s.strip() for s in sentences if s.strip()]
    
# ...

@NodeRegistry.register("Paragraph Chunking", "AI/Chunking")
class ParagraphChunkingNode(ChunkingProvider, SuperNode):
    """
    Splits text into chunks based on paragraph boundaries (double newlines).
    
    Inputs:
    - Flow: Trigger execution and register as a chunking provider.
    - Text: Optional text to chunk immediately.
    
    Outputs:
    - Flow: Triggered after registration/chunking.
    - Chunks: List of generated paragraphs.
    """
    version = "2.1.0"

    def __init__(self, node_id, name, bridge):
        super().__init__(node_id, name, bridge)
        self.define_schema()

    def define_schema(self):
        super().define_schema()
        self.input_schema["Flow"] = DataType.FLOW
        self.output_schema["Flow"] = DataType.FLOW

    def chunk(self, text, **kwargs):
        if not text:
            return []
        # Basic split by double newline
        paragraphs = re.split(r'\n\s*\n', text)
        return [p.strip() for p in paragraphs if p.strip()]

# ...

@NodeRegistry.register("Semantic Chunking", "AI/Chunking")
class SemanticChunkingNode(ChunkingProvider, SuperNode):
    """
    Splits text into semantic chunks by grouping paragraphs together up to a maximum size.
    
    Inputs:
    - Flow: Trigger execution and register as a chunking provider.
    - Text: Optional text to chunk immediately.
    - MaxChunkSize: The maximum allowed length for a combined chunk (default: 1000).
    
    Outputs:
    - Flow: Triggered after registration/chunking.
    - Chunks: List of combined semantic chunks.
    """
    version = "2.1.0"

    def __init__(self, node_id, name, bridge):
        super().__init__(node_id, name, bridge)
        self.properties["MaxChunkSize"] = 1000
        self.define_schema()

    def define_schema(self):
        super().define_schema()
        self.input_schema["Flow"] = DataType.FLOW
        self.output_schema["Flow"] = DataType.FLOW
        self.input_schema["MaxChunkSize"] = DataType.INTEGER

    def chunk(self, text, MaxChunkSize=None, **kwargs):
        # A basic "semantic" chunking without a model.
        # Fallback implementation.
        if max_chunk_size is None:
            max_chunk_size = self.properties.get("MaxChunkSize", 1000)
        
        if not text: return []
        
        # Split by paragraph first
        paragraphs = re.split(r'\n\s*\n', text)
        chunks = []
        current_chunk = ""
        
        for p in paragraphs:
            if len(current_chunk) + len(p) < max_chunk_size:
                current_chunk += p + "\n\n"
            else:
                if current_chunk:
                    chunks.append(current_chunk.strip())
                # If a single paragraph is larger than max_chunk_size, we just add it anyway.
                current_chunk = p + "\n\n"
        
        if current_chunk:
            chunks.append(current_chunk.strip())
            
        return chunks

# ...

@NodeRegistry.register("Chunk String", "AI/Chunking")
class ChunkStringNode(SuperNode):
    """
    Uses an AI Provider to perform intelligent semantic chunking of input text.
    If no AI Provider is available, it attempts to use a Chunking Provider or falls back to basic rules.
    
    Inputs:
    - Flow: Trigger execution.
    - Text: The text string to be chunked.
    - System Prompt: Instructions for the AI on how to perform chunking.
    
    Outputs:
    - Flow: Triggered after chunking is complete.
    - Chunks: The resulting list of text chunks.
    - Error Flow: Triggered if AI-based chunking fails.
    """
    version = "2.1.0"
    
    def __init__(self, node_id, name, bridge):
        super().__init__(node_id, name, bridge)
        self.required_providers = ["AI"]
        self.is_native = True
        self.define_schema()
        self.register_handlers()

    def register_handlers(self):
        self.register_handler("Flow", self.chunk_text)

    def define_schema(self):
        self.input_schema = {
            "Flow": DataType.FLOW,
            "Text": DataType.STRING,
            "System Prompt": DataType.STRING
        }
        self.output_schema = {
            "Flow": DataType.FLOW,
            "Chunks": DataType.LIST,
            "Error Flow": DataType.FLOW
        }
        
    def chunk_text(self, **kwargs):
        text = kwargs.get("Text") or self.properties.get("Text")
        system_prompt = kwargs.get("System Prompt") or self.properties.get("System Prompt")
        
        if not text:
            self.bridge.set(f"{self.node_id}_ActivePorts", ["Flow"], self.name)
            return True
        
        # Use AI Provider for semantic chunking as requested
        provider_id = self.get_provider_id("AI")
        provider = self.bridge.get(f"{provider_id}_Provider") if provider_id else None
        
        if not provider:
            # Fallback to local rule-based chunking if no AI provider
            chunking_provider_id = self.get_provider_id("Chunking Provider")
            if chunking_provider_id:
                strategy_name = self.bridge.get(f"{chunking_provider_id}_ChunkStrategy")
                config_json = self.bridge.get(f"{chunking_provider_id}_ChunkConfig")
                config = json.loads(config_json) if config_json else {}
                
                try:
                    chunks = ChunkingStrategy.execute_strategy(strategy_name, text, config)
                    self.bridge.set(f"{self.node_id}_Chunks", chunks, self.name)
                    self.bridge.set(f"{self.node_id}_ActivePorts", ["Flow"], self.name)
                    return True
                except:
                    pass

            self.logger.warning("No Provider found. Returning full text.")
            self.bridge.set(f"{self.node_id}_Chunks", [text], self.name)
            self.bridge.set(f"{self.node_id}_ActivePorts", ["Flow"], self.name)
            return True

        if not system_prompt:
            system_prompt = "You are a text chunking assistant. Break the following text into logical, semantic chunks. Each chunk should be a standalone coherent piece of information. Return the result EXCLUSIVELY as a JSON object with a key 'chunks' containing a list of strings."

        try:
            response = provider.generate(
                system_prompt=system_prompt,
                user_prompt=f"Text to chunk:\n{text}",
                return_json=True
            )
            
            if isinstance(response, str):
                try:
                    # Extraction logic if provider returned raw string instead of dict
                    start = response.find('{')
                    end = response.rfind('}') + 1
                    if start != -1 and end != 0:
                        data = json.loads(response[start:end])
                    else:
                        raise ValueError("No JSON found in AI response")
                except:
                    data = {"chunks": [response]}
            else:
                data = response

            chunks = data.get("chunks", [text])
            self.bridge.set(f"{self.node_id}_Chunks", chunks, self.name)
        except Exception as e:
            self.logger.error(f"AI Chunking failed: {e}")
            self.bridge.set(f"{self.node_id}_ActivePorts", ["Error Flow", "Flow"], self.name)
            return True
            
        self.bridge.set(f"{self.node_id}_ActivePorts", ["Flow"], self.name)
        return True

class ChunkingStrategy:
    @staticmethod
    def execute_strategy(name, text, config):
        if name == "FixedSizeChunkingNode":
            size = config.get("ChunkSize", 1000)
            overlap = config.get("OverlapSize", 200)
            chunks = []
            start = 0
            while start < len(text):
                end = min(start + size, len(text))
                chunks.append(text[start:end])
                start += size - overlap
                if start >= len(text) or size - overlap <= 0: break
            return chunks
        elif name == "SentenceChunkingNode":
            sentences = re.split(r'(?<=[.!?]) +', text)
            return [s.strip() for s in sentences if s.strip()]
        elif name == "ParagraphChunkingNode":
            paragraphs = re.split(r'\n\s*\n', text)
            return [p.strip() for p in paragraphs if p.strip()]
        elif name == "SemanticChunkingNode":
            max_size = config.get("MaxChunkSize", 1000)
            paragraphs = re.split(r'\n\s*\n', text)
            chunks = []
            current = ""
            for p in paragraphs:
                if len(current) + len(p) < max_size:
                    current += p + "\n\n"
                else:
                    if current: chunks.append(current.strip())
                    current = p + "\n\n"
            if current: chunks.append(current.strip())
            return chunks
        return [text]
