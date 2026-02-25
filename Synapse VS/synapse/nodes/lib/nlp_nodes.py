from synapse.core.super_node import SuperNode
from synapse.nodes.registry import NodeRegistry
from synapse.core.types import DataType
from synapse.core.dependencies import DependencyManager

# Lazy Globals
SentimentIntensityAnalyzer = None
detect = None
detect_langs = None

def ensure_vader():
    global SentimentIntensityAnalyzer
    if SentimentIntensityAnalyzer: return True
    if DependencyManager.ensure("vaderSentiment"):
        from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer as _S
        SentimentIntensityAnalyzer = _S; return True
    return False

def ensure_langdetect():
    global detect, detect_langs
    if detect: return True
    if DependencyManager.ensure("langdetect"):
        from langdetect import detect as _d, detect_langs as _dl
        detect = _d; detect_langs = _dl; return True
    return False

@NodeRegistry.register("Sentiment Analysis", "AI/NLP")
class SentimentNode(SuperNode):
    """
    Analyzes the emotional tone of a text string using the VADER sentiment algorithm.
    Detects if a statement is positive, negative, or neutral.
    
    Inputs:
    - Flow: Trigger the analysis process.
    - Text: The string to be analyzed.
    
    Outputs:
    - Flow: Triggered after analysis is complete.
    - Compound Score: A normalized score between -1 (extremely negative) and +1 (extremely positive).
    - Is Positive: True if the text has a net positive sentiment.
    - Is Negative: True if the text has a net negative sentiment.
    - Is Neutral: True if the text is objectively neutral.
    """
    version = "2.1.0"

    def __init__(self, node_id, name, bridge):
        super().__init__(node_id, name, bridge)
        self.analyzer = None
        self.properties["Text"] = ""
        self.define_schema()
        self.register_handlers()

    def register_handlers(self):
        self.register_handler("Flow", self.analyze_sentiment)

    def define_schema(self):
        self.input_schema = {
            "Flow": DataType.FLOW,
            "Text": DataType.STRING
        }
        self.output_schema = {
            "Flow": DataType.FLOW,
            "Compound Score": DataType.NUMBER,
            "Is Positive": DataType.BOOLEAN,
            "Is Negative": DataType.BOOLEAN,
            "Is Neutral": DataType.BOOLEAN
        }

    def analyze_sentiment(self, Text=None, **kwargs):
        # Fallback to properties
        text = Text if Text is not None else self.properties.get("Text", "")
        if not text: 
             self.bridge.set(f"{self.node_id}_ActivePorts", ["Flow"], self.name)
             return True

        if not ensure_vader():
            self.logger.error("vaderSentiment not installed.")
            self.bridge.set(f"{self.node_id}_ActivePorts", ["Flow"], self.name)
            return True

        if not self.analyzer:
            self.analyzer = SentimentIntensityAnalyzer()

        try:
            scores = self.analyzer.polarity_scores(text)
            compound = scores['compound']
            
            # Simple thresholds
            is_pos = compound >= 0.05
            is_neg = compound <= -0.05
            is_neu = not (is_pos or is_neg)
            
            self.bridge.set(f"{self.node_id}_Compound Score", float(compound), self.name)
            self.bridge.set(f"{self.node_id}_Is Positive", is_pos, self.name)
            self.bridge.set(f"{self.node_id}_Is Negative", is_neg, self.name)
            self.bridge.set(f"{self.node_id}_Is Neutral", is_neu, self.name)
            
            self.logger.info(f"Sentiment: {compound}")

        except Exception as e:
            self.logger.error(f"Analysis Error: {e}")

        self.bridge.set(f"{self.node_id}_ActivePorts", ["Flow"], self.name)
        return True


@NodeRegistry.register("Language Detector", "AI/NLP")
class LanguageDetectorNode(SuperNode):
    """
    Identifies the primary language and confidence level of a given text string.
    Supports a wide variety of ISO language codes.
    
    Inputs:
    - Flow: Trigger the detection process.
    - Text: The string to be identified.
    
    Outputs:
    - Flow: Triggered after detection is complete.
    - Language Code: The ISO 639-1 language code of the detected language (e.g., 'en', 'fr', 'es').
    - Confidence: Probability score representing the detector's certainty (0.0 to 1.0).
    """
    version = "2.1.0"

    def __init__(self, node_id, name, bridge):
        super().__init__(node_id, name, bridge)
        self.properties["Text"] = ""
        self.define_schema()
        self.register_handlers()

    def register_handlers(self):
        self.register_handler("Flow", self.detect_language)

    def define_schema(self):
        self.input_schema = {
            "Flow": DataType.FLOW,
            "Text": DataType.STRING
        }
        self.output_schema = {
            "Flow": DataType.FLOW,
            "Language Code": DataType.STRING,
            "Confidence": DataType.NUMBER
        }

    def detect_language(self, Text=None, **kwargs):
        # Fallback to properties
        text = Text if Text is not None else self.properties.get("Text", "")
        if not text: 
             self.bridge.set(f"{self.node_id}_ActivePorts", ["Flow"], self.name)
             return True
        
        if not ensure_langdetect():
            self.logger.error("langdetect not installed.")
            self.bridge.set(f"{self.node_id}_ActivePorts", ["Flow"], self.name)
            return True

        try:
            # detect_langs returns list like [en:0.999]
            langs = detect_langs(text)
            if langs:
                top = langs[0] # Most probable
                code = top.lang
                conf = top.prob
                
                self.bridge.set(f"{self.node_id}_Language Code", code, self.name)
                self.bridge.set(f"{self.node_id}_Confidence", float(conf), self.name)
            else:
                self.bridge.set(f"{self.node_id}_Language Code", "unknown", self.name)
                self.bridge.set(f"{self.node_id}_Confidence", 0.0, self.name)

        except Exception as e:
            # langdetect throws exception on empty/no-features text
            self.logger.error(f"Detection Error: {e}")
            self.bridge.set(f"{self.node_id}_Language Code", "error", self.name)

        self.bridge.set(f"{self.node_id}_ActivePorts", ["Flow"], self.name)
        return True
