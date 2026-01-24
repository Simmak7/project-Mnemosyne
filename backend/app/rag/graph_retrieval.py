"""
Graph-based retrieval module for RAG system.

Implements multi-hop traversal through wikilink connections:
- BFS expansion from seed notes
- Relevance decay with hop distance
- Relationship chain tracking for explainability
"""

import logging
from collections import deque
from dataclasses import dataclass, field
from typing import List, Dict, Set, Optional, Any
from sqlalchemy import text
from sqlalchemy.orm import Session

from models import Note
from .retrieval import RetrievalResult

logger = logging.getLogger(__name__)


@dataclass
class RelationshipLink:
    """A single link in a relationship chain."""
    link_type: str  # 'wikilink', 'backlink'
    from_note_id: int
    to_note_id: int
    from_title: str = ''
    to_title: str = ''


@dataclass
class GraphTraversalConfig:
    """Configuration for graph traversal."""
    max_hops: int = 2
    max_results_per_hop: int = 5
    relevance_decay: float = 0.5  # Multiply by this each hop
    include_backlinks: bool = True


def get_outgoing_wikilinks(db: Session, note_id: int, owner_id: int) -> List[Dict[str, Any]]:
    """
    Get notes that this note links TO via wikilinks.

    Args:
        db: Database session
        note_id: Source note ID
        owner_id: User ID for filtering

    Returns:
        List of linked note info dicts
    """
    try:
        result = db.execute(text("""
            SELECT
                n.id,
                n.title,
                n.content,
                n.slug
            FROM notes n
            WHERE n.owner_id = :owner_id
              AND n.id IN (
                  SELECT target_note_id
                  FROM note_wikilinks
                  WHERE source_note_id = :note_id
              )
        """), {
            "note_id": note_id,
            "owner_id": owner_id
        })

        return [
            {
                'id': row.id,
                'title': row.title,
                'content': row.content,
                'slug': row.slug,
                'link_type': 'wikilink'
            }
            for row in result
        ]

    except Exception as e:
        logger.error(f"Error getting outgoing wikilinks: {e}")
        # Rollback to clean up failed transaction state
        db.rollback()
        return []


def get_incoming_backlinks(db: Session, note_id: int, owner_id: int) -> List[Dict[str, Any]]:
    """
    Get notes that link TO this note (backlinks).

    Args:
        db: Database session
        note_id: Target note ID
        owner_id: User ID for filtering

    Returns:
        List of linking note info dicts
    """
    try:
        result = db.execute(text("""
            SELECT
                n.id,
                n.title,
                n.content,
                n.slug
            FROM notes n
            WHERE n.owner_id = :owner_id
              AND n.id IN (
                  SELECT source_note_id
                  FROM note_wikilinks
                  WHERE target_note_id = :note_id
              )
        """), {
            "note_id": note_id,
            "owner_id": owner_id
        })

        return [
            {
                'id': row.id,
                'title': row.title,
                'content': row.content,
                'slug': row.slug,
                'link_type': 'backlink'
            }
            for row in result
        ]

    except Exception as e:
        logger.error(f"Error getting incoming backlinks: {e}")
        # Rollback to clean up failed transaction state
        db.rollback()
        return []


