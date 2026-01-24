"""
Settings Feature - Data Export Service (Phase 4)

Handles GDPR-compliant data export with background processing.
"""

import logging
import uuid
import json
import os
import zipfile
import shutil
from datetime import datetime, timezone, timedelta
from typing import Optional, Tuple

from sqlalchemy.orm import Session

from core import config
import models

logger = logging.getLogger(__name__)

# Export configuration
EXPORT_DIR = os.path.join(config.UPLOAD_DIR, "exports")
EXPORT_EXPIRY_HOURS = 24


def create_export_job(
    db: Session,
    user: models.User,
    include_notes: bool = True,
    include_images: bool = True,
    include_tags: bool = True,
    include_activity: bool = False
) -> models.DataExportJob:
    """
    Create a new data export job.

    Args:
        db: Database session
        user: User requesting export
        include_notes: Include notes in export
        include_images: Include images in export
        include_tags: Include tags in export
        include_activity: Include activity history in export

    Returns:
        Created DataExportJob object
    """
    job_id = str(uuid.uuid4())

    job = models.DataExportJob(
        job_id=job_id,
        user_id=user.id,
        status="pending",
        progress=0,
        include_notes=include_notes,
        include_images=include_images,
        include_tags=include_tags,
        include_activity=include_activity
    )

    db.add(job)
    db.commit()
    db.refresh(job)

    logger.info(f"Created data export job {job_id} for user {user.username}")
    return job


def get_export_job(db: Session, job_id: str, user_id: int) -> Optional[models.DataExportJob]:
    """
    Get an export job by ID.

    Args:
        db: Database session
        job_id: Job UUID
        user_id: User ID (for security check)

    Returns:
        DataExportJob or None
    """
    return db.query(models.DataExportJob).filter(
        models.DataExportJob.job_id == job_id,
        models.DataExportJob.user_id == user_id
    ).first()


def get_user_export_jobs(
    db: Session,
    user: models.User,
    limit: int = 10
) -> list[models.DataExportJob]:
    """
    Get recent export jobs for a user.

    Args:
        db: Database session
        user: User object
        limit: Max jobs to return

    Returns:
        List of DataExportJob objects
    """
    return db.query(models.DataExportJob).filter(
        models.DataExportJob.user_id == user.id
    ).order_by(models.DataExportJob.created_at.desc()).limit(limit).all()


def update_job_status(
    db: Session,
    job: models.DataExportJob,
    status: str,
    progress: int = None,
    error_message: str = None,
    file_path: str = None,
    file_size: int = None
) -> models.DataExportJob:
    """
    Update export job status.

    Args:
        db: Database session
        job: DataExportJob object
        status: New status
        progress: Progress percentage (0-100)
        error_message: Error message if failed
        file_path: Path to generated file
        file_size: Size of generated file

    Returns:
        Updated DataExportJob
    """
    job.status = status

    if progress is not None:
        job.progress = progress

    if error_message is not None:
        job.error_message = error_message

    if file_path is not None:
        job.file_path = file_path

    if file_size is not None:
        job.file_size = file_size

    if status == "completed":
        job.completed_at = datetime.now(timezone.utc)
        job.expires_at = datetime.now(timezone.utc) + timedelta(hours=EXPORT_EXPIRY_HOURS)

    db.commit()
    db.refresh(job)
    return job


def get_download_url(job: models.DataExportJob) -> Optional[str]:
    """
    Get download URL for a completed export.

    Args:
        job: DataExportJob object

    Returns:
        Download URL or None
    """
    if job.status != "completed" or not job.file_path:
        return None

    if job.expires_at and job.expires_at < datetime.now(timezone.utc):
        return None

    # Return relative URL for download endpoint
    return f"/settings/export-data/{job.job_id}/download"


def cleanup_expired_exports(db: Session) -> int:
    """
    Clean up expired export files and jobs.

    Args:
        db: Database session

    Returns:
        Number of exports cleaned up
    """
    now = datetime.now(timezone.utc)
    expired_jobs = db.query(models.DataExportJob).filter(
        models.DataExportJob.expires_at < now,
        models.DataExportJob.status == "completed"
    ).all()

    count = 0
    for job in expired_jobs:
        if job.file_path and os.path.exists(job.file_path):
            try:
                os.remove(job.file_path)
                logger.info(f"Deleted expired export file: {job.file_path}")
            except Exception as e:
                logger.error(f"Failed to delete export file {job.file_path}: {e}")

        job.status = "expired"
        job.file_path = None
        count += 1

    db.commit()

    if count > 0:
        logger.info(f"Cleaned up {count} expired export jobs")

    return count
