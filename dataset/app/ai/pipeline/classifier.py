"""
Lightweight TF-IDF Intent Classification Engine.

Implements a pure-Python Term Frequency-Inverse Document Frequency (TF-IDF) 
algorithm with Cosine Similarity to detect intents without heavy ML dependencies.
"""

from typing import Tuple, Optional, Dict, List
import math
from app.ai.intent_classifier import Intent
from collections import Counter

# ---------------------------------------------------------------------------
# Training Corpus
# ---------------------------------------------------------------------------
# We map intents to arrays of example phrases to allow generalized semantic matching.

INTENT_CORPUS = {
    Intent.SEARCH_CASES: [
        "Show robbery cases",
        "Show theft cases",
        "Show fraud cases",
        "Show kidnapping cases",
        "Pending robbery cases",
        "Latest theft cases",
        "Search cases",
        "Find cases"
    ],
    Intent.PREDICT_CRIME: [
        "Predict robbery next month",
        "Forecast theft",
        "Expected crime rate",
        "Crime prediction",
        "Predict future crime"
    ],
    Intent.AGGREGATE_COUNT: [
        "how many cases in total",
        "total number of theft",
        "count the number of firs",
        "aggregate stats for murder",
        "what is the total count"
    ],
    Intent.CRIME_TREND: [
        "Crime trend in Mysuru",
        "Crime trend in Hassan",
        "Theft trend",
        "Monthly trend",
        "Yearly trend",
        "Crime trend analysis"
    ],
    Intent.HOTSPOT: [
        "Show hotspots",
        "Crime hotspots",
        "High crime areas",
        "Dangerous locations",
        "Where are the heat maps"
    ],
    Intent.SEARCH_ACCUSED: [
        "Find accused Ravi",
        "Show accused Rajesh",
        "Accused named Ravi",
        "Who is accused Ravi",
        "List accused",
        "Search accused",
        "Accused details"
    ],
    Intent.SEARCH_VICTIMS: [
        "Show victim Ravi",
        "Victim named Anjali",
        "Find victims",
        "Victim details",
        "Search for victims"
    ],
    Intent.REPORTS: [
        "generate a report",
        "open the dashboard",
        "show statistics dashboard",
        "export the report"
    ],
    Intent.FIR_LOOKUP: [
        "Open FIR KSP-000347",
        "Show FIR KSP-000347",
        "Find FIR KSP-000347",
        "Case KSP-000347",
        "Crime No KSP-000347",
        "Open Case KSP-000347"
    ],
    Intent.REPEAT_OFFENDERS: [
        "show repeat offenders",
        "who are the habitual offenders",
        "list serial offenders",
        "recidivist tracking"
    ],
    Intent.MOST_WANTED: [
        "show the most wanted",
        "who are the high risk accused",
        "list dangerous criminals",
        "top most wanted list"
    ],
    Intent.GREETING: [
        "Hi",
        "Hello",
        "Hey",
        "Good Morning",
        "Good Evening",
        "Greetings"
    ],
    Intent.GOODBYE: [
        "bye",
        "goodbye",
        "see you later"
    ],
    Intent.THANKS: [
        "thanks",
        "thank you",
        "appreciate it"
    ],
    Intent.HELP: [
        "Help",
        "How can you help",
        "Commands",
        "Capabilities"
    ],
    Intent.BOT_IDENTITY: [
        "who are you",
        "are you a bot"
    ],
    Intent.BOT_CAPABILITIES: [
        "what can you do",
        "how can you help"
    ],
    Intent.SEARCH_LOCATION: [
        "Show crimes in Mysuru",
        "Cases in Mysuru",
        "Cases in Hassan",
        "Robbery in Mandya",
        "FIRs from Udupi",
        "Crime in Bengaluru"
    ],
    Intent.SEARCH_COURT: [
        "Search court",
        "Cases in high court",
        "Supreme court cases"
    ],
    Intent.SEARCH_COMPLAINANT: [
        "Find complainant",
        "Show complainant details",
        "Who complained"
    ],
    Intent.SEARCH_POLICE_STATION: [
        "Search police station",
        "Station cases",
        "Show cases in station"
    ],
    Intent.SEARCH_OFFICER: [
        "Search officer",
        "Investigating officer",
        "Officer details"
    ],
    Intent.SEARCH_CRIME_TYPE: [
        "Search crime type",
        "Crime type details"
    ],
    Intent.SEARCH_ACT_SECTION: [
        "Search section",
        "Act and section"
    ],
    Intent.STATISTICS: [
        "Statistics",
        "Show stats",
        "Overall statistics"
    ],
    Intent.GENERAL_CHAT: [
        "General chat",
        "Let's chat",
        "Talk to me"
    ],
    Intent.UNKNOWN: [
        "dsfjsdfkjsd",
        "blah blah",
        "unknown"
    ]
}

