"""
Stage 3: Graph-Aware Context Builder

Assembles retrieved results into three sections:
- SOURCES: Content with citation markers [1], [2], etc.
- CONNECTIONS: How sources relate via wikilinks/communities
- ORIGINS: Where each source came from (manual, image, PDF)

Also generates ConnectionInsight and ExplorationSuggestion objects.
"""

import logging
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional

from features.rag_chat.services.context_builder import (
    estimate_tokens,
    truncate_content,
)
from features.rag_chat.services.ranking import RankedResult
from features.nexus.schemas import (
    NexusRichCitation,
    ConnectionInsight,
    ExplorationSuggestion,
)
from .prompts import format_nexus_context
from .context_helpers import (
    build_connections,
    build_origins,
    build_exploration_suggestions,
    artifact_url,
)

logger = logging.getLogger(__name__)


@dataclass
class NexusContextConfig:
    """Token budgets for NEXUS context assembly."""
    source_token_budget: int = 6000
    connection_token_budget: int = 800
    origin_token_budget: int = 400
    max_content_per_source: int = 600


@dataclass
class NexusAssembledContext:
    """Assembled context ready for NEXUS LLM prompt."""
    formatted_context: str
    rich_citations: List[NexusRichCitation]
    connection_insights: List[ConnectionInsight]
    exploration_suggestions: List[ExplorationSuggestion]
    total_tokens_approx: int
    truncated: bool = False


def build_nexus_context(
    ranked_results: List[RankedResult],
    source_chains: Dict[int, Dict[str, Any]],
    config: NexusContextConfig = None,
) -> NexusAssembledContext:
    """
    Build graph-aware context from ranked results and source chains.

    Args:
        ranked_results: Sorted retrieval results
        source_chains: Origin/tag/community data per note_id
        config: Token budget configuration

    Returns:
        NexusAssembledContext with formatted text and metadata
    """
    if config is None:
        config = NexusContextConfig()

    rich_citations: List[NexusRichCitation] = []
    source_parts: List[str] = []
    total_source_chars = 0
    max_source_chars = config.source_token_budget * 4
    truncated = False

    # Remove note-image duplicates (note generated from image, both in results)
    skip_indices = _find_cross_type_duplicates(ranked_results, source_chains)
    citation_index = 0

    # Build SOURCES section
    for i, rr in enumerate(ranked_results):
        if i in skip_indices:
            continue
        citation_index += 1
        result = rr.result
        chain = source_chains.get(result.source_id, {})

        content = truncate_content(result.content, config.max_content_per_source)
        type_label = _source_type_label(result.source_type)
        source_text = f"[{citation_index}] ({type_label}) {result.title}\n{content}\n"

        if total_source_chars + len(source_text) > max_source_chars:
            if not rich_citations:
                source_text = truncate_content(source_text, max_source_chars)
                truncated = True
            else:
                truncated = True
                break

        source_parts.append(source_text)
        total_source_chars += len(source_text)

        # Build rich citation
        citation = _build_rich_citation(
            citation_index, rr, result, chain, ranked_results
        )
        rich_citations.append(citation)

    sources_section = "\n".join(source_parts)

    # Build other sections using helpers
    connections_section, connection_insights = build_connections(
        rich_citations, config.connection_token_budget * 4
    )
    origins_section = build_origins(rich_citations, config.origin_token_budget * 4)
    exploration_suggestions = build_exploration_suggestions(rich_citations)

    formatted = format_nexus_context(sources_section, connections_section, origins_section)

    return NexusAssembledContext(
        formatted_context=formatted,
        rich_citations=rich_citations,
        connection_insights=connection_insights,
        exploration_suggestions=exploration_suggestions,
        total_tokens_approx=estimate_tokens(formatted),
        truncated=truncated,
    )


def _find_cross_type_duplicates(
    ranked_results: List[RankedResult],
    source_chains: Dict[int, Dict[str, Any]],
) -> set:
    """
    Find note-image pairs where the note was generated from the image.

    When both a note (origin_type=image_analysis) and its source image
    appear in results, skip the lower-ranked duplicate to free source slots.
    """
    skip = set()

    # Map image source_id -> index in ranked_results
    image_idx_map = {}
    for i, rr in enumerate(ranked_results):
        if rr.result.source_type in ("image", "image_chunk"):
            image_idx_map[rr.result.source_id] = i

    if not image_idx_map:
        return skip

    for i, rr in enumerate(ranked_results):
        if rr.result.source_type != "note":
            continue
        chain = source_chains.get(rr.result.source_id, {})
        if chain.get("origin_type") != "image_analysis":
            continue
        artifact_id = chain.get("artifact_id")
        if artifact_id and artifact_id in image_idx_map:
            # Both note and its source image present — skip lower-ranked one
            skip.add(max(i, image_idx_map[artifact_id]))

    if skip:
        logger.info(f"Cross-type dedup: skipping {len(skip)} note-image duplicates")

    return skip


def _source_type_label(source_type: str) -> str:
    """Human-readable label for source types."""
    labels = {
        "note": "Note",
        "chunk": "Note Excerpt",
        "image": "Image",
        "image_chunk": "Image",
        "document_chunk": "PDF Document",
    }
    return labels.get(source_type, "Source")


def _build_rich_citation(citation_index, rr, result, chain, ranked_results):
    """Build a NexusRichCitation from result data and source chain."""
    wikilink_targets = chain.get("wikilink_targets", [])
    tags = chain.get("tags", [])

    other_ids = {r.result.source_id for r in ranked_results}
    paths = [
        {"target_note_id": wl["note_id"], "target_title": wl["title"]}
        for wl in wikilink_targets
        if wl["note_id"] in other_ids
    ]

    return NexusRichCitation(
        index=citation_index,
        source_type=result.source_type,
        source_id=result.source_id,
        title=result.title,
        content_preview=result.content[:200],
        relevance_score=round(rr.final_score, 3),
        retrieval_method=result.retrieval_method,
        hop_count=result.metadata.get("hop_count", 0),
        origin_type=chain.get("origin_type"),
        artifact_id=chain.get("artifact_id"),
        artifact_filename=chain.get("artifact_filename"),
        community_name=chain.get("community_name"),
        community_id=chain.get("community_id"),
        community_top_terms=chain.get("community_top_terms"),
        tags=tags,
        direct_wikilinks=[
            {"note_id": wl["note_id"], "title": wl["title"]}
            for wl in wikilink_targets[:5]
        ],
        path_to_other_results=paths,
        note_url=f"/notes/{result.source_id}" if result.source_type == "note" else None,
        graph_url=f"/graph?focus={result.source_id}" if result.source_type == "note" else None,
        artifact_url=artifact_url(chain),
    )
