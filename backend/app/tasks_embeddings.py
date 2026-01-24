"""
Celery tasks for embedding generation - COMPATIBILITY SHIM.

This module re-exports tasks from the new location for backwards compatibility.
New code should import from features.search.tasks instead.

DEPRECATED: Use features.search.tasks directly.
"""

# Re-export all tasks from new location
from features.search.tasks import (
    generate_note_embedding_task,
    regenerate_all_embeddings_task,
)

__all__ = [
    "generate_note_embedding_task",
    "regenerate_all_embeddings_task",
]
