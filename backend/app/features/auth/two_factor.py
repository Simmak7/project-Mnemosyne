"""
Auth Feature - Two-Factor Authentication Service

Handles TOTP-based 2FA setup, verification, and backup codes.
"""

import logging
import secrets
import json
import base64
from io import BytesIO
from typing import List, Optional, Tuple
from datetime import datetime, timezone

from sqlalchemy.orm import Session

from core import config
from core.auth import get_password_hash, verify_password

try:
    import pyotp
    import qrcode
    TOTP_AVAILABLE = True
except ImportError:
    TOTP_AVAILABLE = False
    pyotp = None
    qrcode = None

import models

logger = logging.getLogger(__name__)


def is_2fa_available() -> bool:
    """Check if 2FA dependencies are installed."""
    return TOTP_AVAILABLE


def generate_totp_secret() -> str:
    """Generate a random TOTP secret."""
    if not TOTP_AVAILABLE:
        raise RuntimeError("pyotp not installed")
    return pyotp.random_base32()


def generate_backup_codes(count: int = 10) -> List[str]:
    """
    Generate backup codes for 2FA recovery.

    Args:
        count: Number of codes to generate

    Returns:
        List of backup codes (plain text, store hashed)
    """
    codes = []
    for _ in range(count):
        # Generate 8-character alphanumeric codes
        code = secrets.token_hex(4).upper()
        codes.append(code)
    return codes


def hash_backup_codes(codes: List[str]) -> str:
    """
    Hash backup codes for storage.

    Args:
        codes: List of plain text backup codes

    Returns:
        JSON string of hashed codes
    """
    hashed = [get_password_hash(code) for code in codes]
    return json.dumps(hashed)


def generate_qr_code(secret: str, username: str) -> str:
    """
    Generate a QR code for TOTP setup.

    Args:
        secret: TOTP secret
        username: User's username

    Returns:
        Base64-encoded PNG image
    """
    if not TOTP_AVAILABLE:
        raise RuntimeError("qrcode not installed")

    totp = pyotp.TOTP(secret)
    provisioning_uri = totp.provisioning_uri(
        name=username,
        issuer_name=config.TOTP_ISSUER_NAME
    )

    # Generate QR code
    qr = qrcode.QRCode(version=1, box_size=10, border=5)
    qr.add_data(provisioning_uri)
    qr.make(fit=True)

    img = qr.make_image(fill_color="black", back_color="white")

    # Convert to base64
    buffer = BytesIO()
    img.save(buffer, format="PNG")
    buffer.seek(0)
    img_base64 = base64.b64encode(buffer.getvalue()).decode()

    return f"data:image/png;base64,{img_base64}"


def verify_totp_code(secret: str, code: str) -> bool:
    """
    Verify a TOTP code.

    Args:
        secret: TOTP secret
        code: 6-digit code to verify

    Returns:
        True if code is valid
    """
    if not TOTP_AVAILABLE:
        return False

    totp = pyotp.TOTP(secret)
    return totp.verify(code)


def setup_2fa(db: Session, user: models.User) -> Tuple[str, str, List[str]]:
    """
    Initialize 2FA setup for a user.

    Args:
        db: Database session
        user: User object

    Returns:
        Tuple of (secret, qr_code_base64, backup_codes)
    """
    if not TOTP_AVAILABLE:
        raise RuntimeError("2FA dependencies not installed (pyotp, qrcode)")

    # Generate secret
    secret = generate_totp_secret()

    # Generate backup codes
    backup_codes = generate_backup_codes()

    # Check if user already has 2FA record
    existing = db.query(models.User2FA).filter(
        models.User2FA.user_id == user.id
    ).first()

    if existing:
        # Update existing record (not yet enabled)
        existing.secret_key = secret
        existing.backup_codes = hash_backup_codes(backup_codes)
        existing.is_enabled = False
        existing.updated_at = datetime.now(timezone.utc)
    else:
        # Create new record
        two_factor = models.User2FA(
            user_id=user.id,
            secret_key=secret,
            backup_codes=hash_backup_codes(backup_codes),
            is_enabled=False
        )
        db.add(two_factor)

    db.commit()

    # Generate QR code
    qr_code = generate_qr_code(secret, user.username)

    logger.info(f"2FA setup initiated for user: {user.username}")

    return secret, qr_code, backup_codes


