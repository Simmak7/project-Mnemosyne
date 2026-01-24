"""Memory Classifier - Classify facts by memory type.

Memory Types:
- EPISODIC: Time-bound, specific events - kept in RAG only (not trained into LoRA)
  Examples: "Meeting scheduled for Dec 25", "Bought groceries yesterday"

- SEMANTIC: Stable concepts and facts - candidates for training
  Examples: "Python is my primary language", "Sarah works at Acme Corp"

- PREFERENCE: High recurrence patterns - priority for LoRA training
  Examples: "I prefer bullet points", "Always use dark mode"

Classification Factors:
1. Temporal reference: Events with specific dates → EPISODIC
2. Recurrence: Facts appearing multiple times → higher priority
3. Stability: Facts that don't change → SEMANTIC or PREFERENCE
4. Graph centrality: Well-connected concepts → PREFERENCE
"""

import logging
from typing import List, Dict, Optional, Set
from dataclasses import dataclass, field
from datetime import datetime
import re

from .condenser import ExtractedFact

logger = logging.getLogger(__name__)


@dataclass
class GraphSignals:
    """Graph analysis signals for classification."""
    centrality: Dict[str, float] = field(default_factory=dict)  # concept -> centrality
    recurrence: Dict[str, int] = field(default_factory=dict)    # concept -> count
    connections: Dict[str, Set[str]] = field(default_factory=dict)  # concept -> related


@dataclass
class ClassifiedFact:
    """A fact with memory type classification."""
    fact: ExtractedFact
    memory_type: str  # episodic, semantic, preference
    priority_score: float  # 0.0-1.0, higher = train sooner
    classification_reason: str


@dataclass
class ClassifiedMemory:
    """Result of memory classification."""
    episodic: List[ClassifiedFact] = field(default_factory=list)
    semantic: List[ClassifiedFact] = field(default_factory=list)
    preferences: List[ClassifiedFact] = field(default_factory=list)

    @property
    def total_count(self) -> int:
        return len(self.episodic) + len(self.semantic) + len(self.preferences)

    @property
    def trainable_count(self) -> int:
        """Count of facts suitable for training (semantic + preferences)."""
        return len(self.semantic) + len(self.preferences)


# Patterns that indicate temporal/episodic content
TEMPORAL_PATTERNS = [
    r'\b(today|yesterday|tomorrow)\b',
    r'\b(this|next|last)\s+(week|month|year)\b',
    r'\b(jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)\w*\s+\d{1,2}',
    r'\b\d{1,2}[/\-]\d{1,2}[/\-]\d{2,4}\b',
    r'\b\d{4}[/\-]\d{1,2}[/\-]\d{1,2}\b',
    r'\b(meeting|appointment|deadline|due|scheduled)\b',
    r'\b(ago|from now)\b',
]

# Patterns that indicate preferences
PREFERENCE_PATTERNS = [
    r'\b(prefer|always|never|like|dislike|favorite)\b',
    r'\b(usually|typically|normally|often)\b',
    r'\b(best|worst|ideal|default)\b',
    r'\b(style|format|approach|method)\b',
]

# Patterns that indicate stable identity/facts
IDENTITY_PATTERNS = [
    r'\b(i am|i\'m|my name|i work)\b',
    r'\b(my\s+\w+\s+is)\b',
    r'\b(lives in|works at|born in)\b',
]