def graph_traversal(
    db: Session,
    seed_note_ids: List[int],
    owner_id: int,
    config: GraphTraversalConfig = None
) -> List[RetrievalResult]:
    """
    Perform BFS traversal from seed notes through wikilink graph.

    Strategy:
    1. Start from seed notes (semantic matches)
    2. BFS through outgoing wikilinks and incoming backlinks
    3. Track relationship chains for explainability
    4. Apply relevance decay with hop distance

    Args:
        db: Database session
        seed_note_ids: Starting note IDs
        owner_id: User ID for filtering
        config: Traversal configuration

    Returns:
        List of RetrievalResult objects with relationship chains
    """
    if config is None:
        config = GraphTraversalConfig()

    if not seed_note_ids:
        return []

    results: List[RetrievalResult] = []
    visited: Set[int] = set(seed_note_ids)  # Don't revisit seed notes

    # BFS queue: (note_id, hop_count, relationship_chain, from_note_title)
    queue = deque()

    # Initialize queue with neighbors of seed notes
    for seed_id in seed_note_ids:
        seed_note = db.query(Note).filter(
            Note.id == seed_id,
            Note.owner_id == owner_id
        ).first()

        if not seed_note:
            continue

        seed_title = seed_note.title or 'Untitled'

        # Add outgoing wikilinks
        outgoing = get_outgoing_wikilinks(db, seed_id, owner_id)
        for linked in outgoing:
            if linked['id'] not in visited:
                chain = [RelationshipLink(
                    link_type='wikilink',
                    from_note_id=seed_id,
                    to_note_id=linked['id'],
                    from_title=seed_title,
                    to_title=linked['title'] or 'Untitled'
                )]
                queue.append((linked['id'], 1, chain, seed_title))

        # Add incoming backlinks
        if config.include_backlinks:
            incoming = get_incoming_backlinks(db, seed_id, owner_id)
            for linked in incoming:
                if linked['id'] not in visited:
                    chain = [RelationshipLink(
                        link_type='backlink',
                        from_note_id=linked['id'],
                        to_note_id=seed_id,
                        from_title=linked['title'] or 'Untitled',
                        to_title=seed_title
                    )]
                    queue.append((linked['id'], 1, chain, seed_title))

    # BFS traversal
    hop_counts = {1: 0, 2: 0}  # Track results per hop level

    while queue:
        note_id, hop_count, chain, _ = queue.popleft()

        # Check limits
        if hop_count > config.max_hops:
            continue

        if hop_counts.get(hop_count, 0) >= config.max_results_per_hop * len(seed_note_ids):
            continue

        if note_id in visited:
            continue

        visited.add(note_id)

        # Fetch the note
        note = db.query(Note).filter(
            Note.id == note_id,
            Note.owner_id == owner_id
        ).first()

        if not note:
            continue

        # Calculate relevance based on hop distance
        # hop 1: 0.5, hop 2: 0.25
        relevance = config.relevance_decay ** hop_count

        # Convert chain to serializable format
        chain_data = [
            {
                'type': link.link_type,
                'from': link.from_note_id,
                'to': link.to_note_id,
                'from_title': link.from_title,
                'to_title': link.to_title
            }
            for link in chain
        ]

        results.append(RetrievalResult(
            source_type='note',
            source_id=note.id,
            title=note.title or 'Untitled',
            content=note.content or '',
            similarity=relevance,
            retrieval_method='wikilink',
            metadata={
                'hop_count': hop_count,
                'relationship_chain': chain_data,
                'full_note': True
            }
        ))

        hop_counts[hop_count] = hop_counts.get(hop_count, 0) + 1

        # Add neighbors for next hop (if within limit)
        if hop_count < config.max_hops:
            note_title = note.title or 'Untitled'

            # Outgoing wikilinks
            outgoing = get_outgoing_wikilinks(db, note_id, owner_id)
            for linked in outgoing:
                if linked['id'] not in visited:
                    new_chain = chain + [RelationshipLink(
                        link_type='wikilink',
                        from_note_id=note_id,
                        to_note_id=linked['id'],
                        from_title=note_title,
                        to_title=linked['title'] or 'Untitled'
                    )]
                    queue.append((linked['id'], hop_count + 1, new_chain, note_title))

            # Incoming backlinks
            if config.include_backlinks:
                incoming = get_incoming_backlinks(db, note_id, owner_id)
                for linked in incoming:
                    if linked['id'] not in visited:
                        new_chain = chain + [RelationshipLink(
                            link_type='backlink',
                            from_note_id=linked['id'],
                            to_note_id=note_id,
                            from_title=linked['title'] or 'Untitled',
                            to_title=note_title
                        )]
                        queue.append((linked['id'], hop_count + 1, new_chain, note_title))

    # Sort by relevance (higher hop count = lower relevance)
    results.sort(key=lambda x: x.similarity, reverse=True)

    logger.info(
        f"Graph traversal from {len(seed_note_ids)} seeds: "
        f"{len(results)} results (hop 1: {hop_counts.get(1, 0)}, hop 2: {hop_counts.get(2, 0)})"
    )

    return results


def get_relationship_explanation(chain: List[Dict[str, Any]]) -> str:
    """
    Generate human-readable explanation of a relationship chain.

    Args:
        chain: List of relationship link dictionaries

    Returns:
        Human-readable explanation string
    """
    if not chain:
        return "Direct match"

    parts = []
    for i, link in enumerate(chain):
        if link['type'] == 'wikilink':
            if i == 0:
                parts.append(f"'{link['from_title']}' links to '{link['to_title']}'")
            else:
                parts.append(f"which links to '{link['to_title']}'")
        else:  # backlink
            if i == 0:
                parts.append(f"'{link['from_title']}' references '{link['to_title']}'")
            else:
                parts.append(f"which is referenced by '{link['from_title']}'")

    return ' → '.join(parts) if len(parts) == 1 else ', '.join(parts)


def format_relationship_chain_for_display(chain: List[Dict[str, Any]]) -> str:
    """
    Format relationship chain for UI display.

    Args:
        chain: List of relationship link dictionaries

    Returns:
        Formatted string with arrows and note titles
    """
    if not chain:
        return "Direct"

    hop_count = len(chain)
    first_link = chain[0]
    last_link = chain[-1]

    if hop_count == 1:
        link_symbol = "→" if first_link['type'] == 'wikilink' else "←"
        return f"{first_link['from_title']} {link_symbol} {first_link['to_title']}"
    else:
        # Show simplified chain
        return f"{first_link['from_title']} → ... → {last_link['to_title']} ({hop_count} hops)"
