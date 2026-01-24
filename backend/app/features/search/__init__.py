"""
Search feature module.

Provides full-text search, semantic similarity search, and result ranking
using PostgreSQL tsvector and pgvector extensions.
"""

from features.search.router import router
from features.search.logic.fulltext import (
    search_notes_fulltext,
    search_images_fulltext,
    search_tags_fuzzy,
    search_combined,
    search_by_tag,
)
from features.search.logic.semantic import (
    semantic_search,
    find_similar_notes,
    find_unlinked_mentions,
)
from features.search.logic.embeddings import (
    generate_embedding,
    prepare_note_text,
    cosine_similarity,
    check_ollama_health,
)

__all__ = [
    "router",
    # Fulltext search
    "search_notes_fulltext",
    "search_images_fulltext",
    "search_tags_fuzzy",
    "search_combined",
    "search_by_tag",
    # Semantic search
    "semantic_search",
    "find_similar_notes",
    "find_unlinked_mentions",
    # Embeddings
    "generate_embedding",
    "prepare_note_text",
    "cosine_similarity",
    "check_ollama_health",
]
