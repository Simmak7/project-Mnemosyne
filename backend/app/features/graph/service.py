"""
Graph Feature - Service Layer

Business logic for wikilink resolution, backlink detection,
graph data generation, and orphaned note detection.
"""

import logging
from typing import List, Set, Optional, Dict, Any
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import or_

import models
from features.graph.wikilink_parser import extract_wikilinks, parse_wikilink, create_slug
from features.graph.batch_helpers import (
    batch_resolve_wikilinks,
    batch_find_backlinks,
    batch_backlink_counts,
    batch_tag_note_counts,
)

logger = logging.getLogger(__name__)


def resolve_wikilinks(
    db: Session, note_id: int, content: str, owner_id: int
) -> List[int]:
    """Extract wikilinks from content and resolve to note IDs (single-note)."""
    wikilinks = extract_wikilinks(content)
    linked_note_ids: Set[int] = set()
    for wikilink in wikilinks:
        target, _ = parse_wikilink(wikilink)
        if not target:
            continue
        target_slug = create_slug(target)
        linked_note = db.query(models.Note).filter(
            models.Note.owner_id == owner_id,
            or_(models.Note.slug == target_slug, models.Note.title.ilike(target))
        ).first()
        if linked_note and linked_note.id != note_id:
            linked_note_ids.add(linked_note.id)
    return list(linked_note_ids)


def get_backlinks(db: Session, note_id: int, owner_id: int) -> List[int]:
    """Find all notes that link TO this note via wikilinks (single-note)."""
    current_note = db.query(models.Note).filter(
        models.Note.id == note_id, models.Note.owner_id == owner_id
    ).first()
    if not current_note:
        return []

    patterns = [f"[[{current_note.title}]]", f"[[{current_note.title}|"]
    if current_note.slug:
        patterns.extend([f"[[{current_note.slug}]]", f"[[{current_note.slug}|"])

    backlink_ids: Set[int] = set()
    for pattern in patterns:
        for note in db.query(models.Note).filter(
            models.Note.owner_id == owner_id,
            models.Note.id != note_id,
            models.Note.content.contains(pattern)
        ).all():
            backlink_ids.add(note.id)
    return list(backlink_ids)


def get_or_create_note_by_wikilink(
    db: Session, wikilink_target: str, owner_id: int,
    auto_create: bool = False
) -> Optional[models.Note]:
    """Get a note by wikilink target, optionally creating a stub."""
    target_slug = create_slug(wikilink_target)
    note = db.query(models.Note).filter(
        models.Note.owner_id == owner_id,
        or_(models.Note.slug == target_slug, models.Note.title.ilike(wikilink_target))
    ).first()
    if note:
        return note
    if auto_create:
        new_note = models.Note(
            title=wikilink_target, slug=target_slug,
            content=f"# {wikilink_target}\n\n*This note was auto-created from a wikilink.*",
            owner_id=owner_id
        )
        db.add(new_note)
        db.commit()
        db.refresh(new_note)
        return new_note
    return None


def get_note_graph_data(
    db: Session, note_id: int, owner_id: int, depth: int = 1
) -> dict:
    """Get graph data for a single note with depth traversal."""
    visited_ids: Set[int] = set()
    nodes, edges = [], []

    def traverse(current_id: int, current_depth: int):
        if current_id in visited_ids or current_depth > depth:
            return
        visited_ids.add(current_id)
        note = db.query(models.Note).filter(
            models.Note.id == current_id, models.Note.owner_id == owner_id
        ).first()
        if not note:
            return
        nodes.append({
            "id": note.id, "title": note.title, "slug": note.slug,
            "created_at": note.created_at.isoformat() if note.created_at else None
        })
        for lid in resolve_wikilinks(db, note.id, note.content, owner_id):
            edges.append({"source": note.id, "target": lid, "type": "wikilink"})
            if current_depth < depth:
                traverse(lid, current_depth + 1)
        for bid in get_backlinks(db, note.id, owner_id):
            if not any(e["source"] == bid and e["target"] == note.id for e in edges):
                edges.append({"source": bid, "target": note.id, "type": "backlink"})
            if current_depth < depth:
                traverse(bid, current_depth + 1)

    traverse(note_id, 1)
    return {"nodes": nodes, "edges": edges}


