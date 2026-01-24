"""
Graph Feature - Service Layer

Provides business logic for:
- Wikilink resolution
- Backlink detection
- Graph data generation
- Orphaned note detection
"""

import logging
from typing import List, Set, Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import or_

import models
from features.graph.wikilink_parser import extract_wikilinks, parse_wikilink, create_slug

logger = logging.getLogger(__name__)


# ============================================
# Wikilink Resolution
# ============================================

def resolve_wikilinks(
    db: Session,
    note_id: int,
    content: str,
    owner_id: int
) -> List[int]:
    """
    Extract wikilinks from content and resolve them to note IDs.

    Wikilinks can reference notes by:
    - Title (case-insensitive)
    - Slug
    - ID (if numeric)

    Args:
        db: Database session
        note_id: ID of the note containing the wikilinks (to avoid self-references)
        content: Markdown content containing [[wikilinks]]
        owner_id: Owner ID for multi-tenant security

    Returns:
        List of resolved note IDs (excluding the current note)

    Example:
        If content contains "See [[My Note]] and [[another-note]]"
        Returns: [5, 12] (IDs of matching notes)
    """
    wikilinks = extract_wikilinks(content)
    linked_note_ids: Set[int] = set()

    for wikilink in wikilinks:
        target, _ = parse_wikilink(wikilink)

        if not target:
            continue

        # Try to resolve by slug or title (case-insensitive)
        target_slug = create_slug(target)

        linked_note = db.query(models.Note).filter(
            models.Note.owner_id == owner_id,
            or_(
                models.Note.slug == target_slug,
                models.Note.title.ilike(target)  # Case-insensitive title match
            )
        ).first()

        if linked_note and linked_note.id != note_id:
            linked_note_ids.add(linked_note.id)

    return list(linked_note_ids)


def get_backlinks(
    db: Session,
    note_id: int,
    owner_id: int
) -> List[int]:
    """
    Find all notes that link TO this note (backlinks).

    Searches for wikilinks that reference the target note by:
    - Title
    - Slug

    Args:
        db: Database session
        note_id: ID of the note to find backlinks for
        owner_id: Owner ID for multi-tenant security

    Returns:
        List of note IDs that contain wikilinks to this note

    Example:
        If note "My Note" has ID 5,
        and other notes contain [[My Note]] or [[my-note]],
        those note IDs will be returned
    """
    current_note = db.query(models.Note).filter(
        models.Note.id == note_id,
        models.Note.owner_id == owner_id
    ).first()

    if not current_note:
        return []

    # Build search patterns for this note
    search_patterns = []

    # Pattern 1: [[Title]]
    search_patterns.append(f"[[{current_note.title}]]")

    # Pattern 2: [[slug]]
    if current_note.slug:
        search_patterns.append(f"[[{current_note.slug}]]")

    # Pattern 3: [[Title|alias]] (partial match)
    # This will catch [[Title|any alias text]]
    search_patterns.append(f"[[{current_note.title}|")
    if current_note.slug:
        search_patterns.append(f"[[{current_note.slug}|")

    # Query for notes containing any of these patterns
    backlink_note_ids: Set[int] = set()

    for pattern in search_patterns:
        notes = db.query(models.Note).filter(
            models.Note.owner_id == owner_id,
            models.Note.id != note_id,  # Exclude self
            models.Note.content.contains(pattern)
        ).all()

        for note in notes:
            backlink_note_ids.add(note.id)

    return list(backlink_note_ids)


def get_or_create_note_by_wikilink(
    db: Session,
    wikilink_target: str,
    owner_id: int,
    auto_create: bool = False
) -> Optional[models.Note]:
    """
    Get a note by wikilink target, optionally creating it if it doesn't exist.

    Args:
        db: Database session
        wikilink_target: The target from a [[wikilink]]
        owner_id: Owner ID for the note
        auto_create: If True, create a stub note if not found

    Returns:
        Note model or None
    """
    target_slug = create_slug(wikilink_target)

    # Try to find existing note
    note = db.query(models.Note).filter(
        models.Note.owner_id == owner_id,
        or_(
            models.Note.slug == target_slug,
            models.Note.title.ilike(wikilink_target)
        )
    ).first()

    if note:
        return note

    if auto_create:
        # Create stub note
        new_note = models.Note(
            title=wikilink_target,
            slug=target_slug,
            content=f"# {wikilink_target}\n\n*This note was auto-created from a wikilink.*",
            owner_id=owner_id
        )
        db.add(new_note)
        db.commit()
        db.refresh(new_note)
        return new_note

    return None


