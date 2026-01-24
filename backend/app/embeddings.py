"""
Embedding generation module - COMPATIBILITY SHIM.

This module re-exports functions from the new location for backwards compatibility.
New code should import from features.search.logic.embeddings instead.

DEPRECATED: Use features.search.logic.embeddings directly.
"""

# Re-export all functions from new location
from features.search.logic.embeddings import (
    generate_embedding,
    prepare_note_text,
    cosine_similarity,
    check_ollama_health,
    batch_generate_embeddings,
    OLLAMA_HOST,
    EMBEDDING_MODEL,
    EMBEDDING_DIMENSION,
    MAX_TEXT_LENGTH,
)

__all__ = [
    "generate_embedding",
    "prepare_note_text",
    "cosine_similarity",
    "check_ollama_health",
    "batch_generate_embeddings",
    "OLLAMA_HOST",
    "EMBEDDING_MODEL",
    "EMBEDDING_DIMENSION",
    "MAX_TEXT_LENGTH",
]
