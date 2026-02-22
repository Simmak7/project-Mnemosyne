"""
Images Feature - Upload and Task Endpoints

Upload image, retry analysis, delete image, and task status.
"""

from fastapi import APIRouter, UploadFile, File, Form, Depends, Request
from sqlalchemy.orm import Session
import os
import uuid
import logging

from core.database import get_db
from core.auth import get_current_active_user
from core import exceptions
import models

from features.images import schemas
from features.images.service import ImageService
from features.images.tasks import analyze_image_task

from slowapi import Limiter
from slowapi.util import get_remote_address
from typing import Annotated

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
    auto_tagging: Annotated[bool, Form(description="Enable automatic tag extraction")] = True,
    max_tags: Annotated[int, Form(description="Maximum number of tags to extract")] = 10,
    auto_create_note: Annotated[bool, Form(description="Auto-create note from image analysis")] = True,
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

    if not file.content_type:
        logger.warning("Upload rejected: No content type provided")
        raise exceptions.ValidationException("File type could not be determined")

    try:
        contents = await file.read()

        is_valid, error_msg = ImageService.validate_file(
            content_type=file.content_type,
            file_size=len(contents),
            filename=file.filename
        )

        if not is_valid:
            logger.warning(f"Upload rejected: {error_msg}")
            raise exceptions.ValidationException(error_msg)

        file_extension = os.path.splitext(file.filename)[1].lower()
        unique_filename = f"{uuid.uuid4()}{file_extension}"

        file_path = ImageService.save_file(contents, unique_filename)

        blur_hash, img_width, img_height = ImageService.generate_blur_hash(contents)
        if blur_hash:
            logger.debug(f"Generated blur hash for {unique_filename}: {blur_hash}")

        image_data = ImageService.create_image(
            db=db,
            filename=unique_filename,
            filepath=file_path,
            prompt=prompt,
            owner_id=current_user.id,
            blur_hash=blur_hash,
            width=img_width,
            height=img_height,
            file_size=len(contents)
        )
        logger.info(f"Image saved: {unique_filename} (ID: {image_data.id}) for user {current_user.username}")

        # Resolve user's vision model preference
        user_vision_model = None
        try:
            prefs = db.query(models.UserPreferences).filter(
                models.UserPreferences.user_id == current_user.id
            ).first()
            if prefs and getattr(prefs, "vision_model", None):
                user_vision_model = prefs.vision_model
        except Exception:
            pass  # Fall back to default if preference lookup fails

        task_id = None
        try:
            task = analyze_image_task.delay(
                image_id=image_data.id,
                image_path=file_path,
                prompt=prompt,
                album_id=album_id,
                auto_tagging=auto_tagging,
                max_tags=max_tags,
                auto_create_note=auto_create_note,
                vision_model=user_vision_model,
            )
            logger.info(f"AI analysis task queued for image {image_data.id}, task_id: {task.id}, album_id: {album_id}")
            task_id = task.id
        except Exception as e:
            logger.error(f"Failed to queue AI analysis task for image {image_data.id}: {str(e)}", exc_info=True)
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

    image = ImageService.get_image_by_owner(db, image_id=image_id, owner_id=current_user.id)
    if not image:
        logger.warning(f"Image {image_id} not found for user {current_user.username}")
        raise exceptions.NotFoundException(f"Image with ID {image_id} not found")

    if not ImageService.file_exists(image.filepath):
        logger.error(f"Image file {image.filepath} not found on disk")
        raise exceptions.NotFoundException("Image file not found on disk")

    try:
        ImageService.update_analysis_status(
            db=db,
            image_id=image_id,
            status="queued",
            result=None
        )

        # Resolve user's vision model preference for retry
        retry_vision_model = None
        try:
            prefs = db.query(models.UserPreferences).filter(
                models.UserPreferences.user_id == current_user.id
            ).first()
            if prefs and getattr(prefs, "vision_model", None):
                retry_vision_model = prefs.vision_model
        except Exception:
            pass

        task = analyze_image_task.delay(
            image_id=image_id,
            image_path=image.filepath,
            prompt=image.prompt or "Analyze this image",
            vision_model=retry_vision_model,
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
