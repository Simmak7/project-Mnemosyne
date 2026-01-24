"""
Context builder module for RAG system.

Assembles retrieved content into a formatted context for LLM prompts:
- Citation markers ([1], [2], etc.)
- Token budget management
- Source metadata for explainability
"""

import logging
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
import re

from .ranking import RankedResult
from .graph_retrieval import get_relationship_explanation

logger = logging.getLogger(__name__)


@dataclass
class CitationSource:
    """A source that can be cited in the response."""
    index: int  # [1], [2], etc.
    source_type: str  # 'note', 'chunk', 'image'
    source_id: int
    title: str
    content: str
    relevance_score: float
    retrieval_method: str
    hop_count: int = 0
    relationship_chain: List[Dict[str, Any]] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class AssembledContext:
    """The assembled context ready for LLM prompt."""
    formatted_context: str
    sources: List[CitationSource]
    total_tokens_approx: int
    truncated: bool = False


@dataclass
class ContextConfig:
    """Configuration for context assembly."""
    max_tokens: int = 4000  # Token budget for context
    max_content_per_source: int = 800  # Max chars per source
    include_metadata: bool = True
    include_relationship_info: bool = True


def estimate_tokens(text: str) -> int:
    """
    Rough token count estimation.

    Approximation: ~4 characters per token for English text.

    Args:
        text: Text to estimate tokens for

    Returns:
        Estimated token count
    """
    return len(text) // 4


def truncate_content(content: str, max_chars: int) -> str:
    """
    Truncate content to max characters, preferring sentence boundaries.

    Args:
        content: Content to truncate
        max_chars: Maximum characters

    Returns:
        Truncated content
    """
    if len(content) <= max_chars:
        return content

    # Try to truncate at sentence boundary
    truncated = content[:max_chars]

    # Find last sentence end
    last_period = truncated.rfind('.')
    last_question = truncated.rfind('?')
    last_exclaim = truncated.rfind('!')

    last_sentence_end = max(last_period, last_question, last_exclaim)

    if last_sentence_end > max_chars * 0.5:  # At least half the content
        return truncated[:last_sentence_end + 1]

    # Fallback: truncate at word boundary
    last_space = truncated.rfind(' ')
    if last_space > max_chars * 0.5:
        return truncated[:last_space] + "..."

    return truncated + "..."


def format_source_header(
    source: CitationSource,
    config: ContextConfig
) -> str:
    """
    Format the header for a source in the context.

    Args:
        source: Citation source
        config: Context configuration

    Returns:
        Formatted header string
    """
    lines = []

    # Main header
    type_emoji = {
        'note': '📄',
        'chunk': '📝',
        'image': '🖼️'
    }.get(source.source_type, '📋')

    lines.append(f"{'═' * 60}")
    lines.append(f"SOURCE [{source.index}] {type_emoji} {source.title}")

    if config.include_metadata:
        relevance_pct = int(source.relevance_score * 100)
        method_display = {
            'semantic': '🔗 Semantic match',
            'wikilink': '🕸️ Wikilink connection',
            'fulltext': '🔤 Keyword match',
            'image_tag': '🏷️ Tag match',
            'image_link': '🔗 Linked image',
            'direct': '📌 Direct reference'
        }.get(source.retrieval_method, source.retrieval_method)

        lines.append(f"Relevance: {relevance_pct}% | Found via: {method_display}")

    if config.include_relationship_info and source.relationship_chain:
        explanation = get_relationship_explanation(source.relationship_chain)
        lines.append(f"Connection: {explanation}")

    if source.hop_count > 0:
        lines.append(f"Distance: {source.hop_count} hop(s) from query")

    lines.append(f"{'─' * 60}")

    return '\n'.join(lines)


def build_context(
    ranked_results: List[RankedResult],
    config: ContextConfig = None
) -> AssembledContext:
    """
    Build formatted context from ranked results.

    Args:
        ranked_results: Results from ranking module
        config: Context configuration

    Returns:
        AssembledContext with formatted text and source list
    """
    if config is None:
        config = ContextConfig()

    sources: List[CitationSource] = []
    context_parts: List[str] = []
    total_chars = 0
    truncated = False

    # Approximate max chars from token budget
    max_chars = config.max_tokens * 4

    for i, rr in enumerate(ranked_results):
        citation_index = i + 1
        result = rr.result

        # Extract relationship chain if present
        relationship_chain = result.metadata.get('relationship_chain', [])
        hop_count = result.metadata.get('hop_count', 0)

        # Create citation source
        source = CitationSource(
            index=citation_index,
            source_type=result.source_type,
            source_id=result.source_id,
            title=result.title,
            content=result.content,
            relevance_score=rr.final_score,
            retrieval_method=result.retrieval_method,
            hop_count=hop_count,
            relationship_chain=relationship_chain,
            metadata=result.metadata
        )

        # Format source content
        header = format_source_header(source, config)
        content = truncate_content(result.content, config.max_content_per_source)
        footer = f"{'═' * 60}\n"

        source_text = f"{header}\n{content}\n{footer}"

        # Check token budget
        if total_chars + len(source_text) > max_chars:
            if not sources:
                # At least include one source
                source_text = truncate_content(source_text, max_chars)
                truncated = True
            else:
                truncated = True
                break

        sources.append(source)
        context_parts.append(source_text)
        total_chars += len(source_text)

    formatted_context = '\n'.join(context_parts)

    logger.info(
        f"Built context with {len(sources)} sources, "
        f"~{estimate_tokens(formatted_context)} tokens"
    )

    return AssembledContext(
        formatted_context=formatted_context,
        sources=sources,
        total_tokens_approx=estimate_tokens(formatted_context),
        truncated=truncated
    )


def sources_to_citation_list(sources: List[CitationSource]) -> List[Dict[str, Any]]:
    """
    Convert sources to a list suitable for API response.

    Args:
        sources: List of citation sources

    Returns:
        List of citation dictionaries
    """
    citations = []

    for source in sources:
        citation = {
            'index': source.index,
            'source_type': source.source_type,
            'source_id': source.source_id,
            'title': source.title,
            'relevance_score': round(source.relevance_score, 3),
            'retrieval_method': source.retrieval_method,
            'used_content': truncate_content(source.content, 200),  # Short preview
            'hop_count': source.hop_count,
        }

        if source.relationship_chain:
            citation['relationship_chain'] = source.relationship_chain

        # Add image-specific fields
        if source.source_type == 'image':
            citation['thumbnail_url'] = f"/images/{source.source_id}/thumbnail"
            citation['filename'] = source.metadata.get('filename', '')

        citations.append(citation)

    return citations


def extract_citations_from_response(
    response: str,
    sources: List[CitationSource]
) -> List[int]:
    """
    Extract which citation indices were actually used in the response.

    Args:
        response: LLM response text
        sources: Available citation sources

    Returns:
        List of citation indices that were used
    """
    # Find all [N] patterns in response
    pattern = r'\[(\d+)\]'
    matches = re.findall(pattern, response)

    used_indices = set()
    max_index = len(sources)

    for match in matches:
        try:
            index = int(match)
            if 1 <= index <= max_index:
                used_indices.add(index)
        except ValueError:
            continue

    return sorted(list(used_indices))


def get_unused_sources(
    sources: List[CitationSource],
    used_indices: List[int]
) -> List[CitationSource]:
    """
    Get sources that were provided but not cited in the response.

    Args:
        sources: All provided sources
        used_indices: Indices that were actually used

    Returns:
        List of unused sources
    """
    used_set = set(used_indices)
    return [s for s in sources if s.index not in used_set]
