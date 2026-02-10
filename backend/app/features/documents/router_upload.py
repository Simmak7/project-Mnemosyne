"""
Documents Feature - Upload & Task Status Endpoints

POST /documents/upload/ - Upload PDF, save, create record, queue Celery task
GET /documents/task-status/{task_id} - Poll processing status
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

from features.documents import schemas
from features.documents.service import DocumentService, ALLOWED_DOCUMENT_TYPES

from slowapi import Limiter
from slowapi.util import get_remote_address
from typing import Annotated, Optional

limiter = Limiter(key_func=get_remote_address)
logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/documents/upload/", response_model=schemas.DocumentUploadResponse)
@limiter.limit("20/minute")
async def upload_document(
    request: Request,
    file: Annotated[UploadFile, File(description="PDF file to upload")],
    instructions: Optional[str] = Form(None),
    current_user: models.User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """
    Upload a PDF document for AI analysis.

    The document is saved and analysis is queued as a background task.
    Returns immediately with a task_id for polling status.

    **File Requirements:**
    - Max size: 50MB
    - Allowed types: PDF

    **Rate Limit:** 20 requests/minute
    """
    logger.info(f"Document upload from user {current_user.username} (ID: {current_user.id})")

    if not file.content_type:
        raise exceptions.ValidationException("File type could not be determined")

    try:
        contents = await file.read()

        is_valid, error_msg = DocumentService.validate_file(
            content_type=file.content_type,
            file_size=len(contents),
            filename=file.filename,
        )
        if not is_valid:
            raise exceptions.ValidationException(error_msg)

        # Generate unique filename
        ext = ALLOWED_DOCUMENT_TYPES.get(file.content_type, ".pdf")
        unique_filename = f"{uuid.uuid4()}{ext}"

        filepath = DocumentService.save_file(contents, unique_filename)

        doc = DocumentService.create_document(
            db=db,
            filename=unique_filename,
            filepath=filepath,
            owner_id=current_user.id,
            file_size=len(contents),
            display_name=file.filename,
        )

        # Queue Celery analysis task
        task_id = None
        try:
            from features.documents.tasks import analyze_document_task

            task = analyze_document_task.delay(
                document_id=doc.id,
                filepath=filepath,
                user_instructions=instructions,
            )
            task_id = task.id
            logger.info(f"Document analysis task queued: doc={doc.id}, task={task.id}")
        except Exception as e:
            logger.error(f"Failed to queue analysis for doc {doc.id}: {e}", exc_info=True)
            DocumentService.update_analysis_status(db, doc.id, "failed", str(e))

        return schemas.DocumentUploadResponse(
            message="Document uploaded. AI analysis queued.",
            document_id=doc.id,
            filename=unique_filename,
            task_id=task_id,
            analysis_status="queued",
        )

    except exceptions.AppException:
        raise
    except OSError as e:
        logger.error(f"File system error: {e}", exc_info=True)
        raise exceptions.FileUploadException(f"Failed to save file: {e}")
    except Exception as e:
        logger.error(f"Unexpected error during document upload: {e}", exc_info=True)
        raise exceptions.FileUploadException(f"Failed to upload document: {e}")


@router.get(
    "/documents/task-status/{task_id}",
    response_model=schemas.TaskStatusResponse,
)
async def get_document_task_status(
    task_id: str,
    current_user: models.User = Depends(get_current_active_user),
):
    """Get the status of a document analysis task."""
    from celery.result import AsyncResult
    from core.celery_app import celery_app

    try:
        task_result = AsyncResult(task_id, app=celery_app)

        response = schemas.TaskStatusResponse(
            task_id=task_id,
            status=task_result.state,
            ready=task_result.ready(),
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

        return response

    except Exception as e:
        logger.error(f"Error checking task {task_id}: {e}", exc_info=True)
        raise exceptions.AppException(f"Failed to check task status: {e}")
