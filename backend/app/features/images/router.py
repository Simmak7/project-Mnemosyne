"""
FastAPI router for Images feature.

Endpoints:
- POST /upload-image/ - Upload image and queue AI analysis
- POST /retry-image/{image_id} - Retry failed analysis
- DELETE /images/{image_id} - Delete image
- GET /images/ - List user's images
- GET /image/{image_id} - Get image file
- GET /task-status/{task_id} - Check analysis task status

Phase 4 - Favorites & Trash:
- POST /images/{id}/favorite - Toggle favorite status
- GET /images/favorites/ - Get favorited images
- POST /images/{id}/trash - Move to trash
- POST /images/{id}/restore - Restore from trash
- DELETE /images/{id}/permanent - Permanently delete from trash
- GET /images/trash/ - Get trashed images
"""

from fastapi import APIRouter, UploadFile, File, Form, Depends, HTTPException, status, Request, Query
from fastapi.responses import JSONResponse, FileResponse
from sqlalchemy.orm import Session
from typing import Annotated, Literal
import os
import uuid
import logging

from core.database import get_db
from core.auth import get_current_active_user, get_current_user_optional
from core import config, exceptions
import models

from features.images import schemas
from features.images.service import ImageService
from features.images.tasks import analyze_image_task

# Rate limiting
from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)
logger = logging.getLogger(__name__)

router = APIRouter(tags=["Image Processing"])


