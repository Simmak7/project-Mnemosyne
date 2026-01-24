"""
Settings Feature - Activity History Service (Phase 4)

Provides access to user activity/security history.
"""

import logging
from typing import Optional, List, Tuple

from sqlalchemy.orm import Session

import models

logger = logging.getLogger(__name__)


def get_activity_history(
    db: Session,
    user: models.User,
    activity_type: Optional[str] = None,
    page: int = 1,
    limit: int = 50
) -> Tuple[List[dict], int]:
    """
    Get user's activity history.

    Args:
        db: Database session
        user: User object
        activity_type: Filter by type (login, password_change, etc.)
        page: Page number (1-indexed)
        limit: Items per page

    Returns:
        Tuple of (activity list, total count)
    """
    # Build base query for login attempts
    query = db.query(models.LoginAttempt).filter(
        models.LoginAttempt.user_id == user.id
    )

    # Filter by type if specified
    if activity_type == "login_success":
        query = query.filter(models.LoginAttempt.success == True)
    elif activity_type == "login_failed":
        query = query.filter(models.LoginAttempt.success == False)

    # Get total count
    total = query.count()

    # Apply pagination
    offset = (page - 1) * limit
    attempts = query.order_by(
        models.LoginAttempt.created_at.desc()
    ).offset(offset).limit(limit).all()

    # Convert to activity items
    activities = []
    for attempt in attempts:
        activities.append({
            "id": attempt.id,
            "type": "login",
            "ip_address": attempt.ip_address,
            "user_agent": attempt.user_agent,
            "success": attempt.success,
            "failure_reason": attempt.failure_reason,
            "details": _get_login_details(attempt),
            "created_at": attempt.created_at
        })

    return activities, total


def _get_login_details(attempt: models.LoginAttempt) -> str:
    """Generate human-readable details for login attempt."""
    if attempt.success:
        return "Successful login"
    elif attempt.failure_reason == "invalid_password":
        return "Failed login: incorrect password"
    elif attempt.failure_reason == "user_not_found":
        return "Failed login: user not found"
    elif attempt.failure_reason == "account_locked":
        return "Failed login: account locked"
    else:
        return f"Failed login: {attempt.failure_reason or 'unknown reason'}"


def get_recent_security_events(
    db: Session,
    user: models.User,
    limit: int = 10
) -> List[dict]:
    """
    Get recent security-related events for dashboard display.

    Args:
        db: Database session
        user: User object
        limit: Max events to return

    Returns:
        List of security events
    """
    # Get recent failed login attempts
    failed_attempts = db.query(models.LoginAttempt).filter(
        models.LoginAttempt.user_id == user.id,
        models.LoginAttempt.success == False
    ).order_by(models.LoginAttempt.created_at.desc()).limit(limit).all()

    events = []
    for attempt in failed_attempts:
        events.append({
            "type": "failed_login",
            "ip_address": attempt.ip_address,
            "timestamp": attempt.created_at,
            "severity": "warning"
        })

    return events


def get_activity_stats(db: Session, user: models.User) -> dict:
    """
    Get activity statistics for the user.

    Args:
        db: Database session
        user: User object

    Returns:
        Activity statistics
    """
    from datetime import datetime, timezone, timedelta

    now = datetime.now(timezone.utc)
    thirty_days_ago = now - timedelta(days=30)

    # Total logins in last 30 days
    total_logins = db.query(models.LoginAttempt).filter(
        models.LoginAttempt.user_id == user.id,
        models.LoginAttempt.success == True,
        models.LoginAttempt.created_at >= thirty_days_ago
    ).count()

    # Failed attempts in last 30 days
    failed_attempts = db.query(models.LoginAttempt).filter(
        models.LoginAttempt.user_id == user.id,
        models.LoginAttempt.success == False,
        models.LoginAttempt.created_at >= thirty_days_ago
    ).count()

    # Unique IPs in last 30 days
    unique_ips = db.query(models.LoginAttempt.ip_address).filter(
        models.LoginAttempt.user_id == user.id,
        models.LoginAttempt.success == True,
        models.LoginAttempt.created_at >= thirty_days_ago
    ).distinct().count()

    return {
        "total_logins_30d": total_logins,
        "failed_attempts_30d": failed_attempts,
        "unique_ips_30d": unique_ips,
        "last_login": user.last_login
    }
