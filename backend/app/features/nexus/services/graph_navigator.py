"""
Stage 2a: Graph Navigator (STANDARD mode)

Single LLM call to select relevant communities/tags/keywords,
then deterministic execution to find graph-connected results.

Flow:
1. Load navigation cache (community map + tag overview)
2. Build compact prompt (~500 tokens)
3. Single LLM call (3B model) -> JSON navigation plan
4. Deterministic execution: load community notes, filter tags, score keywords
5. Follow wikilinks from top scored notes
6. Return scored candidates
"""

import json
import logging
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional

from core import config
from core.llm import get_default_provider, LLMMessage
from features.rag_chat.services.retrieval import RetrievalResult
from .prompts import NAVIGATION_PROMPT_TEMPLATE
from .graph_nav_helpers import (
    load_community_notes,
    load_tag_notes,
    follow_wikilinks,
    candidates_to_results,
)

logger = logging.getLogger(__name__)


@dataclass
class NavigationPlan:
    """Parsed output from navigation LLM call."""
    communities: List[int] = field(default_factory=list)
    tags: List[str] = field(default_factory=list)
    keywords: List[str] = field(default_factory=list)


@dataclass
class GraphNavigationResult:
    """Results from graph navigation."""
    results: List[RetrievalResult]
    plan: NavigationPlan
    cache_hit: bool = False


def navigate_graph(
    db, query: str, owner_id: int,
    community_map: str, tag_overview: str,
    max_results: int = 10,
) -> GraphNavigationResult:
    """
    Execute graph navigation: LLM planning + deterministic retrieval.

    Args:
        db: Database session
        query: User query
        owner_id: User ID
        community_map: Cached community descriptions
        tag_overview: Cached tag listing
        max_results: Max results to return

    Returns:
        GraphNavigationResult with scored candidates
    """
    prompt = NAVIGATION_PROMPT_TEMPLATE.format(
        community_map=community_map[:1500],
        tag_overview=tag_overview[:500],
        query=query,
    )

    plan = _call_navigation_llm(prompt)
    if not plan:
        logger.warning("Navigation LLM failed, returning empty results")
        return GraphNavigationResult(results=[], plan=NavigationPlan())

    results = _execute_plan(db, owner_id, plan, query, max_results)

    logger.info(
        f"Graph nav: {len(results)} results from "
        f"communities={plan.communities}, tags={plan.tags}, "
        f"keywords={plan.keywords}"
    )

    return GraphNavigationResult(results=results, plan=plan)


def _call_navigation_llm(prompt: str) -> Optional[NavigationPlan]:
    """Call the 3B navigation model for a JSON plan."""
    messages = [
        LLMMessage(role="system", content="You are a JSON-only response bot. Output valid JSON only."),
        LLMMessage(role="user", content=prompt),
    ]

    try:
        provider = get_default_provider()
        response = provider.generate(
            messages=messages,
            model=config.NEXUS_NAVIGATION_MODEL,
            temperature=0.1,
            max_tokens=200,
            timeout=config.NEXUS_NAVIGATION_TIMEOUT,
        )
        raw = response.content.strip()

        if raw.startswith("```"):
            raw = raw.split("\n", 1)[-1].rsplit("```", 1)[0]

        data = json.loads(raw)
        return NavigationPlan(
            communities=[int(c) for c in data.get("communities", [])[:3]],
            tags=[str(t).lower() for t in data.get("tags", [])[:5]],
            keywords=[str(k).lower() for k in data.get("keywords", [])[:5]],
        )

    except (json.JSONDecodeError, Exception) as e:
        logger.error(f"Navigation LLM failed: {e}")
        return None


def _execute_plan(db, owner_id, plan, query, max_results):
    """Execute navigation plan with database queries."""
    candidates: Dict[int, Dict[str, Any]] = {}

    if plan.communities:
        load_community_notes(db, owner_id, plan.communities, candidates)

    if plan.tags:
        load_tag_notes(db, owner_id, plan.tags, candidates)

    # Score by keyword match
    query_lower = query.lower()
    keywords = plan.keywords + query_lower.split()[:3]
    for note_id, info in candidates.items():
        score = info.get("score", 0.0)
        title_lower = info.get("title", "").lower()
        content_lower = info.get("content", "")[:500].lower()
        for kw in keywords:
            if kw in title_lower:
                score += 0.3
            elif kw in content_lower:
                score += 0.1
        candidates[note_id]["score"] = score

    # Follow wikilinks from top 5
    sorted_top = sorted(
        candidates.items(), key=lambda x: x[1].get("score", 0), reverse=True
    )[:5]

    wikilink_additions = follow_wikilinks(db, owner_id, sorted_top, candidates)
    candidates.update(wikilink_additions)

    return candidates_to_results(candidates, max_results)