@router.post("/upload-image/", response_model=schemas.UploadResponse)
@limiter.limit("20/minute")
async def upload_image(
    request: Request,
    file: Annotated[UploadFile, File(description="Image file to upload")],
    prompt: Annotated[str | None, Form(description="Prompt for AI analysis")] = None,
    album_id: Annotated[int | None, Form(description="Album ID to add image to after analysis")] = None,
    current_user: models.User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Upload an image for AI analysis.

    The image is saved and AI analysis is queued as a background task.
    Returns immediately with a task_id for polling status.

    **File Requirements:**
    - Max size: 10MB
    - Allowed types: JPEG, PNG, GIF, WebP

    **Optional Parameters:**
    - album_id: Album to add the image to after analysis completes

    **Rate Limit:** 20 requests/minute
    """
    logger.info(f"Image upload request from user {current_user.username} (ID: {current_user.id})")

    # Validate file type
    if not file.content_type:
        logger.warning("Upload rejected: No content type provided")
        raise exceptions.ValidationException("File type could not be determined")

    try:
        # Read file contents
        contents = await file.read()

        # Validate file
        is_valid, error_msg = ImageService.validate_file(
            content_type=file.content_type,
            file_size=len(contents),
            filename=file.filename
        )

        if not is_valid:
            logger.warning(f"Upload rejected: {error_msg}")
            raise exceptions.ValidationException(error_msg)

        # Generate unique filename and save
        file_extension = os.path.splitext(file.filename)[1].lower()
        unique_filename = f"{uuid.uuid4()}{file_extension}"

        file_path = ImageService.save_file(contents, unique_filename)

        # Generate blur hash for instant loading placeholder (Phase 3)
        blur_hash, img_width, img_height = ImageService.generate_blur_hash(contents)
        if blur_hash:
            logger.debug(f"Generated blur hash for {unique_filename}: {blur_hash}")

        # Create image record in database
        image_data = ImageService.create_image(
            db=db,
            filename=unique_filename,
            filepath=file_path,
            prompt=prompt,
            owner_id=current_user.id,
            blur_hash=blur_hash,
            width=img_width,
            height=img_height
        )
        logger.info(f"Image saved: {unique_filename} (ID: {image_data.id}) for user {current_user.username}")

        # Queue AI analysis as background task
        task_id = None
        try:
            task = analyze_image_task.delay(
                image_id=image_data.id,
                image_path=file_path,
                prompt=prompt,
                album_id=album_id
            )
            logger.info(f"AI analysis task queued for image {image_data.id}, task_id: {task.id}, album_id: {album_id}")
            task_id = task.id
        except Exception as e:
            logger.error(f"Failed to queue AI analysis task for image {image_data.id}: {str(e)}", exc_info=True)
            # Mark as failed if we can't queue the task
            ImageService.update_analysis_status(
                db=db,
                image_id=image_data.id,
                status="failed",
                result="Failed to queue AI analysis task"
            )

        return schemas.UploadResponse(
            message="Image uploaded successfully. AI analysis queued.",
            filename=unique_filename,
            image_id=image_data.id,
            task_id=task_id,
            prompt=prompt,
            analysis_status="queued"
        )

    except exceptions.AppException:
        raise
    except OSError as e:
        logger.error(f"File system error during upload: {str(e)}", exc_info=True)
        raise exceptions.FileUploadException(f"Failed to save file: {str(e)}")
    except ValueError as e:
        logger.error(f"Validation error during upload: {str(e)}", exc_info=True)
        raise exceptions.ValidationException(str(e))
    except Exception as e:
        logger.error(f"Unexpected error during image upload: {str(e)}", exc_info=True)
        raise exceptions.FileUploadException(f"Failed to upload image: {str(e)}")


@router.post("/retry-image/{image_id}", response_model=schemas.RetryResponse)
@limiter.limit("10/minute")
async def retry_image_analysis(
    request: Request,
    image_id: int,
    current_user: models.User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Retry AI analysis for a failed image.

    Re-queues the AI analysis task for an image that previously failed.

    **Rate Limit:** 10 requests/minute
    """
    logger.info(f"Retry image analysis request for image {image_id} from user {current_user.username}")

    # Get the image and verify ownership
    image = ImageService.get_image_by_owner(db, image_id=image_id, owner_id=current_user.id)
    if not image:
        logger.warning(f"Image {image_id} not found for user {current_user.username}")
        raise exceptions.NotFoundException(f"Image with ID {image_id} not found")

    # Check if file still exists
    if not ImageService.file_exists(image.filepath):
        logger.error(f"Image file {image.filepath} not found on disk")
        raise exceptions.NotFoundException("Image file not found on disk")

    try:
        # Reset status to queued
        ImageService.update_analysis_status(
            db=db,
            image_id=image_id,
            status="queued",
            result=None
        )

        # Queue AI analysis task
        task = analyze_image_task.delay(
            image_id=image_id,
            image_path=image.filepath,
            prompt=image.prompt or "Analyze this image"
        )

        logger.info(f"Retry: AI analysis task queued for image {image_id}, task_id: {task.id}")

        return schemas.RetryResponse(
            message="Image analysis retry queued successfully",
            image_id=image_id,
            task_id=task.id,
            analysis_status="queued"
        )

    except Exception as e:
        logger.error(f"Failed to retry image analysis for image {image_id}: {str(e)}", exc_info=True)
        raise exceptions.ProcessingException(f"Failed to retry image analysis: {str(e)}")


@router.delete("/images/{image_id}", response_model=schemas.DeleteResponse)
@limiter.limit("20/minute")
async def delete_image(
    request: Request,
    image_id: int,
    current_user: models.User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Delete an image and its associated data.

    Deletes the image file from disk and removes the database record.

    **Rate Limit:** 20 requests/minute
    """
    logger.info(f"Delete image request for image {image_id} from user {current_user.username}")

    try:
        deleted = ImageService.delete_image(
            db=db,
            image_id=image_id,
            owner_id=current_user.id,
            delete_file=True
        )

        if not deleted:
            logger.warning(f"Image {image_id} not found for user {current_user.username}")
            raise exceptions.NotFoundException(f"Image with ID {image_id} not found")

        logger.info(f"Deleted image {image_id}")

        return schemas.DeleteResponse(
            message="Image deleted successfully",
            image_id=image_id
        )

    except exceptions.AppException:
        raise
    except ValueError as e:
        raise exceptions.ProcessingException(str(e))
    except Exception as e:
        logger.error(f"Failed to delete image {image_id}: {str(e)}", exc_info=True)
        raise exceptions.ProcessingException(f"Failed to delete image: {str(e)}")


@router.get("/task-status/{task_id}", response_model=schemas.TaskStatusResponse)
async def get_task_status(
    task_id: str,
    current_user: models.User = Depends(get_current_active_user)
):
    """
    Get the status of a background AI analysis task.

    **Task States:**
    - PENDING: Task is waiting in queue
    - STARTED: Task is currently processing
    - SUCCESS: Task completed successfully
    - FAILURE: Task failed
    - RETRY: Task is being retried
    """
    from celery.result import AsyncResult
    from core.celery_app import celery_app

    logger.info(f"Task status check for {task_id} by user {current_user.username}")

    try:
        task_result = AsyncResult(task_id, app=celery_app)

        response = schemas.TaskStatusResponse(
            task_id=task_id,
            status=task_result.state,
            ready=task_result.ready()
        )

        if task_result.state == "PENDING":
            response.message = "Task is waiting in queue"
        elif task_result.state == "STARTED":
            response.message = "Task is currently processing"
        elif task_result.state == "SUCCESS":
            response.message = "Task completed successfully"
            response.result = task_result.result
        elif task_result.state == "FAILURE":
            response.message = "Task failed"
            response.error = str(task_result.info)
        elif task_result.state == "RETRY":
            response.message = "Task is being retried"

        logger.info(f"Task {task_id} status: {task_result.state}, ready: {task_result.ready()}")
        return response

    except Exception as e:
        logger.error(f"Error checking task status for {task_id}: {str(e)}", exc_info=True)
        raise exceptions.AppException(f"Failed to check task status: {str(e)}")


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
    current_user: models.User | None = Depends(get_current_user_optional)
):
    """
    Get an image file by ID.

    Authentication is optional but recommended.
    Returns the actual image file for display.
    """
    user_info = f" by user {current_user.username}" if current_user else " (anonymous)"
    logger.debug(f"Image {image_id} requested{user_info}")

    try:
        image = ImageService.get_image(db, image_id=image_id)
        if not image:
            logger.warning(f"Image {image_id} not found")
            raise exceptions.ResourceNotFoundException("Image", image_id)

        # Check ownership if user is authenticated
        if current_user and image.owner_id != current_user.id:
            logger.warning(f"User {current_user.username} attempted to access image {image_id} owned by user {image.owner_id}")
            raise exceptions.AuthorizationException("Not authorized to access this image")

        if not ImageService.file_exists(image.filepath):
            logger.error(f"Image file not found on disk: {image.filepath}")
            raise exceptions.FileNotFoundException("Image file not found on disk")

        logger.debug(f"Serving image {image_id}{user_info}")
        return FileResponse(image.filepath)

    except exceptions.AppException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving image {image_id}: {str(e)}", exc_info=True)
        raise exceptions.DatabaseException("Failed to retrieve image")


# =============================================================================
# Phase 4: Favorites & Trash Endpoints
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
# Image Rename Endpoint
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


# =============================================================================
# Search Endpoints
# =============================================================================

@router.get("/images/search/", response_model=list[schemas.ImageResponse])
@limiter.limit("30/minute")
async def search_images(
    request: Request,
    q: str = Query(..., min_length=1, description="Search query"),
    search_type: Literal["text", "smart"] = Query("text", description="Search type: 'text' for full-text, 'smart' for AI semantic search"),
    limit: int = Query(50, ge=1, le=100, description="Maximum results to return"),
    current_user: models.User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Search images with full image data for gallery display.

    **Search Types:**
    - `text`: Full-text search on filename, description, and AI analysis
    - `smart`: AI-powered semantic search using embeddings (requires Ollama)

    Returns full image data including blur_hash, dimensions, tags, etc.
    for direct use in the gallery grid.

    **Rate Limit:** 30 requests/minute
    """
    logger.info(f"Image search: user={current_user.username}, query='{q}', type={search_type}")

    try:
        if search_type == "smart":
            images = ImageService.search_images_smart(
                db=db,
                owner_id=current_user.id,
                query=q,
                limit=limit
            )
        else:
            images = ImageService.search_images_text(
                db=db,
                owner_id=current_user.id,
                query=q,
                limit=limit
            )

        logger.info(f"Search returned {len(images)} images for query: {q}")
        return [schemas.ImageResponse.model_validate(img) for img in images]

    except Exception as e:
        logger.error(f"Image search failed: {str(e)}", exc_info=True)
        raise exceptions.ProcessingException(f"Search failed: {str(e)}")