# ============================================
# Graph Data Generation
# ============================================

def get_note_graph_data(
    db: Session,
    note_id: int,
    owner_id: int,
    depth: int = 1
) -> dict:
    """
    Get graph data for a note including connected notes.

    Args:
        db: Database session
        note_id: Starting note ID
        owner_id: Owner ID for security
        depth: How many levels of connections to traverse (1 = direct connections only)

    Returns:
        Dictionary with nodes and edges for graph visualization
        {
            "nodes": [{"id": 1, "title": "Note", "slug": "note"}],
            "edges": [{"source": 1, "target": 2, "type": "wikilink"}]
        }
    """
    visited_ids: Set[int] = set()
    nodes = []
    edges = []

    def add_note_connections(current_id: int, current_depth: int):
        if current_id in visited_ids or current_depth > depth:
            return

        visited_ids.add(current_id)

        # Get note
        note = db.query(models.Note).filter(
            models.Note.id == current_id,
            models.Note.owner_id == owner_id
        ).first()

        if not note:
            return

        # Add node
        nodes.append({
            "id": note.id,
            "title": note.title,
            "slug": note.slug,
            "created_at": note.created_at.isoformat() if note.created_at else None
        })

        # Get outgoing links (wikilinks)
        linked_ids = resolve_wikilinks(db, note.id, note.content, owner_id)
        for linked_id in linked_ids:
            edges.append({
                "source": note.id,
                "target": linked_id,
                "type": "wikilink"
            })

            if current_depth < depth:
                add_note_connections(linked_id, current_depth + 1)

        # Get backlinks
        backlink_ids = get_backlinks(db, note.id, owner_id)
        for backlink_id in backlink_ids:
            # Only add edge if not already added (avoid duplicates)
            if not any(e["source"] == backlink_id and e["target"] == note.id for e in edges):
                edges.append({
                    "source": backlink_id,
                    "target": note.id,
                    "type": "backlink"
                })

            if current_depth < depth:
                add_note_connections(backlink_id, current_depth + 1)

    add_note_connections(note_id, 1)

    return {
        "nodes": nodes,
        "edges": edges
    }


def find_orphaned_notes(db: Session, owner_id: int) -> List[int]:
    """
    Find notes with no incoming or outgoing wikilinks and no tags.

    Args:
        db: Database session
        owner_id: Owner ID for multi-tenant security

    Returns:
        List of orphaned note IDs
    """
    all_notes = db.query(models.Note).filter(
        models.Note.owner_id == owner_id
    ).all()

    orphaned_ids = []

    for note in all_notes:
        # Check for outgoing links
        outgoing = resolve_wikilinks(db, note.id, note.content, owner_id)

        # Check for incoming links
        incoming = get_backlinks(db, note.id, owner_id)

        # Check for tags
        has_tags = len(note.tags) > 0

        if not outgoing and not incoming and not has_tags:
            orphaned_ids.append(note.id)

    return orphaned_ids


def get_most_linked_notes(db: Session, owner_id: int, limit: int = 10) -> List[tuple]:
    """
    Get notes with the most backlinks (most referenced).

    Args:
        db: Database session
        owner_id: Owner ID
        limit: Maximum number of results

    Returns:
        List of (note_id, title, backlink_count) tuples, sorted by count descending
    """
    notes = db.query(models.Note).filter(
        models.Note.owner_id == owner_id
    ).all()

    note_backlink_counts = []

    for note in notes:
        backlink_count = len(get_backlinks(db, note.id, owner_id))
        note_backlink_counts.append((note.id, note.title, backlink_count))

    # Sort by backlink count descending
    note_backlink_counts.sort(key=lambda x: x[2], reverse=True)

    return note_backlink_counts[:limit]


