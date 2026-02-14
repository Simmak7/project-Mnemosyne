"""
Settings Feature - Celery Tasks (Phase 4)

Background tasks for data export.
"""

import logging
import json
import os
import zipfile
import shutil
from datetime import datetime, timezone

from core.celery_app import celery_app
from core.database import SessionLocal
from core import config
import models

logger = logging.getLogger(__name__)

# Export directory
EXPORT_DIR = os.path.join(config.UPLOAD_DIR, "exports")


@celery_app.task(bind=True, name="generate_data_export")
def generate_data_export(self, job_id: str):
    """
    Generate data export ZIP file for a user.

    Args:
        job_id: Export job UUID
    """
    db = SessionLocal()

    try:
        # Get job
        job = db.query(models.DataExportJob).filter(
            models.DataExportJob.job_id == job_id
        ).first()

        if not job:
            logger.error(f"Export job not found: {job_id}")
            return

        # Update status to processing
        job.status = "processing"
        job.progress = 5
        db.commit()

        # Get user
        user = db.query(models.User).filter(models.User.id == job.user_id).first()
        if not user:
            _fail_job(db, job, "User not found")
            return

        # Create export directory
        os.makedirs(EXPORT_DIR, exist_ok=True)

        # Create temp directory for export
        temp_dir = os.path.join(EXPORT_DIR, f"temp_{job_id}")
        os.makedirs(temp_dir, exist_ok=True)

        try:
            # Export user profile
            job.progress = 10
            db.commit()
            _export_profile(db, user, temp_dir)

            # Export notes if requested
            if job.include_notes:
                job.progress = 30
                db.commit()
                _export_notes(db, user, temp_dir)

            # Export images if requested
            if job.include_images:
                job.progress = 50
                db.commit()
                _export_images(db, user, temp_dir)

            # Export tags if requested
            if job.include_tags:
                job.progress = 70
                db.commit()
                _export_tags(db, user, temp_dir)

            # Export activity if requested
            if job.include_activity:
                job.progress = 85
                db.commit()
                _export_activity(db, user, temp_dir)

            # Create ZIP file
            job.progress = 95
            db.commit()

            zip_filename = f"export_{job_id}.zip"
            zip_path = os.path.join(EXPORT_DIR, zip_filename)

            with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                for root, dirs, files in os.walk(temp_dir):
                    for file in files:
                        file_path = os.path.join(root, file)
                        arc_name = os.path.relpath(file_path, temp_dir)
                        zipf.write(file_path, arc_name)

            # Get file size
            file_size = os.path.getsize(zip_path)

            # Update job as completed
            job.status = "completed"
            job.progress = 100
            job.file_path = zip_path
            job.file_size = file_size
            job.completed_at = datetime.now(timezone.utc)
            from datetime import timedelta
            job.expires_at = datetime.now(timezone.utc) + timedelta(hours=24)
            db.commit()

            logger.info(f"Data export completed for user {user.username}: {zip_path}")

        finally:
            # Clean up temp directory
            if os.path.exists(temp_dir):
                shutil.rmtree(temp_dir)

    except Exception as e:
        logger.error(f"Data export failed for job {job_id}: {e}", exc_info=True)
        if job:
            _fail_job(db, job, str(e))

    finally:
        db.close()


def _fail_job(db, job: models.DataExportJob, error: str):
    """Mark job as failed."""
    job.status = "failed"
    job.error_message = error
    db.commit()


def _export_profile(db, user: models.User, temp_dir: str):
    """Export user profile data."""
    profile_data = {
        "id": user.id,
        "username": user.username,
        "email": user.email,
        "display_name": user.display_name,
        "created_at": user.created_at.isoformat() if user.created_at else None,
        "last_login": user.last_login.isoformat() if user.last_login else None,
    }

    profile_path = os.path.join(temp_dir, "profile.json")
    with open(profile_path, 'w', encoding='utf-8') as f:
        json.dump(profile_data, f, indent=2, ensure_ascii=False)

    logger.debug(f"Exported profile for user {user.username}")


