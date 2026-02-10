"""
Images Feature - CRUD Endpoints

Get images list, image metadata, and image file.
"""

from fastapi import APIRouter, Depends
from fastapi.responses import FileResponse
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


@router.get("/images/", response_model=list[schemas.ImageResponse])
async def get_images(
    skip: int = 0,
    limit: int = 100,
    current_user: models.User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Get all images for the current user.

    Returns images with their tags and associated notes.
    """
    logger.debug(f"Fetching images for user {current_user.username}, skip={skip}, limit={limit}")

    try:
        images = ImageService.get_images_by_user(
            db=db,
            owner_id=current_user.id,
            skip=skip,
            limit=limit
        )
        logger.info(f"Retrieved {len(images)} images for user {current_user.username}")
        return [schemas.ImageResponse.model_validate(img) for img in images]

    except Exception as e:
        logger.error(f"Error fetching images for user {current_user.username}: {str(e)}", exc_info=True)
        raise exceptions.DatabaseException("Failed to retrieve images")


@router.get("/images/{image_id}", response_model=schemas.ImageResponse)
async def get_image_metadata(
    image_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_active_user)
):
    """
    Get image metadata by ID (JSON response).

    Returns image details including filename, AI analysis, and tags.
    Use this for preview cards. For the actual image file, use /image/{id}.
    """
    try:
        image = ImageService.get_image(db, image_id=image_id)
        if not image:
            raise exceptions.ResourceNotFoundException("Image", image_id)

        if image.owner_id != current_user.id:
            raise exceptions.AuthorizationException("Not authorized to access this image")

        return schemas.ImageResponse.model_validate(image)

    except exceptions.AppException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving image {image_id}: {str(e)}", exc_info=True)
        raise exceptions.DatabaseException("Failed to retrieve image")


@router.get("/image/{image_id}")
async def get_image_file(
    image_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_active_user)
):
    """
    Get an image file by ID.

    **Authentication required.** Returns the actual image file for display.
    Only the owner of the image can access it.
    """
    logger.debug(f"Image {image_id} requested by user {current_user.username}")

    try:
        image = ImageService.get_image(db, image_id=image_id)
        if not image:
            logger.warning(f"Image {image_id} not found")
            raise exceptions.ResourceNotFoundException("Image", image_id)

        if image.owner_id != current_user.id:
            logger.warning(f"User {current_user.username} attempted to access image {image_id} owned by user {image.owner_id}")
            raise exceptions.AuthorizationException("Not authorized to access this image")

        if not ImageService.file_exists(image.filepath):
            logger.error(f"Image file not found on disk: {image.filepath}")
            raise exceptions.FileNotFoundException("Image file not found on disk")

        logger.debug(f"Serving image {image_id} to user {current_user.username}")
        return FileResponse(image.filepath)

    except exceptions.AppException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving image {image_id}: {str(e)}", exc_info=True)
        raise exceptions.DatabaseException("Failed to retrieve image")
