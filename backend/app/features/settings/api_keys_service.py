"""
API Keys Service - Encrypted storage and validation for cloud AI keys.
"""

import logging
from datetime import datetime, timezone
from typing import Optional, List

from sqlalchemy.orm import Session

from core.encryption import encrypt_api_key, decrypt_api_key, make_key_hint
from core.llm.base import ProviderType

logger = logging.getLogger(__name__)


def save_api_key(
    db: Session,
    user_id: int,
    provider: str,
    api_key: str,
    base_url: str = None,
) -> dict:
    """Encrypt and save an API key for a user."""
    from models import UserAPIKey

    encrypted = encrypt_api_key(api_key)
    hint = make_key_hint(api_key)

    existing = db.query(UserAPIKey).filter(
        UserAPIKey.user_id == user_id,
        UserAPIKey.provider == provider,
    ).first()

    if existing:
        existing.encrypted_key = encrypted
        existing.key_hint = hint
        existing.base_url = base_url
        existing.is_valid = True
        existing.updated_at = datetime.now(timezone.utc)
    else:
        existing = UserAPIKey(
            user_id=user_id,
            provider=provider,
            encrypted_key=encrypted,
            key_hint=hint,
            base_url=base_url,
            is_valid=True,
        )
        db.add(existing)

    db.commit()
    db.refresh(existing)
    logger.info(f"Saved API key for user {user_id}, provider {provider}")
    return {"provider": provider, "key_hint": hint}


def get_api_key(db: Session, user_id: int, provider: str) -> Optional[str]:
    """Retrieve and decrypt an API key for a user."""
    from models import UserAPIKey

    record = db.query(UserAPIKey).filter(
        UserAPIKey.user_id == user_id,
        UserAPIKey.provider == provider,
    ).first()

    if not record:
        return None

    try:
        return decrypt_api_key(record.encrypted_key)
    except Exception as e:
        logger.error(f"Failed to decrypt API key for user {user_id}: {e}")
        return None


def get_api_key_with_url(
    db: Session, user_id: int, provider: str
) -> Optional[dict]:
    """Get decrypted API key and base_url for a provider."""
    from models import UserAPIKey

    record = db.query(UserAPIKey).filter(
        UserAPIKey.user_id == user_id,
        UserAPIKey.provider == provider,
    ).first()

    if not record:
        return None

    try:
        return {
            "api_key": decrypt_api_key(record.encrypted_key),
            "base_url": record.base_url,
        }
    except Exception:
        return None


def delete_api_key(db: Session, user_id: int, provider: str) -> bool:
    """Delete an API key for a user."""
    from models import UserAPIKey

    deleted = db.query(UserAPIKey).filter(
        UserAPIKey.user_id == user_id,
        UserAPIKey.provider == provider,
    ).delete()

    db.commit()
    logger.info(f"Deleted API key for user {user_id}, provider {provider}")
    return deleted > 0


def validate_api_key(
    provider: str, api_key: str, base_url: str = None
) -> dict:
    """Test an API key by making a minimal API call."""
    from core.llm.registry import register_cloud_provider

    provider_map = {
        "anthropic": ProviderType.ANTHROPIC,
        "openai": ProviderType.OPENAI,
        "custom": ProviderType.CUSTOM,
    }

    ptype = provider_map.get(provider)
    if not ptype:
        return {"valid": False, "message": f"Unknown provider: {provider}"}

    try:
        llm_provider = register_cloud_provider(ptype, api_key, base_url)
        health = llm_provider.health_check()

        if health.get("connected"):
            models = llm_provider.list_models()
            return {
                "valid": True,
                "message": "Connection successful",
                "models_available": len(models),
            }
        else:
            return {
                "valid": False,
                "message": health.get("error", "Connection failed"),
            }
    except Exception as e:
        return {"valid": False, "message": str(e)}


def get_user_api_keys_summary(db: Session, user_id: int) -> List[dict]:
    """Get summary of all API keys for a user (hints only)."""
    from models import UserAPIKey

    records = db.query(UserAPIKey).filter(
        UserAPIKey.user_id == user_id,
    ).all()

    return [
        {
            "provider": r.provider,
            "key_hint": r.key_hint,
            "is_valid": r.is_valid,
            "base_url": r.base_url,
            "last_validated_at": r.last_validated_at,
            "created_at": r.created_at,
        }
        for r in records
    ]


def mark_key_validated(
    db: Session, user_id: int, provider: str, is_valid: bool
) -> None:
    """Update key validation status."""
    from models import UserAPIKey

    record = db.query(UserAPIKey).filter(
        UserAPIKey.user_id == user_id,
        UserAPIKey.provider == provider,
    ).first()

    if record:
        record.is_valid = is_valid
        record.last_validated_at = datetime.now(timezone.utc)
        db.commit()
