"""
API Keys Router - Endpoints for managing cloud AI provider keys.

POST   /settings/api-keys              - Save API key (encrypted)
GET    /settings/api-keys              - List keys (hints only)
DELETE /settings/api-keys/{provider}   - Remove key
POST   /settings/api-keys/{provider}/test - Validate key
"""

import logging

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from core.database import get_db
from core.auth import get_current_active_user
from core import exceptions
from features.auth.models import User
from features.settings import api_keys_service as service
from features.settings.api_keys_schemas import (
    APIKeyCreate,
    APIKeySummary,
    APIKeyTestResult,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api-keys", tags=["Cloud AI Keys"])


@router.post("", response_model=dict)
async def save_api_key(
    data: APIKeyCreate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """
    Save an encrypted API key for a cloud AI provider.

    The key is encrypted at rest and never returned in plaintext.
    Only a hint (first 3 + last 4 chars) is stored for display.
    """
    result = service.save_api_key(
        db=db,
        user_id=current_user.id,
        provider=data.provider,
        api_key=data.api_key,
        base_url=data.base_url,
    )
    logger.info(
        f"User {current_user.username} saved API key for {data.provider}"
    )
    return result


@router.get("", response_model=list[APIKeySummary])
async def list_api_keys(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """
    List saved API keys (hints only, never plaintext).

    Returns provider name, hint, validation status, and timestamps.
    """
    return service.get_user_api_keys_summary(db, current_user.id)


@router.delete("/{provider}")
async def delete_api_key(
    provider: str,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """Delete a saved API key for a provider."""
    deleted = service.delete_api_key(db, current_user.id, provider)
    if not deleted:
        raise exceptions.NotFoundException(
            f"No API key found for provider: {provider}"
        )
    return {"message": f"API key for {provider} deleted"}


@router.post("/{provider}/test", response_model=APIKeyTestResult)
async def test_api_key(
    provider: str,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """
    Test a saved API key by making a minimal API call.

    Verifies the key is valid and the provider is reachable.
    """
    api_key = service.get_api_key(db, current_user.id, provider)
    if not api_key:
        raise exceptions.NotFoundException(
            f"No API key found for provider: {provider}"
        )

    # Get base_url for custom providers
    key_info = service.get_api_key_with_url(db, current_user.id, provider)
    base_url = key_info.get("base_url") if key_info else None

    result = service.validate_api_key(provider, api_key, base_url)

    # Update validation status
    service.mark_key_validated(
        db, current_user.id, provider, result["valid"]
    )

    return APIKeyTestResult(
        provider=provider,
        valid=result["valid"],
        message=result["message"],
        models_available=result.get("models_available", 0),
    )