def _export_notes(db, user: models.User, temp_dir: str):
    """Export user's notes."""
    notes_dir = os.path.join(temp_dir, "notes")
    os.makedirs(notes_dir, exist_ok=True)

    notes = db.query(models.Note).filter(models.Note.owner_id == user.id).all()

    notes_metadata = []
    for note in notes:
        # Save note content as markdown
        safe_title = "".join(c if c.isalnum() or c in " -_" else "_" for c in note.title)[:50]
        md_filename = f"{note.id}_{safe_title}.md"
        md_path = os.path.join(notes_dir, md_filename)

        with open(md_path, 'w', encoding='utf-8') as f:
            f.write(f"# {note.title}\n\n")
            f.write(note.content or "")

        # Collect metadata
        notes_metadata.append({
            "id": note.id,
            "title": note.title,
            "created_at": note.created_at.isoformat() if note.created_at else None,
            "updated_at": note.updated_at.isoformat() if note.updated_at else None,
            "file": md_filename,
            "tags": [tag.name for tag in note.tags] if note.tags else []
        })

    # Save metadata
    metadata_path = os.path.join(notes_dir, "_metadata.json")
    with open(metadata_path, 'w', encoding='utf-8') as f:
        json.dump(notes_metadata, f, indent=2, ensure_ascii=False)

    logger.debug(f"Exported {len(notes)} notes for user {user.username}")


def _export_images(db, user: models.User, temp_dir: str):
    """Export user's images."""
    images_dir = os.path.join(temp_dir, "images")
    os.makedirs(images_dir, exist_ok=True)

    images = db.query(models.Image).filter(models.Image.owner_id == user.id).all()

    images_metadata = []
    for image in images:
        # Copy image file if it exists
        if image.filepath and os.path.exists(image.filepath):
            filename = os.path.basename(image.filepath)
            dest_path = os.path.join(images_dir, filename)
            shutil.copy2(image.filepath, dest_path)
        else:
            filename = None

        # Collect metadata
        images_metadata.append({
            "id": image.id,
            "original_filename": image.filename,
            "display_name": image.display_name,
            "file": filename,
            "ai_analysis": image.ai_analysis_result,
            "uploaded_at": image.uploaded_at.isoformat() if image.uploaded_at else None,
            "tags": [tag.name for tag in image.tags] if image.tags else []
        })

    # Save metadata
    metadata_path = os.path.join(images_dir, "_metadata.json")
    with open(metadata_path, 'w', encoding='utf-8') as f:
        json.dump(images_metadata, f, indent=2, ensure_ascii=False)

    logger.debug(f"Exported {len(images)} images for user {user.username}")


def _export_tags(db, user: models.User, temp_dir: str):
    """Export user's tags."""
    tags = db.query(models.Tag).filter(models.Tag.owner_id == user.id).all()

    tags_data = []
    for tag in tags:
        tags_data.append({
            "id": tag.id,
            "name": tag.name,
            "created_at": tag.created_at.isoformat() if tag.created_at else None
        })

    tags_path = os.path.join(temp_dir, "tags.json")
    with open(tags_path, 'w', encoding='utf-8') as f:
        json.dump(tags_data, f, indent=2, ensure_ascii=False)

    logger.debug(f"Exported {len(tags)} tags for user {user.username}")


def _export_activity(db, user: models.User, temp_dir: str):
    """Export user's activity history."""
    # Get login attempts
    attempts = db.query(models.LoginAttempt).filter(
        models.LoginAttempt.user_id == user.id
    ).order_by(models.LoginAttempt.created_at.desc()).limit(1000).all()

    activity_data = []
    for attempt in attempts:
        activity_data.append({
            "type": "login",
            "ip_address": attempt.ip_address,
            "user_agent": attempt.user_agent,
            "success": attempt.success,
            "failure_reason": attempt.failure_reason,
            "created_at": attempt.created_at.isoformat() if attempt.created_at else None
        })

    activity_path = os.path.join(temp_dir, "activity.json")
    with open(activity_path, 'w', encoding='utf-8') as f:
        json.dump(activity_data, f, indent=2, ensure_ascii=False)

    logger.debug(f"Exported {len(activity_data)} activity records for user {user.username}")
