"""
Images Feature - Status Endpoints

Favorites, trash, and rename operations.
"""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
import logging

from core.database import get_db
from core.auth import get_current_active_user
from core import exceptions
import models

from features.images import schemas
from features.images.service import ImageService

logger = logging.getLogger(__name__)

router = APIRouter(tags=["Image Processing"])


# =============================================================================
# Favorites Endpoints
# =============================================================================

@router.post("/images/{image_id}/favorite", response_model=schemas.ImageResponse)
async def toggle_favorite(
    image_id: int,
    current_user: models.User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Toggle the favorite status of an image.

    Returns the updated image with the new favorite status.
    """
    logger.info(f"Toggle favorite request for image {image_id} from user {current_user.username}")

    try:
        image = ImageService.toggle_favorite(
            db=db,
            image_id=image_id,
            owner_id=current_user.id
        )

        if not image:
            logger.warning(f"Image {image_id} not found for user {current_user.username}")
            raise exceptions.NotFoundException(f"Image with ID {image_id} not found")

        logger.info(f"Image {image_id} favorite status: {image.is_favorite}")
        return schemas.ImageResponse.model_validate(image)

    except exceptions.AppException:
        raise
    except ValueError as e:
        raise exceptions.ProcessingException(str(e))
    except Exception as e:
        logger.error(f"Failed to toggle favorite for image {image_id}: {str(e)}", exc_info=True)
        raise exceptions.ProcessingException(f"Failed to toggle favorite: {str(e)}")


@router.get("/images/favorites/", response_model=list[schemas.ImageResponse])
async def get_favorite_images(
    skip: int = 0,
    limit: int = 100,
    current_user: models.User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Get all favorited images for the current user.

    Returns images marked as favorites (not including trashed images).
    """
    logger.debug(f"Fetching favorite images for user {current_user.username}")

    try:
        images = ImageService.get_favorites(
            db=db,
            owner_id=current_user.id,
            skip=skip,
            limit=limit
        )
        logger.info(f"Retrieved {len(images)} favorite images for user {current_user.username}")
        return [schemas.ImageResponse.model_validate(img) for img in images]

    except Exception as e:
        logger.error(f"Error fetching favorite images for user {current_user.username}: {str(e)}", exc_info=True)
        raise exceptions.DatabaseException("Failed to retrieve favorite images")


# =============================================================================
# Trash Endpoints
# =============================================================================

@router.post("/images/{image_id}/trash", response_model=schemas.ImageResponse)
async def move_to_trash(
    image_id: int,
    current_user: models.User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Move an image to trash.

    The image can be restored later using the restore endpoint.
    Trashed images are retained for 30 days before permanent deletion.
    """
    logger.info(f"Move to trash request for image {image_id} from user {current_user.username}")

    try:
        image = ImageService.move_to_trash(
            db=db,
            image_id=image_id,
            owner_id=current_user.id
        )

        if not image:
            logger.warning(f"Image {image_id} not found for user {current_user.username}")
            raise exceptions.NotFoundException(f"Image with ID {image_id} not found")

        logger.info(f"Image {image_id} moved to trash")
        return schemas.ImageResponse.model_validate(image)

    except exceptions.AppException:
        raise
    except ValueError as e:
        raise exceptions.ProcessingException(str(e))
    except Exception as e:
        logger.error(f"Failed to move image {image_id} to trash: {str(e)}", exc_info=True)
        raise exceptions.ProcessingException(f"Failed to move to trash: {str(e)}")


@router.post("/images/{image_id}/restore", response_model=schemas.ImageResponse)
async def restore_from_trash(
    image_id: int,
    current_user: models.User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Restore an image from trash.

    The image will be returned to the main gallery.
    """
    logger.info(f"Restore from trash request for image {image_id} from user {current_user.username}")

    try:
        image = ImageService.restore_from_trash(
            db=db,
            image_id=image_id,
            owner_id=current_user.id
        )

        if not image:
            logger.warning(f"Image {image_id} not found in trash for user {current_user.username}")
            raise exceptions.NotFoundException(f"Image with ID {image_id} not found in trash")

        logger.info(f"Image {image_id} restored from trash")
        return schemas.ImageResponse.model_validate(image)

    except exceptions.AppException:
        raise
    except ValueError as e:
        raise exceptions.ProcessingException(str(e))
    except Exception as e:
        logger.error(f"Failed to restore image {image_id} from trash: {str(e)}", exc_info=True)
        raise exceptions.ProcessingException(f"Failed to restore from trash: {str(e)}")


@router.get("/images/trash/", response_model=list[schemas.ImageResponse])
async def get_trashed_images(
    skip: int = 0,
    limit: int = 100,
    current_user: models.User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Get all trashed images for the current user.

    Returns images that have been moved to trash.
    """
    logger.debug(f"Fetching trashed images for user {current_user.username}")

    try:
        images = ImageService.get_trashed(
            db=db,
            owner_id=current_user.id,
            skip=skip,
            limit=limit
        )
        logger.info(f"Retrieved {len(images)} trashed images for user {current_user.username}")
        return [schemas.ImageResponse.model_validate(img) for img in images]

    except Exception as e:
        logger.error(f"Error fetching trashed images for user {current_user.username}: {str(e)}", exc_info=True)
        raise exceptions.DatabaseException("Failed to retrieve trashed images")


@router.delete("/images/{image_id}/permanent", response_model=schemas.DeleteResponse)
async def permanent_delete(
    image_id: int,
    current_user: models.User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Permanently delete an image from trash.

    This action cannot be undone. The image file will be deleted from disk.
    Only works for images that are already in trash.
    """
    logger.info(f"Permanent delete request for image {image_id} from user {current_user.username}")

    try:
        deleted = ImageService.permanent_delete(
            db=db,
            image_id=image_id,
            owner_id=current_user.id
        )

        if not deleted:
            logger.warning(f"Image {image_id} not found in trash for user {current_user.username}")
            raise exceptions.NotFoundException(f"Image with ID {image_id} not found in trash")

        logger.info(f"Image {image_id} permanently deleted")
        return schemas.DeleteResponse(
            message="Image permanently deleted",
            image_id=image_id
        )

    except exceptions.AppException:
        raise
    except ValueError as e:
        raise exceptions.ProcessingException(str(e))
    except Exception as e:
        logger.error(f"Failed to permanently delete image {image_id}: {str(e)}", exc_info=True)
        raise exceptions.ProcessingException(f"Failed to permanently delete: {str(e)}")


# =============================================================================
# Rename Endpoint
# =============================================================================

@router.put("/images/{image_id}/rename", response_model=schemas.ImageResponse)
async def rename_image(
    image_id: int,
    rename_data: schemas.ImageRename,
    current_user: models.User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Rename an image by setting its display name.

    The display name is shown in the UI instead of the auto-generated filename.
    """
    logger.info(f"Rename request for image {image_id} from user {current_user.username}")

    try:
        image = ImageService.rename_image(
            db=db,
            image_id=image_id,
            owner_id=current_user.id,
            display_name=rename_data.display_name
        )

        if not image:
            logger.warning(f"Image {image_id} not found for user {current_user.username}")
            raise exceptions.NotFoundException(f"Image with ID {image_id} not found")

        logger.info(f"Image {image_id} renamed to '{rename_data.display_name}'")
        return schemas.ImageResponse.model_validate(image)

    except exceptions.AppException:
        raise
    except ValueError as e:
        raise exceptions.ProcessingException(str(e))
    except Exception as e:
        logger.error(f"Failed to rename image {image_id}: {str(e)}", exc_info=True)
        raise exceptions.ProcessingException(f"Failed to rename image: {str(e)}")