class MemoryClassifier:
    """Classify facts by memory type for training decisions."""

    def __init__(
        self,
        recurrence_threshold: int = 3,
        centrality_threshold: float = 0.5,
        stability_threshold: float = 0.7
    ):
        """Initialize classifier.

        Args:
            recurrence_threshold: Min occurrences for preference
            centrality_threshold: Min centrality for preference
            stability_threshold: Min stability for semantic
        """
        self.recurrence_threshold = recurrence_threshold
        self.centrality_threshold = centrality_threshold
        self.stability_threshold = stability_threshold

        # Compile regex patterns
        self._temporal_re = [re.compile(p, re.IGNORECASE) for p in TEMPORAL_PATTERNS]
        self._preference_re = [re.compile(p, re.IGNORECASE) for p in PREFERENCE_PATTERNS]
        self._identity_re = [re.compile(p, re.IGNORECASE) for p in IDENTITY_PATTERNS]

    def classify(
        self,
        facts: List[ExtractedFact],
        graph_signals: Optional[GraphSignals] = None
    ) -> ClassifiedMemory:
        """Classify facts by memory type.

        Args:
            facts: List of extracted facts
            graph_signals: Optional graph analysis data

        Returns:
            ClassifiedMemory with facts sorted by type
        """
        if graph_signals is None:
            graph_signals = GraphSignals()

        result = ClassifiedMemory()

        for fact in facts:
            classified = self._classify_single(fact, graph_signals)

            if classified.memory_type == "episodic":
                result.episodic.append(classified)
            elif classified.memory_type == "preference":
                result.preferences.append(classified)
            else:
                result.semantic.append(classified)

        # Sort by priority within each category
        result.preferences.sort(key=lambda x: x.priority_score, reverse=True)
        result.semantic.sort(key=lambda x: x.priority_score, reverse=True)
        result.episodic.sort(key=lambda x: x.priority_score, reverse=True)

        logger.info(
            f"Classified {result.total_count} facts: "
            f"{len(result.preferences)} preferences, "
            f"{len(result.semantic)} semantic, "
            f"{len(result.episodic)} episodic"
        )

        return result

    def _classify_single(
        self,
        fact: ExtractedFact,
        graph_signals: GraphSignals
    ) -> ClassifiedFact:
        """Classify a single fact.

        Classification priority:
        1. Check for temporal markers → EPISODIC
        2. Check recurrence + centrality → PREFERENCE
        3. Check stability → SEMANTIC
        4. Default → SEMANTIC with lower priority
        """
        # Handle None values safely
        text = (fact.fact_text or "").lower()
        concept = (fact.concept or "unknown").lower()

        # Get graph signals for this concept
        centrality = graph_signals.centrality.get(concept, 0.0)
        recurrence = graph_signals.recurrence.get(concept, 1)

        # 1. Check for temporal/episodic markers
        if self._is_temporal(fact):
            return ClassifiedFact(
                fact=fact,
                memory_type="episodic",
                priority_score=0.3,  # Lower priority for RAG-only
                classification_reason="temporal_reference"
            )

        # 2. Check for high recurrence + centrality → PREFERENCE
        if (recurrence >= self.recurrence_threshold and
                centrality >= self.centrality_threshold):
            priority = min(1.0, (recurrence / 10) * 0.5 + centrality * 0.5)
            return ClassifiedFact(
                fact=fact,
                memory_type="preference",
                priority_score=priority,
                classification_reason=f"high_recurrence({recurrence})+centrality({centrality:.2f})"
            )

        # 3. Check for preference language patterns
        if self._has_preference_patterns(text):
            return ClassifiedFact(
                fact=fact,
                memory_type="preference",
                priority_score=0.7,
                classification_reason="preference_language"
            )

        # 4. Check for identity patterns (high priority semantic)
        if self._has_identity_patterns(text):
            return ClassifiedFact(
                fact=fact,
                memory_type="semantic",
                priority_score=0.8,
                classification_reason="identity_fact"
            )

        # 5. Default to semantic with confidence-based priority
        stability = self._estimate_stability(fact)
        priority = fact.confidence * 0.5 + stability * 0.5

        return ClassifiedFact(
            fact=fact,
            memory_type="semantic",
            priority_score=priority,
            classification_reason=f"default_semantic(stability={stability:.2f})"
        )

    def _is_temporal(self, fact: ExtractedFact) -> bool:
        """Check if fact has temporal references."""
        if fact.has_temporal_reference:
            return True

        if fact.fact_type == "event":
            return True

        text = fact.fact_text
        for pattern in self._temporal_re:
            if pattern.search(text):
                return True

        return False

    def _has_preference_patterns(self, text: str) -> bool:
        """Check if text contains preference language."""
        for pattern in self._preference_re:
            if pattern.search(text):
                return True
        return False

    def _has_identity_patterns(self, text: str) -> bool:
        """Check if text contains identity/self-reference patterns."""
        for pattern in self._identity_re:
            if pattern.search(text):
                return True
        return False

    def _estimate_stability(self, fact: ExtractedFact) -> float:
        """Estimate how stable/unchanging a fact is.

        Stable facts are good training candidates.
        """
        # Entity facts tend to be stable
        if fact.fact_type == "entity":
            return 0.8

        # Relations are moderately stable
        if fact.fact_type == "relation":
            return 0.7

        # Attributes vary
        if fact.fact_type == "attribute":
            return 0.6

        # Events are least stable
        if fact.fact_type == "event":
            return 0.3

        return 0.5

    def update_with_recurrence(
        self,
        classified: ClassifiedMemory,
        fact_history: Dict[str, int]
    ) -> ClassifiedMemory:
        """Re-classify based on updated recurrence data.

        Call this after storing facts to database to incorporate
        historical recurrence counts.
        """
        # Move high-recurrence semantic facts to preferences
        promoted = []
        remaining_semantic = []

        for cf in classified.semantic:
            concept = (cf.fact.concept or "unknown").lower()
            historical_count = fact_history.get(concept, 0)
            total_recurrence = historical_count + 1

            if total_recurrence >= self.recurrence_threshold:
                cf.memory_type = "preference"
                cf.priority_score = min(1.0, total_recurrence / 10)
                cf.classification_reason = f"promoted_by_recurrence({total_recurrence})"
                promoted.append(cf)
            else:
                remaining_semantic.append(cf)

        classified.semantic = remaining_semantic
        classified.preferences.extend(promoted)
        classified.preferences.sort(key=lambda x: x.priority_score, reverse=True)

        if promoted:
            logger.info(f"Promoted {len(promoted)} facts to preferences based on recurrence")

        return classified
