"""
Settings Feature - API Router

FastAPI endpoints for user preferences:
- GET /settings/preferences - Get user preferences
- PATCH /settings/preferences - Update user preferences
- POST /settings/preferences/reset - Reset to defaults
- GET /settings/options - Get available options
"""

import logging

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from core.database import get_db
from core.auth import get_current_active_user
from core import exceptions

from features.settings import schemas
from features.settings import service
from features.auth.models import User

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/settings", tags=["Settings"])


@router.get("/preferences", response_model=schemas.UserPreferencesResponse)
async def get_preferences(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Get current user's preferences.

    Creates default preferences if none exist.

    Returns:
        User preferences
    """
    preferences = service.get_user_preferences(db, current_user)
    return preferences


@router.patch("/preferences", response_model=schemas.UserPreferencesResponse)
async def update_preferences(
    data: schemas.UserPreferencesUpdate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Update user preferences.

    Only provided fields will be updated.

    Args:
        data: Preference fields to update

    Returns:
        Updated preferences
    """
    preferences, error = service.update_user_preferences(
        db=db,
        user=current_user,
        theme=data.theme,
        accent_color=data.accent_color,
        ui_density=data.ui_density,
        font_size=data.font_size,
        sidebar_collapsed=data.sidebar_collapsed,
        default_view=data.default_view,
        rag_model=data.rag_model,
        brain_model=data.brain_model,
        nexus_model=data.nexus_model,
        cloud_ai_enabled=data.cloud_ai_enabled,
        cloud_ai_provider=data.cloud_ai_provider,
        cloud_rag_model=data.cloud_rag_model,
        cloud_brain_model=data.cloud_brain_model,
    )

    if error:
        raise exceptions.ProcessingException(error)

    return preferences


@router.post("/preferences/reset", response_model=schemas.UserPreferencesResponse)
async def reset_preferences(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Reset preferences to defaults.

    Returns:
        Reset preferences with default values
    """
    preferences = service.reset_user_preferences(db, current_user)
    return preferences


@router.get("/options", response_model=schemas.PreferencesOptions)
async def get_preference_options():
    """
    Get available options for preferences.

    Returns:
        Available themes, colors, densities, font sizes, and views
    """
    return schemas.PreferencesOptions()


@router.get("/accent-colors", response_model=schemas.AccentColorsResponse)
async def get_accent_colors():
    """
    Get accent colors with their hex values.

    Useful for frontend color rendering.

    Returns:
        List of accent colors with hex values
    """
    return schemas.AccentColorsResponse()


# ============================================
# Phase 4: Data Export Endpoints
# ============================================

from features.settings import data_export
from features.settings import activity
from features.settings.tasks import generate_data_export
from fastapi.responses import FileResponse
import os


@router.post("/export-data", response_model=schemas.DataExportResponse)
async def request_data_export(
    data: schemas.DataExportRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Request a data export (GDPR compliance).

    Starts a background job to generate a ZIP file with all user data.
    The export will be available for 24 hours.

    Args:
        data: Export options (what to include)

    Returns:
        Export job details
    """
    job = data_export.create_export_job(
        db=db,
        user=current_user,
        include_notes=data.include_notes,
        include_images=data.include_images,
        include_tags=data.include_tags,
        include_activity=data.include_activity
    )

    # Queue Celery task
    generate_data_export.delay(job.job_id)

    logger.info(f"Data export requested by user {current_user.username}: {job.job_id}")

    return {
        "job_id": job.job_id,
        "status": job.status,
        "message": "Export started. Check status with GET /settings/export-data/{job_id}",
        "created_at": job.created_at
    }


@router.get("/export-data/{job_id}", response_model=schemas.DataExportStatus)
async def get_export_status(
    job_id: str,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Get status of a data export job.

    Args:
        job_id: Export job UUID

    Returns:
        Export job status and download URL if completed
    """
    job = data_export.get_export_job(db, job_id, current_user.id)

    if not job:
        raise exceptions.NotFoundException("Export job not found")

    download_url = data_export.get_download_url(job)

    return {
        "job_id": job.job_id,
        "status": job.status,
        "progress": job.progress,
        "download_url": download_url,
        "expires_at": job.expires_at,
        "error_message": job.error_message,
        "created_at": job.created_at,
        "completed_at": job.completed_at
    }


@router.get("/export-data/{job_id}/download")
async def download_export(
    job_id: str,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Download a completed data export.

    Args:
        job_id: Export job UUID

    Returns:
        ZIP file download
    """
    job = data_export.get_export_job(db, job_id, current_user.id)

    if not job:
        raise exceptions.NotFoundException("Export job not found")

    if job.status != "completed":
        raise exceptions.ValidationException("Export not ready for download")

    if not job.file_path or not os.path.exists(job.file_path):
        raise exceptions.NotFoundException("Export file not found")

    from datetime import datetime, timezone
    if job.expires_at and job.expires_at < datetime.now(timezone.utc):
        raise exceptions.ValidationException("Export has expired")

    return FileResponse(
        path=job.file_path,
        filename=f"mnemosyne_export_{job.job_id[:8]}.zip",
        media_type="application/zip"
    )


# ============================================
# Phase 4: Activity History Endpoints
# ============================================

@router.get("/activity", response_model=schemas.ActivityHistoryResponse)
async def get_activity_history(
    page: int = 1,
    limit: int = 50,
    type: str = None,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Get user's activity history.

    Args:
        page: Page number (1-indexed)
        limit: Items per page (max 100)
        type: Filter by activity type (login_success, login_failed)

    Returns:
        Paginated activity history
    """
    if limit > 100:
        limit = 100

    activities, total = activity.get_activity_history(
        db=db,
        user=current_user,
        activity_type=type,
        page=page,
        limit=limit
    )

    return {
        "activities": activities,
        "total": total,
        "page": page,
        "limit": limit,
        "has_more": (page * limit) < total
    }


@router.get("/activity/stats", response_model=schemas.ActivityStatsResponse)
async def get_activity_stats(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Get activity statistics for the last 30 days.

    Returns:
        Activity statistics (logins, failed attempts, unique IPs)
    """
    stats = activity.get_activity_stats(db, current_user)
    return stats


# ============================================
# Phase 5: Notification Preferences Endpoints
# ============================================

from features.settings import notifications
from features.settings.api_keys_router import router as api_keys_router

# Include API keys sub-router
router.include_router(api_keys_router)


@router.get("/notifications", response_model=schemas.NotificationPreferencesResponse)
async def get_notification_preferences(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Get current user's notification preferences.

    Creates default preferences if none exist.

    Returns:
        Notification preferences
    """
    prefs = notifications.get_notification_preferences(db, current_user)
    return prefs


@router.patch("/notifications", response_model=schemas.NotificationPreferencesResponse)
async def update_notification_preferences(
    data: schemas.NotificationPreferencesUpdate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Update notification preferences.

    Only provided fields will be updated.

    Args:
        data: Notification preference fields to update

    Returns:
        Updated notification preferences
    """
    prefs, error = notifications.update_notification_preferences(
        db=db,
        user=current_user,
        email_security_alerts=data.email_security_alerts,
        email_weekly_digest=data.email_weekly_digest,
        email_product_updates=data.email_product_updates,
        push_enabled=data.push_enabled
    )

    if error:
        raise exceptions.ProcessingException(error)

    return prefs


@router.post("/notifications/reset", response_model=schemas.NotificationPreferencesResponse)
async def reset_notification_preferences(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Reset notification preferences to defaults.

    Returns:
        Reset notification preferences with default values
    """
    prefs = notifications.reset_notification_preferences(db, current_user)
    return prefs


@router.get("/notifications/options", response_model=schemas.NotificationOptions)
async def get_notification_options():
    """
    Get available notification options.

    Returns:
        Available notification types and their descriptions
    """
    return schemas.NotificationOptions()


# ============================================
# Cloud AI Usage Tracking
# ============================================

@router.get("/ai-usage")
async def get_ai_usage(
    days: int = 30,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """
    Get AI usage summary and daily breakdown.

    Args:
        days: Number of days to look back (default 30)

    Returns:
        Usage summary with cost estimates and daily breakdown
    """
    from core.llm.cost_tracker import get_usage_summary, get_daily_usage

    summary = get_usage_summary(db, current_user.id, days)
    daily = get_daily_usage(db, current_user.id, days)

    return {
        "summary": summary,
        "daily": daily,
    }
