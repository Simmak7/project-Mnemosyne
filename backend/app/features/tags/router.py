"""
Tags Feature - FastAPI Router

Endpoints for tag management and associations.

Endpoints:
- GET /tags/ - List all tags for current user
- POST /tags/ - Create a new tag (or get existing)
- POST /images/{image_id}/tags/{tag_name} - Add tag to image
- DELETE /images/{image_id}/tags/{tag_id} - Remove tag from image

Note: Note-specific tag endpoints remain in features/notes/router.py
- POST /notes/{note_id}/tags/{tag_name}
- DELETE /notes/{note_id}/tags/{tag_id}
"""

import logging
from typing import List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

import models
from core.database import get_db
from core.auth import get_current_active_user
from core.exceptions import ResourceNotFoundException, DatabaseException

from .schemas import TagCreate, TagResponse, TagAddResponse, TagRemoveResponse
from .service import TagService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/tags", tags=["Tags"])


@router.get("/", response_model=List[TagResponse])
async def get_tags(
    current_user: models.User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Get all tags for the current user.

    Returns a list of all tags owned by the authenticated user.
    Tags are stored in lowercase. Includes note_count for each tag.
    """
    logger.debug(f"Fetching tags for user {current_user.username}")

    try:
        tags = TagService.get_tags_by_user(db, owner_id=current_user.id)
        logger.info(f"Retrieved {len(tags)} tags for user {current_user.username}")
        # Build response with note counts
        result = []
        for tag in tags:
            tag_dict = {
                "id": tag.id,
                "name": tag.name,
                "created_at": tag.created_at,
                "owner_id": tag.owner_id,
                "note_count": len(tag.notes) if tag.notes else 0
            }
            result.append(TagResponse(**tag_dict))
        return result
    except Exception as e:
        logger.error(f"Error fetching tags for user {current_user.username}: {str(e)}", exc_info=True)
        raise DatabaseException("Failed to retrieve tags")


@router.post("/", response_model=TagResponse)
async def create_tag(
    tag: TagCreate,
    current_user: models.User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Create a new tag (or return existing if already exists).

    Tags are case-insensitive and stored in lowercase.
    If a tag with the same name already exists for this user,
    the existing tag is returned instead of creating a duplicate.
    """
    logger.info(f"Tag creation request from user {current_user.username}: {tag.name}")

    try:
        db_tag = TagService.get_or_create_tag(db, tag_name=tag.name, owner_id=current_user.id)
        logger.info(f"Tag '{db_tag.name}' ready for user {current_user.username} (ID: {db_tag.id})")
        return TagResponse.model_validate(db_tag)
    except Exception as e:
        logger.error(f"Error creating tag: {str(e)}", exc_info=True)
        raise DatabaseException("Failed to create tag")


# Image-tag association endpoints
# These are defined with full path since they operate on images
image_tag_router = APIRouter(tags=["Tags"])


@image_tag_router.post("/images/{image_id}/tags/{tag_name}", response_model=TagAddResponse)
async def add_tag_to_image(
    image_id: int,
    tag_name: str,
    current_user: models.User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Add a tag to an image (creates tag if it doesn't exist).

    The tag name is case-insensitive and will be stored in lowercase.
    If the tag already exists on the image, the operation succeeds
    without creating a duplicate association.
    """
    logger.info(f"Adding tag '{tag_name}' to image {image_id} for user {current_user.username}")

    try:
        tag = TagService.add_tag_to_image(db, image_id=image_id, tag_name=tag_name, owner_id=current_user.id)
        logger.info(f"Tag '{tag.name}' added to image {image_id}")
        return TagAddResponse(status="success", tag_id=tag.id, tag_name=tag.name)
    except ValueError as e:
        logger.warning(f"Failed to add tag to image: {str(e)}")
        raise ResourceNotFoundException("Image", image_id)
    except Exception as e:
        logger.error(f"Error adding tag to image: {str(e)}", exc_info=True)
        raise DatabaseException("Failed to add tag to image")


@image_tag_router.delete("/images/{image_id}/tags/{tag_id}", response_model=TagRemoveResponse)
async def remove_tag_from_image(
    image_id: int,
    tag_id: int,
    current_user: models.User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Remove a tag from an image.

    Returns success if the tag was removed, or raises 404 if the
    image or tag association was not found.
    """
    logger.info(f"Removing tag {tag_id} from image {image_id} for user {current_user.username}")

    try:
        success = TagService.remove_tag_from_image(db, image_id=image_id, tag_id=tag_id, owner_id=current_user.id)

        if success:
            logger.info(f"Tag {tag_id} removed from image {image_id}")
            return TagRemoveResponse(status="success")
        else:
            logger.warning(f"Failed to remove tag {tag_id} from image {image_id}")
            raise ResourceNotFoundException("Image or Tag", f"{image_id}/{tag_id}")
    except ResourceNotFoundException:
        raise
    except Exception as e:
        logger.error(f"Error removing tag from image: {str(e)}", exc_info=True)
        raise DatabaseException("Failed to remove tag from image")


__all__ = ["router", "image_tag_router"]