# ---------------------------------------------------------------------------
# TF-IDF Implementation
# ---------------------------------------------------------------------------

def _tokenize(text: str) -> List[str]:
    # Very basic tokenizer assuming text is normalized
    return text.lower().split()

class TFIDFEngine:
    def __init__(self, corpus: Dict[str, List[str]]):
        self.corpus = corpus
        self.documents = []
        self.doc_intents = []
        self.vocab = set()
        
        # Flatten corpus
        for intent, phrases in self.corpus.items():
            for phrase in phrases:
                tokens = _tokenize(phrase)
                self.documents.append(tokens)
                self.doc_intents.append(intent)
                self.vocab.update(tokens)
                
        self.N = len(self.documents)
        self.idf = self._compute_idf()
        
        # Compute TF-IDF vectors for all training documents
        self.doc_vectors = [self._compute_tfidf(doc) for doc in self.documents]
        
    def _compute_idf(self) -> Dict[str, float]:
        idf = {}
        for word in self.vocab:
            # count how many documents contain the word
            doc_count = sum(1 for doc in self.documents if word in doc)
            # Add 1 to avoid division by zero
            idf[word] = math.log((self.N + 1) / (doc_count + 1)) + 1
        return idf
        
    def _compute_tfidf(self, doc_tokens: List[str]) -> Dict[str, float]:
        tf = Counter(doc_tokens)
        doc_len = len(doc_tokens) if doc_tokens else 1
        
        vector = {}
        for word, count in tf.items():
            if word in self.idf:
                vector[word] = (count / doc_len) * self.idf[word]
        return vector
        
    def _cosine_similarity(self, vec1: Dict[str, float], vec2: Dict[str, float]) -> float:
        intersection = set(vec1.keys()) & set(vec2.keys())
        numerator = sum([vec1[x] * vec2[x] for x in intersection])
        
        sum1 = sum([val**2 for val in vec1.values()])
        sum2 = sum([val**2 for val in vec2.values()])
        denominator = math.sqrt(sum1) * math.sqrt(sum2)
        
        if not denominator:
            return 0.0
        return float(numerator) / denominator

    def classify(self, text: str) -> Tuple[Optional[str], float]:
        """
        Returns the top intent and its confidence score based on TF-IDF Cosine Similarity.
        """
        tokens = _tokenize(text)
        if not tokens:
            return None, 0.0
            
        query_vector = self._compute_tfidf(tokens)
        
        # In a real TF-IDF we might just check distance. 
        # But for exact matching out of the box, we check strong words.
        # Let's aggregate scores per intent.
        intent_scores = {intent: 0.0 for intent in self.corpus.keys()}
        
        for i, doc_vector in enumerate(self.doc_vectors):
            sim = self._cosine_similarity(query_vector, doc_vector)
            intent = self.doc_intents[i]
            # Take the max similarity for any phrase in that intent's corpus
            if sim > intent_scores[intent]:
                intent_scores[intent] = sim
                
        best_intent = max(intent_scores, key=intent_scores.get)
        best_score = intent_scores[best_intent]
        
        if best_score == 0.0:
            return Intent.UNKNOWN if hasattr(Intent, "UNKNOWN") else "UNKNOWN", 0.0
        
        # Return Enum if applicable, otherwise string (for CONVERSATION)
        if best_intent in [i.value for i in Intent]:
            return Intent(best_intent), best_score
        return best_intent, best_score

# Singleton instance
_engine = None

def get_classifier_engine() -> TFIDFEngine:
    global _engine
    if not _engine:
        _engine = TFIDFEngine(INTENT_CORPUS)
    return _engine

def classify_pipeline_intent(text: str) -> Tuple[Optional[str], float]:
    """Public wrapper to classify intent."""
    engine = get_classifier_engine()
    return engine.classify(text)
