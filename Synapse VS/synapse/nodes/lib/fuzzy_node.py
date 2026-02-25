"""
Fuzzy Search & Automated Spell Check Node.

Combines data cleaning and validation into an automated pipeline:
  1. Fuzzy Match (rapidfuzz) raw text against a target.
  2. If below threshold, run Spell Check (pyspellchecker) to fix typos.
  3. Re-score corrected text.
  4. Route to "Ambiguous" flow if still below threshold.
"""
from synapse.core.super_node import SuperNode
from synapse.nodes.registry import NodeRegistry
from synapse.core.types import DataType
from synapse.core.dependencies import DependencyManager


# Lazy Globals
rapidfuzz_fuzz = None
PySpellChecker = None

def ensure_rapidfuzz():
    global rapidfuzz_fuzz
    if rapidfuzz_fuzz: return True
    if DependencyManager.ensure("rapidfuzz"):
        from rapidfuzz import fuzz as _f; rapidfuzz_fuzz = _f; return True
    return False

def ensure_spellchecker():
    global PySpellChecker
    if PySpellChecker: return True
    if DependencyManager.ensure("pyspellchecker", "spellchecker"):
        from spellchecker import SpellChecker as _S; PySpellChecker = _S; return True
    return False


def _fuzzy_score(text, target):
    """
    Computes fuzzy match score (0-100) between text and target.
    Uses rapidfuzz if available, falls back to simple ratio.
    """
    if rapidfuzz_fuzz:
        return rapidfuzz_fuzz.ratio(text, target)
    else:
        if not text or not target:
            return 0.0
        common = set(text.lower()) & set(target.lower())
        return (len(common) / max(len(set(text.lower())), len(set(target.lower())))) * 100


def _spell_correct(text):
    """
    Runs spell correction on each word using pyspellchecker.
    Returns corrected text string.
    """
    if not PySpellChecker:
        return text 

    spell = PySpellChecker()
    words = text.split()
    corrected = []

    for word in words:
        stripped = word.strip(".,;:!?\"'()[]{}")
        if not stripped.isalpha():
            corrected.append(word)
            continue

        correction = spell.correction(stripped)
        if correction and correction != stripped:
            if stripped[0].isupper():
                correction = correction.capitalize()
            corrected.append(word.replace(stripped, correction))
        else:
            corrected.append(word)

    return " ".join(corrected)


def _word_confidences(text, target):
    """
    Computes per-word fuzzy confidence against the target.
    Returns list of integers (0-100) for each word in text.
    """
    words = text.split()
    target_words = target.split()
    scores = []

    for i, word in enumerate(words):
        if i < len(target_words):
            if rapidfuzz_fuzz:
                score = int(rapidfuzz_fuzz.ratio(word, target_words[i]))
            else:
                score = 100 if word.lower() == target_words[i].lower() else 0
        else:
            score = 0
        scores.append(score)

    return scores


