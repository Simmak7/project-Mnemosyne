"""
Stage 1: Heuristic Query Router (< 50ms, no LLM)

Classifies queries into FAST | STANDARD | DEEP modes and
detects intent (factual, synthesis, exploration, temporal, creative).

Rules:
- Short factual queries -> FAST
- Queries with relationship/connection words -> STANDARD
- Queries asking for analysis/patterns across notes -> DEEP
- Auto mode picks based on heuristics
"""

import re
import logging
from dataclasses import dataclass
from typing import Optional

logger = logging.getLogger(__name__)

# Pattern sets for classification
DEEP_PATTERNS = [
    r'\b(analyz|analysis|pattern|relationship|across|all my|every|comprehensive)\b',
    r'\b(connect|connection|relate|between|compare|contrast|overview)\b',
    r'\b(trend|evolut|chang|over time|history of my)\b',
    r'\b(missing|gap|blind spot|unexplored)\b',
]

STANDARD_PATTERNS = [
    r'\b(how does|how do|why|explain|what links|connected to)\b',
    r'\b(similar to|related to|link between|associated with)\b',
    r'\b(community|cluster|group|topic)\b',
    r'\bhow .+ relate\b',
]

TEMPORAL_PATTERNS = [
    r'\b(recent|latest|last week|yesterday|today|this month)\b',
    r'\b(when did|since|before|after|timeline|chronolog)\b',
    r'\b(new|newest|updated|changed)\b',
]

CREATIVE_PATTERNS = [
    r'\b(brainstorm|idea|suggest|inspir|creative|novel)\b',
    r'\b(what if|imagine|could|might|hypothetic)\b',
]

SYNTHESIS_PATTERNS = [
    r'\b(summarize|summary|synthesize|combine|bring together)\b',
    r'\b(overall|big picture|holistic|key takeaway)\b',
]


@dataclass
class QueryRoute:
    """Result of query routing."""
    mode: str  # FAST | STANDARD | DEEP
    intent: str  # factual | synthesis | exploration | temporal | creative
    auto_detected: bool  # True if mode was auto-detected
    has_temporal_signal: bool = False
    estimated_complexity: float = 0.0  # 0.0 to 1.0


def _count_matches(text: str, patterns: list) -> int:
    """Count how many pattern groups match the text."""
    count = 0
    for pattern in patterns:
        if re.search(pattern, text, re.IGNORECASE):
            count += 1
    return count


def _detect_intent(query: str) -> str:
    """Detect the primary intent of the query."""
    query_lower = query.lower()

    scores = {
        "temporal": _count_matches(query_lower, TEMPORAL_PATTERNS),
        "creative": _count_matches(query_lower, CREATIVE_PATTERNS),
        "synthesis": _count_matches(query_lower, SYNTHESIS_PATTERNS),
        "exploration": _count_matches(query_lower, DEEP_PATTERNS),
        "factual": 1,  # baseline
    }

    # Boost factual for short queries or questions starting with "what is"
    if len(query.split()) <= 6:
        scores["factual"] += 2
    if re.match(r'^(what is|who is|where is|define|what does)', query_lower):
        scores["factual"] += 3

    return max(scores, key=scores.get)


def route_query(query: str, requested_mode: Optional[str] = None) -> QueryRoute:
    """
    Route a query to the appropriate NEXUS mode.

    Args:
        query: User's query text
        requested_mode: Explicit mode override (fast/standard/deep/auto/None)

    Returns:
        QueryRoute with mode, intent, and metadata
    """
    intent = _detect_intent(query)
    has_temporal = _count_matches(query.lower(), TEMPORAL_PATTERNS) > 0

    # Explicit mode requested
    if requested_mode and requested_mode.lower() in ("fast", "standard", "deep"):
        return QueryRoute(
            mode=requested_mode.upper(),
            intent=intent,
            auto_detected=False,
            has_temporal_signal=has_temporal,
        )

    # Auto-detect mode
    query_lower = query.lower()
    word_count = len(query.split())
    deep_score = _count_matches(query_lower, DEEP_PATTERNS)
    standard_score = _count_matches(query_lower, STANDARD_PATTERNS)

    # Short simple queries -> FAST
    if word_count <= 5 and deep_score == 0 and standard_score == 0:
        mode = "FAST"
        complexity = 0.1
    # Deep analysis signals
    elif deep_score >= 2 or (deep_score >= 1 and word_count > 12):
        mode = "DEEP"
        complexity = 0.8 + (0.1 * min(deep_score, 2))
    # Standard navigation signals
    elif standard_score >= 1 or (word_count > 8 and intent != "factual"):
        mode = "STANDARD"
        complexity = 0.4 + (0.1 * min(standard_score, 3))
    else:
        mode = "FAST"
        complexity = 0.2

    logger.info(
        f"NEXUS route: mode={mode}, intent={intent}, "
        f"words={word_count}, deep={deep_score}, std={standard_score}"
    )

    return QueryRoute(
        mode=mode,
        intent=intent,
        auto_detected=True,
        has_temporal_signal=has_temporal,
        estimated_complexity=min(complexity, 1.0),
    )