# ============================================
# Full Knowledge Graph
# ============================================

def get_full_graph_data(
    db: Session,
    owner_id: int
) -> Dict[str, Any]:
    """
    Get full knowledge graph data (all notes, tags, images) in react-force-graph format.

    Args:
        db: Database session
        owner_id: Owner ID for multi-tenant security

    Returns:
        Dictionary with nodes and links for react-force-graph:
        {
            "nodes": [
                {"id": "note-123", "title": "...", "type": "note", ...},
                {"id": "tag-456", "title": "python", "type": "tag", ...},
                {"id": "image-789", "title": "photo.jpg", "type": "image", ...}
            ],
            "links": [
                {"source": "note-123", "target": "note-456", "type": "wikilink"},
                {"source": "note-123", "target": "tag-789", "type": "tag"},
                {"source": "note-456", "target": "image-789", "type": "image"}
            ]
        }
    """
    logger.debug(f"Generating full graph data for user {owner_id}")

    notes = db.query(models.Note).filter(models.Note.owner_id == owner_id).all()
    tags = db.query(models.Tag).filter(models.Tag.owner_id == owner_id).all()
    images = db.query(models.Image).filter(models.Image.owner_id == owner_id).all()

    nodes = []
    links = []

    existing_note_ids = {note.id for note in notes}
    existing_tag_ids = {tag.id for tag in tags}
    existing_image_ids = {image.id for image in images}

    # Create note nodes
    for note in notes:
        linked_note_ids = resolve_wikilinks(db, note.id, note.content, owner_id)
        backlink_ids = get_backlinks(db, note.id, owner_id)

        nodes.append({
            "id": f"note-{note.id}",
            "title": note.title or f"Note {note.id}",
            "type": "note",
            "noteId": note.id,
            "content": note.content,
            "slug": note.slug,
            "backlinkCount": len(backlink_ids),
            "linkCount": len(linked_note_ids),
            "created_at": note.created_at.isoformat() if note.created_at else None,
        })

        # Wikilink edges (note → note)
        for target_id in linked_note_ids:
            links.append({
                "source": f"note-{note.id}",
                "target": f"note-{target_id}",
                "type": "wikilink"
            })

        # Tag edges (note → tag)
        for tag in note.tags:
            if tag.id in existing_tag_ids:
                links.append({
                    "source": f"note-{note.id}",
                    "target": f"tag-{tag.id}",
                    "type": "tag"
                })

        # Image edges (note → image)
        for image in note.images:
            if image.id in existing_image_ids:
                links.append({
                    "source": f"note-{note.id}",
                    "target": f"image-{image.id}",
                    "type": "image"
                })

    # Create tag nodes
    for tag in tags:
        tag_note_count = db.query(models.Note).join(
            models.Note.tags
        ).filter(
            models.Tag.id == tag.id,
            models.Note.owner_id == owner_id
        ).count()

        nodes.append({
            "id": f"tag-{tag.id}",
            "title": tag.name,
            "type": "tag",
            "tagId": tag.id,
            "noteCount": tag_note_count,
            "created_at": tag.created_at.isoformat() if tag.created_at else None,
        })

    # Create image nodes
    for image in images:
        nodes.append({
            "id": f"image-{image.id}",
            "title": image.filename,
            "type": "image",
            "imageId": image.id,
            "filename": image.filename,
            "created_at": image.uploaded_at.isoformat() if image.uploaded_at else None,
        })

    # Create reverse edges (image → note) for bidirectional visualization
    # This allows images to show their connected notes in the graph
    for image in images:
        for note in image.notes:
            if note.id in existing_note_ids and note.owner_id == owner_id:
                links.append({
                    "source": f"image-{image.id}",
                    "target": f"note-{note.id}",
                    "type": "image"
                })

    logger.info(f"Full graph data generated: {len(nodes)} nodes, {len(links)} links")
    return {"nodes": nodes, "links": links}