def find_orphaned_notes(db: Session, owner_id: int) -> List[int]:
    """Find notes with no wikilinks (in or out) and no tags. Batch-optimized."""
    all_notes = db.query(models.Note).options(
        joinedload(models.Note.tags)
    ).filter(models.Note.owner_id == owner_id).all()
    outgoing = batch_resolve_wikilinks(db, all_notes, owner_id)
    backlinks = batch_find_backlinks(all_notes)
    return [
        note.id for note in all_notes
        if not outgoing.get(note.id) and not backlinks.get(note.id) and not note.tags
    ]


def get_most_linked_notes(
    db: Session, owner_id: int, limit: int = 10
) -> List[tuple]:
    """Get notes ranked by backlink count. Batch-optimized."""
    notes = db.query(models.Note).filter(models.Note.owner_id == owner_id).all()
    counts = batch_backlink_counts(notes)
    result = [(n.id, n.title, counts.get(n.id, 0)) for n in notes]
    result.sort(key=lambda x: x[2], reverse=True)
    return result[:limit]


def get_full_graph_data(db: Session, owner_id: int) -> Dict[str, Any]:
    """
    Full knowledge graph in react-force-graph format. Batch-optimized:
    eager-loaded relationships, single wikilink resolution query,
    in-memory backlink scan, single GROUP BY for tag counts.
    """
    logger.debug(f"Generating full graph data for user {owner_id}")

    notes = db.query(models.Note).options(
        joinedload(models.Note.tags), joinedload(models.Note.images),
    ).filter(models.Note.owner_id == owner_id).all()
    tags = db.query(models.Tag).filter(models.Tag.owner_id == owner_id).all()
    images = db.query(models.Image).options(
        joinedload(models.Image.notes),
    ).filter(models.Image.owner_id == owner_id).all()

    outgoing = batch_resolve_wikilinks(db, notes, owner_id)
    backlinks = batch_find_backlinks(notes)
    tag_counts = batch_tag_note_counts(db, [t.id for t in tags], owner_id)

    existing_tag_ids = {t.id for t in tags}
    existing_image_ids = {i.id for i in images}
    existing_note_ids = {n.id for n in notes}
    nodes, links = [], []

    for note in notes:
        linked_ids = outgoing.get(note.id, [])
        backlink_ids = backlinks.get(note.id, [])
        nodes.append({
            "id": f"note-{note.id}", "title": note.title or f"Note {note.id}",
            "type": "note", "noteId": note.id, "content": note.content,
            "slug": note.slug, "backlinkCount": len(backlink_ids),
            "linkCount": len(linked_ids),
            "created_at": note.created_at.isoformat() if note.created_at else None,
        })
        for tid in linked_ids:
            links.append({"source": f"note-{note.id}", "target": f"note-{tid}", "type": "wikilink"})
        for tag in note.tags:
            if tag.id in existing_tag_ids:
                links.append({"source": f"note-{note.id}", "target": f"tag-{tag.id}", "type": "tag"})
        for img in note.images:
            if img.id in existing_image_ids:
                links.append({"source": f"note-{note.id}", "target": f"image-{img.id}", "type": "image"})

    for tag in tags:
        nodes.append({
            "id": f"tag-{tag.id}", "title": tag.name, "type": "tag",
            "tagId": tag.id, "noteCount": tag_counts.get(tag.id, 0),
            "created_at": tag.created_at.isoformat() if tag.created_at else None,
        })

    for image in images:
        nodes.append({
            "id": f"image-{image.id}", "title": image.filename,
            "type": "image", "imageId": image.id, "filename": image.filename,
            "created_at": image.uploaded_at.isoformat() if image.uploaded_at else None,
        })
        for note in image.notes:
            if note.id in existing_note_ids and note.owner_id == owner_id:
                links.append({"source": f"image-{image.id}", "target": f"note-{note.id}", "type": "image"})

    logger.info(f"Full graph data generated: {len(nodes)} nodes, {len(links)} links")
    return {"nodes": nodes, "links": links}
