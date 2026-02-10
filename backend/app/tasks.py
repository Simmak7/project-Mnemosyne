"""
Celery tasks for image processing - COMPATIBILITY SHIM.

This module re-exports tasks from the new location for backwards compatibility.
New code should import from features.images.tasks instead.

DEPRECATED: Use features.images.tasks directly.
"""

# Re-export all tasks and utilities from new locations
from features.images.tasks import (
    analyze_image_task,
    DatabaseTask,
)
from features.images.tasks_helpers import (
    extract_image_metadata,
    generate_note_title,
    extract_summary_from_analysis,
    format_note_content,
    extract_tags_from_ai_response,
)

__all__ = [
    "analyze_image_task",
    "extract_image_metadata",
    "generate_note_title",
    "extract_summary_from_analysis",
    "format_note_content",
    "extract_tags_from_ai_response",
    "DatabaseTask",
]
