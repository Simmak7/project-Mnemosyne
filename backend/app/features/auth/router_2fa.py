"""
Auth Feature - Two-Factor Authentication Endpoints

TOTP-based 2FA setup, enable, disable, and backup codes.
"""

import logging
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from core.database import get_db
from core.auth import get_current_active_user
from core import exceptions

from features.auth import schemas
from features.auth import two_factor
from features.auth.models import User

logger = logging.getLogger(__name__)

router = APIRouter(prefix="", tags=["Authentication"])


@router.post("/2fa/setup", response_model=schemas.TwoFactorSetupResponse)
async def setup_2fa_endpoint(current_user: User = Depends(get_current_active_user), db: Session = Depends(get_db)):
    """Initialize 2FA setup. Returns QR code and backup codes."""
    if not two_factor.is_2fa_available():
        raise exceptions.ProcessingException(
            "2FA is not available. Required packages (pyotp, qrcode) not installed."
        )

    secret, qr_code, backup_codes = two_factor.setup_2fa(db, current_user)

    return {"secret": secret, "qr_code": qr_code, "backup_codes": backup_codes}


@router.post("/2fa/enable")
async def enable_2fa_endpoint(
    data: schemas.TwoFactorEnable,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Enable 2FA after setup. Requires a valid TOTP code."""
    success, error = two_factor.enable_2fa(db, current_user, data.code)

    if not success:
        raise exceptions.ValidationException(error)

    return {"message": "Two-factor authentication enabled successfully"}


@router.post("/2fa/disable")
async def disable_2fa_endpoint(
    data: schemas.TwoFactorDisable,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Disable 2FA. Requires both TOTP code and password."""
    success, error = two_factor.disable_2fa(db, current_user, data.code, data.password)

    if not success:
        raise exceptions.ValidationException(error)

    return {"message": "Two-factor authentication disabled"}


@router.get("/2fa/status", response_model=schemas.TwoFactorStatus)
async def get_2fa_status(current_user: User = Depends(get_current_active_user), db: Session = Depends(get_db)):
    """Get 2FA status for the current user."""
    return two_factor.get_2fa_status(db, current_user)


@router.post("/2fa/regenerate-backup-codes")
async def regenerate_backup_codes(
    password_data: dict,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Regenerate backup codes. Requires password confirmation."""
    password = password_data.get("password", "")

    success, codes, error = two_factor.regenerate_backup_codes(db, current_user, password)

    if not success:
        raise exceptions.ValidationException(error)

    return {"backup_codes": codes}
