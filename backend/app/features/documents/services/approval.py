"""
Document Approval Service

Handles the approval flow:
1. Build note title and content from approved suggestions
2. Resolve wikilinks against existing notes
3. Create note via notes service
4. Apply tags to both document and note
5. Link document to summary note
6. Queue embedding generation
"""

import logging
from datetime import datetime, timezone
from typing import Dict, List, Optional

from sqlalchemy.orm import Session
from sqlalchemy import or_

from models import Document, Note
from features.graph.wikilink_parser import create_slug

logger = logging.getLogger(__name__)


class DocumentApprovalService:
    """Handles document approval and summary note creation."""

    @staticmethod
    def approve_and_create_note(
        db: Session,
        document: Document,
        owner_id: int,
        approved_tags: List[str],
        approved_wikilinks: List[str],
        summary_title: Optional[str] = None,
        summary_content: Optional[str] = None,
    ) -> Dict:
        """
        Approve suggestions and create a linked summary note.

        Returns:
            {"note_id": int, "tags_applied": list[str]}
        """
        from features.notes.service import create_note
        from crud import get_or_create_tag

        # Build note title
        title = summary_title or _build_title(document)

        # Build note content
        if summary_content:
            # User provided/edited content - still append resolved wikilinks
            content = summary_content
            if approved_wikilinks:
                resolved = _resolve_wikilink_titles(db, owner_id, approved_wikilinks)
                links = ", ".join(f"[[{w}]]" for w in resolved)
                content += f"\n\n**Related:** {links}"
        else:
            # Build from document AI summary + wikilinks
            content = _build_content(db, document, approved_wikilinks, owner_id)

        # Append source reference and tags
        content += _build_footer(document, approved_tags)

        # Create the note (create_note commits internally)
        note = create_note(
            db=db,
            title=title,
            content=content,
            owner_id=owner_id,
            source='document_analysis',
            is_standalone=False,
        )

        logger.info(f"Created summary note {note.id} for document {document.id}")

        # Apply tags using savepoints so a failed tag doesn't roll back the note
        tags_applied = []
        for tag_name in approved_tags:
            try:
                nested = db.begin_nested()
                tag = get_or_create_tag(db, tag_name, owner_id)
                if tag not in document.tags:
                    document.tags.append(tag)
                if tag not in note.tags:
                    note.tags.append(tag)
                nested.commit()
                tags_applied.append(tag_name)
            except Exception as e:
                logger.warning(f"Failed to apply tag '{tag_name}': {e}")
                nested.rollback()

        # Link document to note
        document.summary_note_id = note.id
        document.ai_analysis_status = "completed"
        document.approved_at = datetime.now(timezone.utc)

        try:
            db.commit()
        except Exception as e:
            db.rollback()
            logger.error(f"Failed to commit approval: {e}")
            raise

        # Queue embedding generation for the note (non-blocking)
        try:
            from tasks_embeddings import generate_note_embedding_task
            generate_note_embedding_task.delay(note.id)
        except Exception as e:
            logger.warning(f"Failed to queue embedding for note {note.id}: {e}")

        # Queue document chunking + embedding generation (non-blocking)
        try:
            from features.documents.tasks import generate_document_embeddings_task
            generate_document_embeddings_task.delay(document.id)
        except Exception as e:
            logger.warning(f"Failed to queue doc embeddings for {document.id}: {e}")

        return {"note_id": note.id, "tags_applied": tags_applied}


def _build_title(document: Document) -> str:
    """Build note title from document metadata."""
    name = document.display_name or document.filename
    # Remove extension
    if "." in name:
        name = name.rsplit(".", 1)[0]
    return name


def _resolve_wikilink_titles(
    db: Session, owner_id: int, wikilinks: List[str]
) -> List[str]:
    """
    Resolve AI-suggested wikilink names against existing notes.

    For each wikilink entity name, checks if a note with matching
    slug or title exists. If found, uses the exact note title for
    reliable graph resolution. If not found, keeps the original name.
    """
    resolved = []
    for entity_name in wikilinks:
        slug = create_slug(entity_name)
        match = db.query(Note).filter(
            Note.owner_id == owner_id,
            Note.is_trashed == False,
            or_(
                Note.slug == slug,
                Note.title.ilike(entity_name),
            ),
        ).first()
        if match:
            resolved.append(match.title)
        else:
            resolved.append(entity_name)
    return resolved


def _build_content(
    db: Session,
    document: Document,
    wikilinks: List[str],
    owner_id: int,
) -> str:
    """Build note content from AI summary and resolved wikilinks."""
    parts = []

    if document.ai_summary:
        parts.append(document.ai_summary)

    # Resolve wikilinks against existing notes for reliable graph edges
    if wikilinks:
        resolved = _resolve_wikilink_titles(db, owner_id, wikilinks)
        links = ", ".join(f"[[{w}]]" for w in resolved)
        parts.append(f"\n**Related:** {links}")

    return "\n\n".join(parts)


def _build_footer(document: Document, tags: List[str]) -> str:
    """Build source reference and tags footer."""
    footer_parts = []

    # Source reference
    name = document.display_name or document.filename
    footer_parts.append(f"\n\n---\n**Source:** {name}")

    if document.page_count:
        footer_parts.append(f" ({document.page_count} pages)")

    # Tags
    if tags:
        tag_str = " ".join(f"#{t}" for t in tags)
        footer_parts.append(f"\n**Tags:** {tag_str}")

    return "".join(footer_parts)
