"""
RAG (Retrieval-Augmented Generation) Module for Mnemosyne.

This module provides citation-aware, explainable AI chat with:
- Multi-source retrieval (semantic, wikilink graph, full-text, images)
- Source citation tracking with relevance scores
- Multi-hop relationship chain explanation
- Hybrid streaming responses

Components:
- chunking: Paragraph-based text chunking for notes and images
- retrieval: Semantic and full-text retrieval with pgvector
- image_retrieval: Image-based context retrieval
- graph_retrieval: Multi-hop wikilink graph traversal
- ranking: Reciprocal Rank Fusion (RRF) for result merging
- context_builder: Context assembly with citation markers
- prompts: RAG prompt templates
"""

# Chunking
from .chunking import (
    chunk_note_content,
    chunk_image_analysis,
    ChunkResult,
)

# Retrieval
from .retrieval import (
    RetrievalResult,
    RetrievalConfig,
    semantic_search_notes,
    semantic_search_chunks,
    semantic_search_images,
    fulltext_search_notes,
    combined_semantic_search,
    get_note_by_id,
    get_image_by_id,
)

# Image Retrieval
from .image_retrieval import (
    get_images_by_tags,
    get_images_linked_to_notes,
    get_images_from_note_tags,
    extract_potential_tags,
    combined_image_retrieval,
)

# Graph Retrieval
from .graph_retrieval import (
    GraphTraversalConfig,
    RelationshipLink,
    graph_traversal,
    get_relationship_explanation,
    format_relationship_chain_for_display,
)

# Ranking
from .ranking import (
    RankingConfig,
    RankedResult,
    reciprocal_rank_fusion,
    apply_recency_boost,
    deduplicate_results,
    enforce_source_diversity,
    merge_and_rank,
    get_retrieval_summary,
)

# Context Builder
from .context_builder import (
    ContextConfig,
    CitationSource,
    AssembledContext,
    build_context,
    sources_to_citation_list,
    extract_citations_from_response,
    get_unused_sources,
)

# Prompts
from .prompts import (
    RAGPromptConfig,
    RAG_SYSTEM_PROMPT,
    RAG_SYSTEM_PROMPT_CONCISE,
    format_user_message_with_context,
    format_no_context_message,
    format_follow_up_message,
    extract_confidence_signals,
    validate_citations,
    detect_query_type,
    get_query_specific_instructions,
)

# Intent Detection
from .intent_detector import (
    QueryIntent,
    IntentResult,
    detect_intent,
    should_skip_rag_search,
    should_include_conversation_context,
    extract_citation_references,
)

# Ollama Client
from .ollama_client import (
    call_ollama_generate,
    call_ollama_stream,
    check_ollama_health,
)

# Title Generator
from .title_generator import (
    generate_conversation_title,
)

# Cache
from .cache import (
    QueryCache,
    get_query_cache,
    get_cached_retrieval_results,
    cache_retrieval_results,
)

__all__ = [
    # Chunking
    "chunk_note_content",
    "chunk_image_analysis",
    "ChunkResult",

    # Retrieval
    "RetrievalResult",
    "RetrievalConfig",
    "semantic_search_notes",
    "semantic_search_chunks",
    "semantic_search_images",
    "fulltext_search_notes",
    "combined_semantic_search",
    "get_note_by_id",
    "get_image_by_id",

    # Image Retrieval
    "get_images_by_tags",
    "get_images_linked_to_notes",
    "get_images_from_note_tags",
    "extract_potential_tags",
    "combined_image_retrieval",

    # Graph Retrieval
    "GraphTraversalConfig",
    "RelationshipLink",
    "graph_traversal",
    "get_relationship_explanation",
    "format_relationship_chain_for_display",

    # Ranking
    "RankingConfig",
    "RankedResult",
    "reciprocal_rank_fusion",
    "apply_recency_boost",
    "deduplicate_results",
    "enforce_source_diversity",
    "merge_and_rank",
    "get_retrieval_summary",

    # Context Builder
    "ContextConfig",
    "CitationSource",
    "AssembledContext",
    "build_context",
    "sources_to_citation_list",
    "extract_citations_from_response",
    "get_unused_sources",

    # Prompts
    "RAGPromptConfig",
    "RAG_SYSTEM_PROMPT",
    "RAG_SYSTEM_PROMPT_CONCISE",
    "format_user_message_with_context",
    "format_no_context_message",
    "format_follow_up_message",
    "extract_confidence_signals",
    "validate_citations",
    "detect_query_type",
    "get_query_specific_instructions",

    # Intent Detection
    "QueryIntent",
    "IntentResult",
    "detect_intent",
    "should_skip_rag_search",
    "should_include_conversation_context",
    "extract_citation_references",

    # Ollama Client
    "call_ollama_generate",
    "call_ollama_stream",
    "check_ollama_health",

    # Title Generator
    "generate_conversation_title",

    # Cache
    "QueryCache",
    "get_query_cache",
    "get_cached_retrieval_results",
    "cache_retrieval_results",
]
