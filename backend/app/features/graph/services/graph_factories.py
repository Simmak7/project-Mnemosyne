"""
Graph Node and Edge Factory Functions

Static factory methods for creating TypedNode and TypedEdge objects.
Extracted from TypedGraphBuilder for modularity.
"""

from typing import Any
from .graph_index import TypedNode, TypedEdge, NodeType, EdgeType


# Edge weight constants
WEIGHT_WIKILINK = 1.0  # Explicit links are strongest
WEIGHT_TAG = 0.7  # Shared tags are medium-strong
WEIGHT_IMAGE = 0.6  # Image references
WEIGHT_SOURCE = 0.9  # Document-to-note source link
WEIGHT_SESSION = 0.2  # Same-day creation (weak)
# Semantic weights are dynamic (0.3 - 0.9 based on similarity)


# =============================================================================
# Node Factory Functions
# =============================================================================

def note_to_typed_node(note: Any) -> TypedNode:
    """Convert a Note model to TypedNode."""
    return TypedNode(
        id=f"note-{note.id}",
        type=NodeType.NOTE,
        title=note.title or "Untitled",
        metadata={
            "slug": note.slug,
            "created_at": note.created_at.isoformat() if note.created_at else None,
            "updated_at": note.updated_at.isoformat() if note.updated_at else None,
            "excerpt": (note.content or "")[:500],
            "full_excerpt": (note.content or "")[:1500],
            "community_id": note.community_id,
        }
    )


def tag_to_typed_node(tag: Any, note_count: int = 0) -> TypedNode:
    """Convert a Tag model to TypedNode."""
    return TypedNode(
        id=f"tag-{tag.id}",
        type=NodeType.TAG,
        title=tag.name,
        metadata={
            "note_count": note_count,
            "created_at": tag.created_at.isoformat() if tag.created_at else None,
        }
    )


def image_to_typed_node(image: Any) -> TypedNode:
    """Convert an Image model to TypedNode."""
    return TypedNode(
        id=f"image-{image.id}",
        type=NodeType.IMAGE,
        title=image.display_name or image.filename,
        metadata={
            "filename": image.filename,
            "thumbnail": image.blur_hash,
            "width": image.width,
            "height": image.height,
            "uploaded_at": image.uploaded_at.isoformat() if image.uploaded_at else None,
        }
    )


def document_to_typed_node(doc: Any) -> TypedNode:
    """Convert a Document model to TypedNode."""
    return TypedNode(
        id=f"document-{doc.id}",
        type=NodeType.DOCUMENT,
        title=doc.display_name or doc.filename,
        metadata={
            "filename": doc.filename,
            "document_type": doc.document_type,
            "page_count": doc.page_count,
            "summary_note_id": doc.summary_note_id,
            "uploaded_at": doc.uploaded_at.isoformat() if doc.uploaded_at else None,
        }
    )


# =============================================================================
# Edge Factory Functions
# =============================================================================

def create_wikilink_edge(source_note_id: int, target_note_id: int) -> TypedEdge:
    """Create a wikilink edge between two notes."""
    return TypedEdge(
        source=f"note-{source_note_id}",
        target=f"note-{target_note_id}",
        type=EdgeType.WIKILINK,
        weight=WEIGHT_WIKILINK,
    )


def create_tag_edge(note_id: int, tag_id: int) -> TypedEdge:
    """Create a tag assignment edge."""
    return TypedEdge(
        source=f"note-{note_id}",
        target=f"tag-{tag_id}",
        type=EdgeType.TAG,
        weight=WEIGHT_TAG,
    )


def create_image_edge(note_id: int, image_id: int, reverse: bool = False) -> TypedEdge:
    """Create a note-image reference edge.

    Args:
        note_id: The note ID
        image_id: The image ID
        reverse: If True, creates image→note edge instead of note→image
    """
    if reverse:
        return TypedEdge(
            source=f"image-{image_id}",
            target=f"note-{note_id}",
            type=EdgeType.IMAGE,
            weight=WEIGHT_IMAGE,
        )
    return TypedEdge(
        source=f"note-{note_id}",
        target=f"image-{image_id}",
        type=EdgeType.IMAGE,
        weight=WEIGHT_IMAGE,
    )


def create_source_edge(doc_id: int, note_id: int) -> TypedEdge:
    """Create a document-to-note source edge."""
    return TypedEdge(
        source=f"document-{doc_id}",
        target=f"note-{note_id}",
        type=EdgeType.SOURCE,
        weight=WEIGHT_SOURCE,
    )


def create_semantic_edge(
    source_type: str,
    source_id: int,
    target_type: str,
    target_id: int,
    similarity: float
) -> TypedEdge:
    """Create a semantic similarity edge."""
    return TypedEdge(
        source=f"{source_type}-{source_id}",
        target=f"{target_type}-{target_id}",
        type=EdgeType.SEMANTIC,
        weight=similarity,
    )
