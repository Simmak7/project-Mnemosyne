"""
Context Builder Helpers

Connection detection, origin tracing, and exploration suggestion generation
for the NEXUS context builder.
"""

import logging
from typing import List, Dict, Any, Optional, Set

from features.nexus.schemas import (
    NexusRichCitation,
    ConnectionInsight,
    ExplorationSuggestion,
)

logger = logging.getLogger(__name__)


def build_connections(
    citations: List[NexusRichCitation],
    max_connection_chars: int,
) -> tuple:
    """Build the CONNECTIONS section and ConnectionInsight objects."""
    insights: List[ConnectionInsight] = []
    lines: List[str] = []
    current_chars = 0

    # Detect shared communities (one insight per group, not pairwise)
    community_groups: Dict[int, List[int]] = {}
    for c in citations:
        if c.community_id is not None:
            community_groups.setdefault(c.community_id, []).append(c.index)

    for cid, indices in community_groups.items():
        if len(indices) > 1:
            name = next((c.community_name for c in citations
                        if c.community_id == cid and c.community_name), None)
            top_terms = next((c.community_top_terms for c in citations
                             if c.community_id == cid and c.community_top_terms), None)
            # Build a descriptive label
            if name and top_terms:
                desc = f"Sources [{']['.join(map(str, indices))}] share '{name}' community — {top_terms}"
            elif name:
                desc = f"Sources [{']['.join(map(str, indices))}] share '{name}' community"
            elif top_terms:
                desc = f"Sources [{']['.join(map(str, indices))}] share a topic cluster — {top_terms}"
            else:
                desc = f"Sources [{']['.join(map(str, indices))}] are in the same topic cluster"

            line = f"Sources [{']['.join(map(str, indices))}] share community: {name or top_terms or f'cluster {cid}'}"
            if current_chars + len(line) < max_connection_chars:
                lines.append(line)
                current_chars += len(line)
                insights.append(ConnectionInsight(
                    source_index=indices[0],
                    target_index=indices[1],
                    connection_type="shared_community",
                    description=desc,
                ))

    # Detect wikilink connections between results
    for c in citations:
        for path in c.path_to_other_results:
            target_idx = next(
                (tc.index for tc in citations if tc.source_id == path["target_note_id"]),
                None
            )
            if target_idx:
                line = f"[{c.index}] links to [{target_idx}] via wikilink"
                if current_chars + len(line) < max_connection_chars:
                    lines.append(line)
                    current_chars += len(line)
                    insights.append(ConnectionInsight(
                        source_index=c.index,
                        target_index=target_idx,
                        connection_type="wikilink",
                        description=f"'{c.title}' links to '{path['target_title']}'",
                    ))

    # Detect shared tags
    tag_groups: Dict[str, List[int]] = {}
    for c in citations:
        for tag in c.tags:
            tag_groups.setdefault(tag, []).append(c.index)

    for tag, indices in tag_groups.items():
        if len(indices) > 1:
            line = f"Sources [{']['.join(map(str, indices))}] share tag: #{tag}"
            if current_chars + len(line) < max_connection_chars:
                lines.append(line)
                current_chars += len(line)
                insights.append(ConnectionInsight(
                    source_index=indices[0],
                    target_index=indices[1],
                    connection_type="shared_tag",
                    description=f"Sources [{']['.join(map(str, indices))}] share tag #{tag}",
                ))

    return "\n".join(lines), insights


def build_origins(
    citations: List[NexusRichCitation],
    max_origin_chars: int,
) -> str:
    """Build the ORIGINS section showing where each source came from."""
    lines: List[str] = []

    origin_labels = {
        "manual": "Manually created note",
        "image_analysis": "Generated from image analysis",
        "document_analysis": "Extracted from PDF document",
        "journal": "Journal entry",
    }

    current_chars = 0
    for c in citations:
        if c.origin_type and c.origin_type != "manual":
            label = origin_labels.get(c.origin_type, c.origin_type)
            line = f"[{c.index}] {label}"
            if c.artifact_id:
                fname = f" '{c.artifact_filename}'" if c.artifact_filename else ""
                if c.origin_type == "image_analysis":
                    line += f" (image #{c.artifact_id}{fname})"
                elif c.origin_type == "document_analysis":
                    line += f" (document #{c.artifact_id}{fname})"
            if current_chars + len(line) < max_origin_chars:
                lines.append(line)
                current_chars += len(line)

    return "\n".join(lines)


def build_exploration_suggestions(
    citations: List[NexusRichCitation],
) -> List[ExplorationSuggestion]:
    """Generate exploration suggestions from unconnected topics."""
    suggestions: List[ExplorationSuggestion] = []

    result_ids = {c.source_id for c in citations}
    seen_suggestions: Set[int] = set()

    for c in citations:
        for wl in c.direct_wikilinks:
            target_id = wl["note_id"]
            if target_id not in result_ids and target_id not in seen_suggestions:
                suggestions.append(ExplorationSuggestion(
                    query=f"Tell me about {wl['title']}",
                    reason=f"Linked from [{c.index}] '{c.title}'",
                    related_citation_indices=[c.index],
                ))
                seen_suggestions.add(target_id)
                if len(suggestions) >= 3:
                    return suggestions

    return suggestions


def artifact_url(chain: Dict[str, Any]) -> Optional[str]:
    """Generate artifact URL from source chain info."""
    origin = chain.get("origin_type")
    artifact_id = chain.get("artifact_id")
    if not artifact_id:
        return None
    if origin == "image_analysis":
        return f"/images/{artifact_id}"
    if origin == "document_analysis":
        return f"/documents/{artifact_id}"
    return None
