"""
Intent detection for RAG chat queries.

Detects whether a query is:
- FOLLOW_UP: About previous context (skip RAG search)
- REFINED: New topic but related (do RAG with conversation context)
- FRESH: Completely new query (full RAG search)
"""

import re
import logging
from enum import Enum
from typing import List, Dict, Optional, Set
from dataclasses import dataclass

logger = logging.getLogger(__name__)


class QueryIntent(Enum):
    """Types of query intent."""
    FOLLOW_UP = "follow_up"  # About previous context, skip RAG
    REFINED = "refined"      # New topic, do RAG but keep context
    FRESH = "fresh"          # Completely new, full RAG


@dataclass
class IntentResult:
    """Result of intent detection."""
    intent: QueryIntent
    confidence: float  # 0.0 to 1.0
    reason: str
    referenced_citations: List[int] = None  # Citation indices if follow-up


# Patterns for follow-up detection
CITATION_PATTERNS = [
    r'\bsource\s*(\d+)\b',           # "source 1", "Source 2"
    r'\[\s*(\d+)\s*\]',              # "[1]", "[ 2 ]"
    r'\bcitation\s*(\d+)\b',         # "citation 1"
    r'\b(first|second|third|fourth|fifth)\s+(one|source|citation)\b',
    r'\b(the\s+)?(first|second|third|fourth|fifth)\s+result\b',
]

# Pronouns that suggest follow-up (when at start of query)
FOLLOW_UP_STARTERS = {
    'it', 'this', 'that', 'they', 'them', 'these', 'those',
    'he', 'she', 'his', 'her', 'their', 'its',
}

# Continuation words
CONTINUATION_WORDS = {
    'more', 'also', 'additionally', 'furthermore', 'moreover',
    'elaborate', 'explain', 'expand', 'clarify', 'detail',
    'continue', 'and', 'but', 'however',
}

# Very short queries that are likely follow-ups
SHORT_FOLLOW_UP_PATTERNS = [
    r'^why\??$',
    r'^how\??$',
    r'^what\??$',
    r'^when\??$',
    r'^where\??$',
    r'^who\??$',
    r'^yes\??$',
    r'^no\??$',
    r'^really\??$',
    r'^go\s+on\??$',
]

# Topic shift indicators (suggest REFINED search)
TOPIC_SHIFT_PHRASES = [
    r'\bwhat\s+about\b',
    r'\bhow\s+about\b',
    r'\bnow\s+(tell|show|explain)\b',
    r'\bdifferent\s+(question|topic)\b',
    r'\banother\s+(question|topic|thing)\b',
    r'\bchanging\s+(topic|subject)\b',
    r'\bswitching\s+to\b',
    r'\bmoving\s+on\b',
]


def extract_citation_references(query: str) -> List[int]:
    """Extract citation numbers referenced in query."""
    citations = []

    for pattern in CITATION_PATTERNS[:3]:  # Only numeric patterns
        matches = re.findall(pattern, query, re.IGNORECASE)
        for match in matches:
            if isinstance(match, str) and match.isdigit():
                citations.append(int(match))

    # Handle ordinal words
    ordinal_map = {'first': 1, 'second': 2, 'third': 3, 'fourth': 4, 'fifth': 5}
    for ordinal, num in ordinal_map.items():
        if re.search(rf'\b{ordinal}\s+(one|source|citation|result)\b', query, re.I):
            citations.append(num)

    return sorted(set(citations))


def detect_intent(
    query: str,
    previous_messages: List[Dict] = None,
    previous_citations: List[Dict] = None,
) -> IntentResult:
    """
    Detect the intent of a user query.

    Args:
        query: The user's query
        previous_messages: List of previous messages in conversation
                          [{"role": "user"|"assistant", "content": "..."}]
        previous_citations: Citations from the last assistant message

    Returns:
        IntentResult with intent type, confidence, and reason
    """
    previous_messages = previous_messages or []
    previous_citations = previous_citations or []
    query_lower = query.lower().strip()
    words = query_lower.split()

    # No previous context = always FRESH
    if not previous_messages:
        return IntentResult(
            intent=QueryIntent.FRESH,
            confidence=1.0,
            reason="No conversation history"
        )

    # Check for explicit citation references
    cited_indices = extract_citation_references(query)
    if cited_indices and previous_citations:
        return IntentResult(
            intent=QueryIntent.FOLLOW_UP,
            confidence=0.95,
            reason=f"References citation(s): {cited_indices}",
            referenced_citations=cited_indices
        )

    # Check for very short follow-up patterns
    for pattern in SHORT_FOLLOW_UP_PATTERNS:
        if re.match(pattern, query_lower):
            return IntentResult(
                intent=QueryIntent.FOLLOW_UP,
                confidence=0.85,
                reason=f"Short follow-up query: '{query}'"
            )

    # Check if starts with follow-up pronoun
    if words and words[0] in FOLLOW_UP_STARTERS:
        # Check if it's a meaningful question, not just starting with pronoun
        if len(words) <= 10:  # Short query starting with pronoun
            return IntentResult(
                intent=QueryIntent.FOLLOW_UP,
                confidence=0.80,
                reason=f"Starts with pronoun: '{words[0]}'"
            )

    # Check for continuation words
    continuation_in_query = set(words) & CONTINUATION_WORDS
    if continuation_in_query and len(words) <= 15:
        return IntentResult(
            intent=QueryIntent.FOLLOW_UP,
            confidence=0.70,
            reason=f"Contains continuation word(s): {continuation_in_query}"
        )

    # Check for topic shift phrases (REFINED search)
    for pattern in TOPIC_SHIFT_PHRASES:
        if re.search(pattern, query_lower):
            return IntentResult(
                intent=QueryIntent.REFINED,
                confidence=0.85,
                reason=f"Topic shift detected: '{pattern}'"
            )

    # Check query length - very long queries are usually fresh
    if len(query) > 100:
        return IntentResult(
            intent=QueryIntent.FRESH,
            confidence=0.75,
            reason="Long, self-contained query"
        )

    # Check for new keywords not in recent context
    if previous_messages:
        recent_context = " ".join(
            m.get("content", "")[:500]
            for m in previous_messages[-4:]
        ).lower()

        # Extract potential topic words (nouns, longer words)
        query_topics = {w for w in words if len(w) > 4 and w.isalpha()}
        context_words = set(recent_context.split())

        new_topics = query_topics - context_words
        if new_topics and len(new_topics) >= 2:
            return IntentResult(
                intent=QueryIntent.REFINED,
                confidence=0.65,
                reason=f"New topic keywords: {new_topics}"
            )

    # Default: if we have context but no clear signals, do refined search
    # This preserves conversation context while still fetching relevant data
    return IntentResult(
        intent=QueryIntent.REFINED,
        confidence=0.50,
        reason="Default: maintain context with fresh retrieval"
    )


def should_skip_rag_search(intent_result: IntentResult) -> bool:
    """Check if RAG search should be skipped based on intent."""
    return (
        intent_result.intent == QueryIntent.FOLLOW_UP
        and intent_result.confidence >= 0.70
    )


def should_include_conversation_context(intent_result: IntentResult) -> bool:
    """Check if conversation context should be included in prompt."""
    return intent_result.intent in (QueryIntent.FOLLOW_UP, QueryIntent.REFINED)
