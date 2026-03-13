from axonpulse.core.super_node import SuperNode

from axonpulse.nodes.registry import NodeRegistry

from axonpulse.core.types import DataType

from axonpulse.core.dependencies import DependencyManager

from typing import Any, List, Dict, Optional

from axonpulse.core.types import DataType, TypeCaster

from axonpulse.nodes.decorators import axon_node

SentimentIntensityAnalyzer = None

detect = None

detect_langs = None

def ensure_vader():
    global SentimentIntensityAnalyzer
    if SentimentIntensityAnalyzer:
        return True
    if DependencyManager.ensure('vaderSentiment'):
        from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer as _S
        SentimentIntensityAnalyzer = _S
        return True
    return False

def ensure_langdetect():
    global detect, detect_langs
    if detect:
        return True
    if DependencyManager.ensure('langdetect'):
        from langdetect import detect as _d, detect_langs as _dl
        detect = _d
        detect_langs = _dl
        return True
    return False

@axon_node(category="AI/NLP", version="2.3.0", node_label="Sentiment Analysis", outputs=['Compound Score', 'Is Positive', 'Is Negative', 'Is Neutral'])
def SentimentNode(Text: str = '', _bridge: Any = None, _node: Any = None, _node_id: str = None, **kwargs) -> Any:
    """Analyzes the emotional tone of a text string using the VADER sentiment algorithm.
Detects if a statement is positive, negative, or neutral.

Inputs:
- Flow: Trigger the analysis process.
- Text: The string to be analyzed.

Outputs:
- Flow: Triggered after analysis is complete.
- Compound Score: A normalized score between -1 (extremely negative) and +1 (extremely positive).
- Is Positive: True if the text has a net positive sentiment.
- Is Negative: True if the text has a net negative sentiment.
- Is Neutral: True if the text is objectively neutral."""
    text = Text if Text is not None else _node.properties.get('Text', '')
    if not text:
        _bridge.set(f'{_node_id}_ActivePorts', ['Flow'], _node.name)
    else:
        pass
    if not ensure_vader():
        _node.logger.error('vaderSentiment not installed.')
        _bridge.set(f'{_node_id}_ActivePorts', ['Flow'], _node.name)
    else:
        pass
    if not self.analyzer:
        self.analyzer = SentimentIntensityAnalyzer()
    else:
        pass
    try:
        scores = self.analyzer.polarity_scores(text)
        compound = scores['compound']
        is_pos = compound >= 0.05
        is_neg = compound <= -0.05
        is_neu = not (is_pos or is_neg)
        _node.logger.info(f'Sentiment: {compound}')
    except Exception as e:
        _node.logger.error(f'Analysis Error: {e}')
    finally:
        pass
    _bridge.set(f'{_node_id}_ActivePorts', ['Flow'], _node.name)
    return {'Compound Score': float(compound), 'Is Positive': is_pos, 'Is Negative': is_neg, 'Is Neutral': is_neu}


@axon_node(category="AI/NLP", version="2.3.0", node_label="Language Detector", outputs=['Language Code', 'Confidence'])
def LanguageDetectorNode(Text: str = '', _bridge: Any = None, _node: Any = None, _node_id: str = None, **kwargs) -> Any:
    """Identifies the primary language and confidence level of a given text string.
Supports a wide variety of ISO language codes.

Inputs:
- Flow: Trigger the detection process.
- Text: The string to be identified.

Outputs:
- Flow: Triggered after detection is complete.
- Language Code: The ISO 639-1 language code of the detected language (e.g., 'en', 'fr', 'es').
- Confidence: Probability score representing the detector's certainty (0.0 to 1.0)."""
    text = Text if Text is not None else _node.properties.get('Text', '')
    if not text:
        _bridge.set(f'{_node_id}_ActivePorts', ['Flow'], _node.name)
    else:
        pass
    if not ensure_langdetect():
        _node.logger.error('langdetect not installed.')
        _bridge.set(f'{_node_id}_ActivePorts', ['Flow'], _node.name)
    else:
        pass
    try:
        langs = detect_langs(text)
        if langs:
            top = langs[0]
            code = top.lang
            conf = top.prob
        else:
            pass
    except Exception as e:
        _node.logger.error(f'Detection Error: {e}')
    finally:
        pass
    _bridge.set(f'{_node_id}_ActivePorts', ['Flow'], _node.name)
    return {'Language Code': code, 'Confidence': float(conf), 'Language Code': 'unknown', 'Confidence': 0.0, 'Language Code': 'error'}