def enable_2fa(db: Session, user: models.User, code: str) -> Tuple[bool, Optional[str]]:
    """
    Enable 2FA after user verifies with a code.

    Args:
        db: Database session
        user: User object
        code: TOTP code for verification

    Returns:
        Tuple of (success, error_message)
    """
    two_factor = db.query(models.User2FA).filter(
        models.User2FA.user_id == user.id
    ).first()

    if not two_factor:
        return False, "2FA not set up. Please initiate setup first."

    if two_factor.is_enabled:
        return False, "2FA is already enabled"

    # Verify the code
    if not verify_totp_code(two_factor.secret_key, code):
        return False, "Invalid verification code"

    # Enable 2FA
    two_factor.is_enabled = True
    two_factor.updated_at = datetime.now(timezone.utc)
    db.commit()

    logger.info(f"2FA enabled for user: {user.username}")

    return True, None


def disable_2fa(
    db: Session,
    user: models.User,
    code: str,
    password: str
) -> Tuple[bool, Optional[str]]:
    """
    Disable 2FA for a user.

    Args:
        db: Database session
        user: User object
        code: TOTP code for verification
        password: User's password for confirmation

    Returns:
        Tuple of (success, error_message)
    """
    # Verify password
    if not verify_password(password, user.hashed_password):
        return False, "Invalid password"

    two_factor = db.query(models.User2FA).filter(
        models.User2FA.user_id == user.id
    ).first()

    if not two_factor or not two_factor.is_enabled:
        return False, "2FA is not enabled"

    # Verify the code
    if not verify_totp_code(two_factor.secret_key, code):
        return False, "Invalid verification code"

    # Disable 2FA
    two_factor.is_enabled = False
    two_factor.updated_at = datetime.now(timezone.utc)
    db.commit()

    logger.info(f"2FA disabled for user: {user.username}")

    return True, None


def verify_2fa_code(
    db: Session,
    user: models.User,
    code: str
) -> Tuple[bool, Optional[str]]:
    """
    Verify a 2FA code during login.

    Args:
        db: Database session
        user: User object
        code: TOTP code or backup code

    Returns:
        Tuple of (success, error_message)
    """
    two_factor = db.query(models.User2FA).filter(
        models.User2FA.user_id == user.id,
        models.User2FA.is_enabled == True
    ).first()

    if not two_factor:
        return False, "2FA is not enabled"

    # First try TOTP code
    if verify_totp_code(two_factor.secret_key, code):
        return True, None

    # Try backup codes
    if two_factor.backup_codes:
        try:
            hashed_codes = json.loads(two_factor.backup_codes)
            for i, hashed_code in enumerate(hashed_codes):
                if verify_password(code.upper(), hashed_code):
                    # Remove used backup code
                    hashed_codes.pop(i)
                    two_factor.backup_codes = json.dumps(hashed_codes)
                    two_factor.updated_at = datetime.now(timezone.utc)
                    db.commit()
                    logger.info(f"Backup code used for user: {user.username}")
                    return True, None
        except json.JSONDecodeError:
            pass

    return False, "Invalid verification code"


def get_2fa_status(db: Session, user: models.User) -> dict:
    """
    Get 2FA status for a user.

    Args:
        db: Database session
        user: User object

    Returns:
        Dictionary with 2FA status
    """
    two_factor = db.query(models.User2FA).filter(
        models.User2FA.user_id == user.id
    ).first()

    if not two_factor:
        return {
            "is_enabled": False,
            "has_backup_codes": False
        }

    # Count remaining backup codes
    backup_count = 0
    if two_factor.backup_codes:
        try:
            hashed_codes = json.loads(two_factor.backup_codes)
            backup_count = len(hashed_codes)
        except json.JSONDecodeError:
            pass

    return {
        "is_enabled": two_factor.is_enabled,
        "has_backup_codes": backup_count > 0,
        "backup_codes_remaining": backup_count
    }


def regenerate_backup_codes(
    db: Session,
    user: models.User,
    password: str
) -> Tuple[bool, Optional[List[str]], Optional[str]]:
    """
    Regenerate backup codes for a user.

    Args:
        db: Database session
        user: User object
        password: User's password for confirmation

    Returns:
        Tuple of (success, new_codes, error_message)
    """
    # Verify password
    if not verify_password(password, user.hashed_password):
        return False, None, "Invalid password"

    two_factor = db.query(models.User2FA).filter(
        models.User2FA.user_id == user.id,
        models.User2FA.is_enabled == True
    ).first()

    if not two_factor:
        return False, None, "2FA is not enabled"

    # Generate new backup codes
    backup_codes = generate_backup_codes()
    two_factor.backup_codes = hash_backup_codes(backup_codes)
    two_factor.updated_at = datetime.now(timezone.utc)
    db.commit()

    logger.info(f"Backup codes regenerated for user: {user.username}")

    return True, backup_codes, None
