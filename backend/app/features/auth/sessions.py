"""
Auth Feature - Session Management Service (Phase 2)

Handles user session tracking, listing, and revocation.
"""

import logging
import hashlib
from datetime import datetime, timezone, timedelta
from typing import List, Optional, Tuple

from sqlalchemy.orm import Session

from core import config
import models

logger = logging.getLogger(__name__)


def hash_token(token: str) -> str:
    """Hash a JWT token for storage."""
    return hashlib.sha256(token.encode()).hexdigest()


def create_session(
    db: Session,
    user: models.User,
    token: str,
    device_info: Optional[str] = None,
    ip_address: Optional[str] = None
) -> models.UserSession:
    """
    Create a new session record when user logs in.

    Args:
        db: Database session
        user: User object
        token: JWT access token
        device_info: Device/browser info from user agent
        ip_address: Client IP address

    Returns:
        Created session object
    """
    token_hash = hash_token(token)
    expires_at = datetime.now(timezone.utc) + timedelta(
        minutes=config.ACCESS_TOKEN_EXPIRE_MINUTES
    )

    session = models.UserSession(
        user_id=user.id,
        token_hash=token_hash,
        device_info=device_info,
        ip_address=ip_address,
        expires_at=expires_at
    )

    db.add(session)
    db.commit()
    db.refresh(session)

    logger.info(f"Session created for user {user.username} from {ip_address}")
    return session


def get_user_sessions(
    db: Session,
    user: models.User,
    current_token: Optional[str] = None
) -> List[dict]:
    """
    Get all active sessions for a user.

    Args:
        db: Database session
        user: User object
        current_token: Current JWT token to mark as current session

    Returns:
        List of session info dictionaries
    """
    current_hash = hash_token(current_token) if current_token else None

    sessions = db.query(models.UserSession).filter(
        models.UserSession.user_id == user.id,
        models.UserSession.is_revoked == False,
        models.UserSession.expires_at > datetime.now(timezone.utc)
    ).order_by(models.UserSession.last_active.desc()).all()

    result = []
    for session in sessions:
        result.append({
            "id": session.id,
            "device_info": session.device_info,
            "ip_address": session.ip_address,
            "last_active": session.last_active,
            "created_at": session.created_at,
            "is_current": session.token_hash == current_hash if current_hash else False
        })

    return result


def revoke_session(
    db: Session,
    user: models.User,
    session_id: int
) -> Tuple[bool, Optional[str]]:
    """
    Revoke a specific session.

    Args:
        db: Database session
        user: User object
        session_id: ID of session to revoke

    Returns:
        Tuple of (success, error message)
    """
    session = db.query(models.UserSession).filter(
        models.UserSession.id == session_id,
        models.UserSession.user_id == user.id
    ).first()

    if not session:
        return False, "Session not found"

    if session.is_revoked:
        return False, "Session already revoked"

    session.is_revoked = True
    db.commit()

    logger.info(f"Session {session_id} revoked for user {user.username}")
    return True, None


def revoke_all_sessions(
    db: Session,
    user: models.User,
    except_token: Optional[str] = None
) -> int:
    """
    Revoke all sessions for a user, optionally keeping current one.

    Args:
        db: Database session
        user: User object
        except_token: Token to keep (current session)

    Returns:
        Number of sessions revoked
    """
    except_hash = hash_token(except_token) if except_token else None

    query = db.query(models.UserSession).filter(
        models.UserSession.user_id == user.id,
        models.UserSession.is_revoked == False
    )

    if except_hash:
        query = query.filter(models.UserSession.token_hash != except_hash)

    sessions = query.all()
    count = 0

    for session in sessions:
        session.is_revoked = True
        count += 1

    db.commit()

    logger.info(f"Revoked {count} sessions for user {user.username}")
    return count


def update_session_activity(
    db: Session,
    token: str
) -> None:
    """
    Update last_active timestamp for a session.

    Args:
        db: Database session
        token: JWT token
    """
    token_hash = hash_token(token)

    session = db.query(models.UserSession).filter(
        models.UserSession.token_hash == token_hash,
        models.UserSession.is_revoked == False
    ).first()

    if session:
        session.last_active = datetime.now(timezone.utc)
        db.commit()


def cleanup_expired_sessions(db: Session) -> int:
    """
    Clean up expired sessions from the database.

    Args:
        db: Database session

    Returns:
        Number of sessions deleted
    """
    result = db.query(models.UserSession).filter(
        models.UserSession.expires_at < datetime.now(timezone.utc)
    ).delete()

    db.commit()

    if result > 0:
        logger.info(f"Cleaned up {result} expired sessions")

    return result