@NodeRegistry.register("Fuzzy Search", "Logic/Fuzzy")
class FuzzySearchNode(SuperNode):
    """
    Performs fuzzy string matching and automated spell correction.
    
    This node compares 'Raw Text' against 'Target' (string or list) using fuzzy 
    logic. If the initial match is below 'Threshold', it attempts spell 
    correction and re-scores. It routes the flow to 'Ambiguous' if no 
    satisfactory match is found.
    
    Inputs:
    - Flow: Trigger the search.
    - Raw Text: The string to be analyzed.
    - Target: The reference string or list of candidates to match against.
    - Threshold: Minimum score (0-100) to consider a match successful.
    
    Outputs:
    - Flow: Triggered if a match exceeds the threshold.
    - Ambiguous: Triggered if match score is below the threshold.
    - Best Text: The result (either original or spell-corrected).
    - Confidence: Per-word match scores.
    - Score: Overall fuzzy similarity score.
    - Corrected: Boolean indicating if spell correction was applied and improved the score.
    """
    version = "2.1.0"

    def __init__(self, node_id, name, bridge):
        super().__init__(node_id, name, bridge)
        self.is_native = True
        self.properties["Threshold"] = 80
        self.properties["Raw Text"] = ""
        self.properties["Target"] = ""
        self.define_schema()
        self.register_handlers()

    def register_handlers(self):
        self.register_handler("Flow", self.perform_search)

    def define_schema(self):
        self.input_schema = {
            "Flow": DataType.FLOW,
            "Raw Text": DataType.STRING,
            "Target": DataType.ANY, # String or List
            "Threshold": DataType.NUMBER
        }
        self.output_schema = {
            "Flow": DataType.FLOW,
            "Ambiguous": DataType.FLOW,
            "Best Text": DataType.STRING,
            "Confidence": DataType.LIST,
            "Score": DataType.NUMBER,
            "Corrected": DataType.BOOLEAN
        }

    def perform_search(self, Raw_Text=None, Target=None, Threshold=None, **kwargs):
        # BaseNode handles falling back to properties if inputs are None
        raw_text = Raw_Text or kwargs.get("Raw Text") or self.properties.get("Raw Text", self.properties.get("RawText"))
        target = Target or kwargs.get("Target") or self.properties.get("Target")
        threshold = float(Threshold) if Threshold is not None else float(kwargs.get("Threshold", self.properties.get("Threshold", 80)))

        if not raw_text:
            self.logger.warning("Empty Raw Text input.")
            self._set_outputs("", [], 0.0, False, threshold)
            self.bridge.set(f"{self.node_id}_ActivePorts", ["Ambiguous"], self.name)
            return True

        ensure_rapidfuzz()
        ensure_spellchecker()

        # Handle list of targets: find best match
        if isinstance(target, (list, tuple)):
            best_target = ""
            best_score = 0
            for t in target:
                s = _fuzzy_score(raw_text, str(t))
                if s > best_score:
                    best_score = s
                    best_target = str(t)
            target = best_target
            initial_score = best_score
        else:
            target = str(target)
            initial_score = _fuzzy_score(raw_text, target)

        self.logger.info(f"Initial score: {initial_score:.1f}%")

        if initial_score >= threshold:
            confidences = _word_confidences(raw_text, target)
            self._set_outputs(raw_text, confidences, initial_score, False, threshold)
            return True

        if not PySpellChecker:
            self.logger.warning("pyspellchecker not installed — skipping correction.")
            confidences = _word_confidences(raw_text, target)
            self._set_outputs(raw_text, confidences, initial_score, False, threshold)
            return True

        corrected_text = _spell_correct(raw_text)
        corrected_score = _fuzzy_score(corrected_text, target)
        self.logger.info(f"Corrected: '{corrected_text}' → Score: {corrected_score:.1f}%")

        if corrected_score > initial_score:
            best_text = corrected_text
            best_score = corrected_score
            was_corrected = True
        else:
            best_text = raw_text
            best_score = initial_score
            was_corrected = False

        confidences = _word_confidences(best_text, target)
        self._set_outputs(best_text, confidences, best_score, was_corrected, threshold)
        return True

    def _set_outputs(self, best_text, confidences, score, corrected, threshold):
        """Sets all output ports and determines active flow."""
        self.bridge.set(f"{self.node_id}_Best Text", best_text, self.name)
        self.bridge.set(f"{self.node_id}_Confidence", confidences, self.name)
        self.bridge.set(f"{self.node_id}_Score", round(score, 1), self.name)
        self.bridge.set(f"{self.node_id}_Corrected", corrected, self.name)

        if score >= threshold:
            self.bridge.set(f"{self.node_id}_ActivePorts", ["Flow"], self.name)
            self.logger.info(f"✓ Match ({score:.1f}% >= {threshold}%)")
        else:
            self.bridge.set(f"{self.node_id}_ActivePorts", ["Ambiguous"], self.name)
            self.logger.info(f"⚠ Ambiguous ({score:.1f}% < {threshold}%)")
