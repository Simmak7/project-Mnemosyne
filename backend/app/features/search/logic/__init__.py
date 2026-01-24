"""
Search logic module.

Contains the core search algorithms:
- fulltext.py: PostgreSQL tsvector full-text search
- semantic.py: pgvector semantic similarity search
- embeddings.py: Ollama embedding generation
- ranking.py: Result ranking and scoring
"""

from features.search.logic.fulltext import (
    parse_search_query,
    apply_date_filter,
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
    EMBEDDING_DIMENSION,
    EMBEDDING_MODEL,
)
from features.search.logic.ranking import (
    rank_combined_results,
    calculate_relevance_score,
    apply_recency_boost,
)

__all__ = [
    # Fulltext
    "parse_search_query",
    "apply_date_filter",
    "search_notes_fulltext",
    "search_images_fulltext",
    "search_tags_fuzzy",
    "search_combined",
    "search_by_tag",
    # Semantic
    "semantic_search",
    "find_similar_notes",
    "find_unlinked_mentions",
    # Embeddings
    "generate_embedding",
    "prepare_note_text",
    "cosine_similarity",
    "check_ollama_health",
    "EMBEDDING_DIMENSION",
    "EMBEDDING_MODEL",
    # Ranking
    "rank_combined_results",
    "calculate_relevance_score",
    "apply_recency_boost",
]
