"""
Graph Feature - Batch Query Helpers

Efficient batch operations for graph data generation.
Eliminates N+1 query patterns by resolving wikilinks,
backlinks, and tag counts in bulk.
"""

import logging
from typing import Dict, List, Set
from collections import defaultdict
from sqlalchemy.orm import Session
from sqlalchemy import func

import models
from features.graph.wikilink_parser import extract_wikilinks, parse_wikilink, create_slug

logger = logging.getLogger(__name__)


def batch_extract_wikilinks(
    notes: List[models.Note],
) -> Dict[int, List[str]]:
    """
    Extract wikilink targets from all notes in Python (no DB calls).

    Returns:
        Dict mapping note_id -> list of raw wikilink target strings
    """
    result: Dict[int, List[str]] = {}
    for note in notes:
        if note.content:
            raw_links = extract_wikilinks(note.content)
            targets = []
            for raw in raw_links:
                target, _ = parse_wikilink(raw)
                if target:
                    targets.append(target)
            result[note.id] = targets
        else:
            result[note.id] = []
    return result


def batch_resolve_wikilinks(
    db: Session,
    notes: List[models.Note],
    owner_id: int,
) -> Dict[int, List[int]]:
    """
    Resolve wikilinks for ALL notes in minimal DB queries.

    Instead of N queries (one per wikilink), does:
    1. Extract all wikilink targets in Python
    2. Compute all slugs and collect all titles
    3. ONE query to find all matching notes
    4. Map results back to source notes

    Returns:
        Dict mapping source_note_id -> list of target note IDs
    """
    wikilinks_by_note = batch_extract_wikilinks(notes)

    # Collect all unique slugs and titles for a single lookup
    all_slugs: Set[str] = set()
    all_titles: Set[str] = set()
    slug_to_targets: Dict[str, str] = {}  # slug -> original target

    for targets in wikilinks_by_note.values():
        for target in targets:
            slug = create_slug(target)
            all_slugs.add(slug)
            all_titles.add(target.lower())
            slug_to_targets[slug] = target

    if not all_slugs and not all_titles:
        return {note.id: [] for note in notes}

    # Single query: find all notes matching any slug or title
    from sqlalchemy import or_, func as sa_func
    matching_notes = db.query(models.Note).filter(
        models.Note.owner_id == owner_id,
        or_(
            models.Note.slug.in_(list(all_slugs)),
            sa_func.lower(models.Note.title).in_(list(all_titles))
        )
    ).all()

    # Build lookup: slug -> note_id and lowercase_title -> note_id
    slug_to_id: Dict[str, int] = {}
    title_to_id: Dict[str, int] = {}
    for note in matching_notes:
        if note.slug:
            slug_to_id[note.slug] = note.id
        if note.title:
            title_to_id[note.title.lower()] = note.id

    # Map results back to source notes
    result: Dict[int, List[int]] = {}
    for note in notes:
        linked_ids: Set[int] = set()
        for target in wikilinks_by_note.get(note.id, []):
            slug = create_slug(target)
            target_id = slug_to_id.get(slug) or title_to_id.get(target.lower())
            if target_id and target_id != note.id:
                linked_ids.add(target_id)
        result[note.id] = list(linked_ids)

    return result


def batch_find_backlinks(
    notes: List[models.Note],
) -> Dict[int, List[int]]:
    """
    Find backlinks for ALL notes using in-memory content scanning.

    Instead of N * M DB queries, scans each note's content for
    [[title]] and [[slug]] patterns of every other note.

    Returns:
        Dict mapping target_note_id -> list of source note IDs that link to it
    """
    # Build patterns for each note: what strings would link TO this note
    note_patterns: Dict[int, List[str]] = {}
    for note in notes:
        patterns = []
        if note.title:
            patterns.append(f"[[{note.title}]]")
            patterns.append(f"[[{note.title}|")
        if note.slug:
            patterns.append(f"[[{note.slug}]]")
            patterns.append(f"[[{note.slug}|")
        note_patterns[note.id] = patterns

    # Scan all notes' content for these patterns
    backlinks: Dict[int, Set[int]] = defaultdict(set)
    for source_note in notes:
        if not source_note.content:
            continue
        content = source_note.content
        for target_id, patterns in note_patterns.items():
            if target_id == source_note.id:
                continue
            for pattern in patterns:
                if pattern in content:
                    backlinks[target_id].add(source_note.id)
                    break  # One match is enough

    return {nid: list(sids) for nid, sids in backlinks.items()}


def batch_backlink_counts(
    notes: List[models.Note],
) -> Dict[int, int]:
    """
    Count backlinks for ALL notes at once using in-memory scanning.

    Returns:
        Dict mapping note_id -> backlink count
    """
    backlinks = batch_find_backlinks(notes)
    return {note.id: len(backlinks.get(note.id, [])) for note in notes}


def batch_tag_note_counts(
    db: Session,
    tag_ids: List[int],
    owner_id: int,
) -> Dict[int, int]:
    """
    Count notes per tag in a single GROUP BY query.

    Instead of N separate COUNT queries (one per tag), does ONE query.

    Returns:
        Dict mapping tag_id -> note count
    """
    if not tag_ids:
        return {}

    rows = db.query(
        models.NoteTag.tag_id,
        func.count(models.NoteTag.note_id).label("cnt"),
    ).join(
        models.Note, models.Note.id == models.NoteTag.note_id
    ).filter(
        models.NoteTag.tag_id.in_(tag_ids),
        models.Note.owner_id == owner_id,
    ).group_by(
        models.NoteTag.tag_id,
    ).all()

    counts = {tag_id: cnt for tag_id, cnt in rows}
    # Fill in zeros for tags with no notes
    for tid in tag_ids:
        counts.setdefault(tid, 0)
    return counts
