"""
Notes Feature - AI Enhancement Endpoints

AI-powered note improvements: title generation, summarization, wikilink suggestions.
"""

import logging
from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session

from core.database import get_db
from core.auth import get_current_active_user
from core import exceptions
from slowapi import Limiter
from slowapi.util import get_remote_address

from features.notes import service
import models

logger = logging.getLogger(__name__)
limiter = Limiter(key_func=get_remote_address)

router = APIRouter(tags=["Notes"])


@router.post("/notes/{note_id}/improve-title")
@limiter.limit("10/minute")
async def improve_note_title(
    request: Request,
    note_id: int,
    current_user: models.User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Use AI to generate an improved title for a note."""
    logger.info(f"AI title improvement requested for note {note_id}")

    try:
        note = service.get_note(db, note_id=note_id)
        if not note:
            raise exceptions.ResourceNotFoundException("Note", note_id)
        if note.owner_id != current_user.id:
            raise exceptions.AuthorizationException("Not authorized")

        from features.notes import ai_service
        improved = ai_service.improve_title(note.content or "", note.title)

        return {"original_title": note.title, "improved_title": improved}

    except exceptions.AppException:
        raise
    except Exception as e:
        logger.error(f"Error improving title: {str(e)}", exc_info=True)
        raise exceptions.OllamaServiceException("Failed to improve title")


@router.post("/notes/{note_id}/summarize")
@limiter.limit("10/minute")
async def summarize_note(
    request: Request,
    note_id: int,
    current_user: models.User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Use AI to generate a summary of a note."""
    logger.info(f"AI summarization requested for note {note_id}")

    try:
        note = service.get_note(db, note_id=note_id)
        if not note:
            raise exceptions.ResourceNotFoundException("Note", note_id)
        if note.owner_id != current_user.id:
            raise exceptions.AuthorizationException("Not authorized")

        from features.notes import ai_service
        summary = ai_service.summarize_note(note.content or "", note.title)

        return {"title": note.title, "summary": summary}

    except exceptions.AppException:
        raise
    except Exception as e:
        logger.error(f"Error summarizing note: {str(e)}", exc_info=True)
        raise exceptions.OllamaServiceException("Failed to summarize note")


@router.post("/notes/{note_id}/suggest-wikilinks")
@limiter.limit("10/minute")
async def suggest_note_wikilinks(
    request: Request,
    note_id: int,
    current_user: models.User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Use AI to suggest potential wikilink connections."""
    logger.info(f"AI wikilink suggestions requested for note {note_id}")

    try:
        note = service.get_note(db, note_id=note_id)
        if not note:
            raise exceptions.ResourceNotFoundException("Note", note_id)
        if note.owner_id != current_user.id:
            raise exceptions.AuthorizationException("Not authorized")

        from features.notes import ai_service
        suggestions = ai_service.suggest_wikilinks(
            db, note_id, note.content or "", note.title, current_user.id
        )

        return {"note_id": note_id, "suggestions": suggestions}

    except exceptions.AppException:
        raise
    except Exception as e:
        logger.error(f"Error suggesting wikilinks: {str(e)}", exc_info=True)
        raise exceptions.OllamaServiceException("Failed to suggest wikilinks")


@router.post("/notes/{note_id}/enhance")
@limiter.limit("5/minute")
async def enhance_note_all(
    request: Request,
    note_id: int,
    current_user: models.User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Run all AI enhancements on a note (title, summary, wikilinks)."""
    logger.info(f"Full AI enhancement requested for note {note_id}")

    try:
        note = service.get_note(db, note_id=note_id)
        if not note:
            raise exceptions.ResourceNotFoundException("Note", note_id)
        if note.owner_id != current_user.id:
            raise exceptions.AuthorizationException("Not authorized")

        from features.notes import ai_service
        results = ai_service.enhance_note(
            db, note_id, note.content or "", note.title, current_user.id
        )

        return {
            "note_id": note_id,
            "original_title": note.title,
            **results
        }

    except exceptions.AppException:
        raise
    except Exception as e:
        logger.error(f"Error enhancing note: {str(e)}", exc_info=True)
        raise exceptions.OllamaServiceException("Failed to enhance note")


@router.post("/notes/{note_id}/regenerate")
@limiter.limit("5/minute")
async def regenerate_note_from_source(
    request: Request,
    note_id: int,
    apply: bool = False,
    current_user: models.User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Regenerate note content from its linked source image.

    Re-analyzes the linked image using AI and generates fresh content.
    Use apply=true to automatically update the note with the new content.
    """
    logger.info(f"Regenerate from source requested for note {note_id}")

    try:
        from features.notes import ai_service

        # Get regenerated content
        result = ai_service.regenerate_from_source(
            db=db,
            note_id=note_id,
            owner_id=current_user.id
        )

        # Optionally apply changes to the note
        if apply:
            note = service.update_note(
                db=db,
                note_id=note_id,
                owner_id=current_user.id,
                title=result["new_title"],
                content=result["new_content"]
            )

            # Add extracted tags to the note
            extracted_tags = result.get("extracted_tags", [])
            if extracted_tags:
                from crud import get_or_create_tag
                for tag_name in extracted_tags:
                    try:
                        tag = get_or_create_tag(db, tag_name, current_user.id)
                        if tag and tag not in note.tags:
                            note.tags.append(tag)
                    except Exception as tag_err:
                        logger.warning(f"Failed to add tag '{tag_name}': {tag_err}")
                try:
                    db.commit()
                except Exception:
                    db.rollback()

            return {
                "note_id": note_id,
                "applied": True,
                "new_title": result["new_title"],
                "new_content": result["new_content"],
                "image_id": result["image_id"],
                "tags_added": extracted_tags
            }

        return {
            "note_id": note_id,
            "applied": False,
            "new_title": result["new_title"],
            "new_content": result["new_content"],
            "image_id": result["image_id"],
            "tags_available": result.get("extracted_tags", [])
        }

    except ValueError as e:
        logger.warning(f"Regenerate failed: {str(e)}")
        raise exceptions.ValidationException(str(e))
    except exceptions.AppException:
        raise
    except Exception as e:
        logger.error(f"Error regenerating note: {str(e)}", exc_info=True)
        raise exceptions.OllamaServiceException("Failed to regenerate from source")
