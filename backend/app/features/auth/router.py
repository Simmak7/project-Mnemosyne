"""
Auth Feature - API Router

FastAPI endpoints for authentication:
- POST /register - Create new user account
- POST /login - Get JWT access token
- GET /me - Get current user info
- POST /change-password - Change user password
- GET /password-requirements - Get password requirements
- POST /check-password-strength - Check password strength
"""

import logging
from datetime import timedelta

from fastapi import APIRouter, Depends, Request
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from core import config
from core.database import get_db
from core.auth import create_access_token, get_current_active_user
from core import exceptions
from core.password import validate_password, get_password_strength, get_password_requirements

from features.auth import schemas
from features.auth import service
from features.auth import security
from features.auth import sessions
from features.auth import two_factor
from features.auth.models import User

# Rate limiting
from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)
logger = logging.getLogger(__name__)

router = APIRouter(prefix="", tags=["Authentication"])


@router.post("/register", response_model=schemas.UserResponse)
@limiter.limit("5/hour")
async def register_user(
    request: Request,
    user: schemas.UserCreate,
    db: Session = Depends(get_db)
):
    """
    Register a new user account.

    Rate limited to 5 registrations per hour per IP address.

    Args:
        user: Registration data (username, email, password)

    Returns:
        Created user (without password)

    Raises:
        400: Username or email already registered
        500: Database error
    """
    logger.info(f"Registration attempt for username: {user.username}")

    try:
        # Check if username already exists
        db_user = service.get_user_by_username(db, username=user.username)
        if db_user:
            logger.warning(f"Registration failed: Username '{user.username}' already exists")
            raise exceptions.ValidationException("Username already registered")

        # Check if email already exists
        db_user = service.get_user_by_email(db, email=user.email)
        if db_user:
            logger.warning(f"Registration failed: Email '{user.email}' already exists")
            raise exceptions.ValidationException("Email already registered")

        # Create new user
        new_user = service.create_user(db=db, user=user)
        logger.info(f"User registered successfully: {new_user.username} (ID: {new_user.id})")
        return new_user

    except exceptions.AppException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error during registration: {str(e)}", exc_info=True)
        raise exceptions.DatabaseException("Failed to create user account")


@router.post("/login")
@limiter.limit("10/minute")
async def login(
    request: Request,
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
):
    """
    Login and get JWT access token.

    Rate limited to 10 attempts per minute per IP address.
    Uses OAuth2 password flow (form data with username/password).
    Implements account lockout after multiple failed attempts.

    If user has 2FA enabled, returns requires_2fa=true with a temp_token.
    User must then call /login/2fa with the temp_token and TOTP code.

    Args:
        form_data: OAuth2 form with username and password

    Returns:
        JWT access token

    Raises:
        401: Invalid credentials
        403: Account locked
    """
    logger.info(f"Login attempt for username: {form_data.username}")

    # Get client info for logging
    ip_address = request.client.host if request.client else None
    user_agent = request.headers.get("user-agent")

    try:
        # First, check if user exists
        user = service.get_user_by_username(db, form_data.username)

        if user:
            # Check if account is locked
            is_locked, locked_until = security.check_account_lockout(db, user)
            if is_locked:
                security.record_login_attempt(
                    db, user, form_data.username, ip_address, user_agent,
                    success=False, failure_reason="account_locked"
                )
                remaining = int((locked_until - __import__('datetime').datetime.now(
                    __import__('datetime').timezone.utc)).total_seconds() / 60)
                raise exceptions.AuthorizationException(
                    f"Account temporarily locked. Try again in {remaining} minutes."
                )

        # Authenticate
        authenticated_user = service.authenticate_user(
            db, form_data.username, form_data.password
        )

        if not authenticated_user:
            if user:
                # Track failed attempt and potentially lock account
                is_now_locked, locked_until = security.handle_failed_login(db, user)
                security.record_login_attempt(
                    db, user, form_data.username, ip_address, user_agent,
                    success=False, failure_reason="invalid_password"
                )
                if is_now_locked:
                    raise exceptions.AuthorizationException(
                        f"Account locked after too many failed attempts. "
                        f"Try again in {config.LOCKOUT_DURATION_MINUTES} minutes."
                    )
            else:
                security.record_login_attempt(
                    db, None, form_data.username, ip_address, user_agent,
                    success=False, failure_reason="user_not_found"
                )

            logger.warning(f"Failed login attempt for username: {form_data.username}")
            raise exceptions.AuthenticationException("Incorrect username or password")

        # Successful password verification - reset counters
        security.handle_successful_login(db, authenticated_user)
        security.record_login_attempt(
            db, authenticated_user, form_data.username, ip_address, user_agent,
            success=True
        )

        # Check if 2FA is enabled for this user
        tfa_status = two_factor.get_2fa_status(db, authenticated_user)
        if tfa_status.get("is_enabled"):
            # Return a temp token that requires 2FA verification
            temp_token = create_access_token(
                data={"sub": authenticated_user.username, "requires_2fa": True},
                expires_delta=timedelta(minutes=5)  # Short expiry for temp token
            )
            logger.info(f"2FA required for user: {authenticated_user.username}")
            return {"requires_2fa": True, "temp_token": temp_token}

        # No 2FA - issue full access token
        access_token_expires = timedelta(minutes=config.ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = create_access_token(
            data={"sub": authenticated_user.username},
            expires_delta=access_token_expires
        )

        # Create session record for session management
        sessions.create_session(
            db=db,
            user=authenticated_user,
            token=access_token,
            device_info=user_agent,
            ip_address=ip_address
        )

        logger.info(f"User logged in successfully: {authenticated_user.username}")
        return {"access_token": access_token, "token_type": "bearer"}

    except exceptions.AppException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error during login: {str(e)}", exc_info=True)
        raise exceptions.AuthenticationException("Login failed due to server error")


@router.post("/login/2fa", response_model=schemas.Token)
@limiter.limit("10/minute")
async def login_with_2fa(
    request: Request,
    data: schemas.Login2FARequest,
    db: Session = Depends(get_db)
):
    """
    Complete login with 2FA code.

    After initial login returns requires_2fa=true, call this endpoint
    with the temp_token and TOTP code to get the full access token.

    Args:
        data: temp_token and code

    Returns:
        JWT access token

    Raises:
        401: Invalid temp token or 2FA code
    """
    from jose import JWTError, jwt

    try:
        # Decode the temp token
        payload = jwt.decode(
            data.temp_token,
            config.SECRET_KEY,
            algorithms=[config.ALGORITHM]
        )
        username = payload.get("sub")
        requires_2fa = payload.get("requires_2fa")

        if not username or not requires_2fa:
            raise exceptions.AuthenticationException("Invalid temp token")

        # Get user
        user = service.get_user_by_username(db, username)
        if not user:
            raise exceptions.AuthenticationException("User not found")

        # Verify 2FA code
        success, error = two_factor.verify_2fa_code(db, user, data.code)
        if not success:
            raise exceptions.AuthenticationException(error or "Invalid 2FA code")

        # Get client info
        ip_address = request.client.host if request.client else None
        user_agent = request.headers.get("user-agent")

        # Issue full access token
        access_token_expires = timedelta(minutes=config.ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = create_access_token(
            data={"sub": user.username},
            expires_delta=access_token_expires
        )

        # Create session
        sessions.create_session(
            db=db,
            user=user,
            token=access_token,
            device_info=user_agent,
            ip_address=ip_address
        )

        logger.info(f"User completed 2FA login: {user.username}")
        return {"access_token": access_token, "token_type": "bearer"}

    except JWTError:
        raise exceptions.AuthenticationException("Invalid or expired temp token")
    except exceptions.AppException:
        raise
    except Exception as e:
        logger.error(f"2FA login error: {str(e)}", exc_info=True)
        raise exceptions.AuthenticationException("2FA verification failed")


@router.get("/me", response_model=schemas.UserResponse)
async def read_users_me(current_user: User = Depends(get_current_active_user)):
    """
    Get current authenticated user's information.

    Requires valid JWT token in Authorization header.

    Returns:
        Current user data (without password)
    """
    logger.debug(f"User info requested: {current_user.username}")
    return current_user


# ============================================
# Password Management Endpoints
# ============================================

@router.post("/change-password")
@limiter.limit("5/hour")
async def change_password(
    request: Request,
    password_data: schemas.PasswordChange,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Change the current user's password.

    Requires authentication and current password verification.
    Rate limited to 5 attempts per hour.

    Args:
        password_data: Current password and new password

    Returns:
        Success message

    Raises:
        400: Invalid password or validation failure
        401: Not authenticated
    """
    logger.info(f"Password change attempt for user: {current_user.username}")

    success, error = security.change_password(
        db=db,
        user=current_user,
        current_password=password_data.current_password,
        new_password=password_data.new_password
    )

    if not success:
        raise exceptions.ValidationException(error)

    return {"message": "Password changed successfully"}


@router.get("/password-requirements", response_model=schemas.PasswordRequirements)
async def get_password_requirements_endpoint():
    """
    Get the current password requirements.

    Returns:
        Password requirements configuration
    """
    return get_password_requirements()


@router.post("/check-password-strength", response_model=schemas.PasswordStrength)
async def check_password_strength(password_data: dict):
    """
    Check the strength of a password without storing it.

    Args:
        password_data: Dictionary with "password" key

    Returns:
        Password strength score and feedback
    """
    password = password_data.get("password", "")
    return get_password_strength(password)


@router.get("/account-lock-status", response_model=schemas.AccountLockStatus)
async def get_account_lock_status(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Get the current account lock status.

    Returns:
        Account lock status details
    """
    return security.get_account_lock_status(db, current_user)


# ============================================
# Password Reset Endpoints
# ============================================

from features.auth import password_reset


@router.post("/forgot-password")
@limiter.limit("3/hour")
async def forgot_password(
    request: Request,
    data: schemas.PasswordResetRequest,
    db: Session = Depends(get_db)
):
    """
    Request a password reset email.

    Rate limited to 3 requests per hour per IP.
    Always returns success to prevent email enumeration.

    Args:
        data: Email address for password reset

    Returns:
        Success message
    """
    logger.info(f"Password reset requested for email: {data.email}")

    success, message = await password_reset.request_password_reset(db, data.email)
    return {"message": message}


@router.get("/verify-reset-token/{token}")
async def verify_reset_token_endpoint(
    token: str,
    db: Session = Depends(get_db)
):
    """
    Verify a password reset token is valid.

    Args:
        token: Reset token from email

    Returns:
        Token validity and masked email
    """
    is_valid, user, error = password_reset.verify_reset_token(db, token)

    if not is_valid:
        return {
            "valid": False,
            "email": None,
            "error": error
        }

    return {
        "valid": True,
        "email": password_reset.get_masked_email(user.email),
        "error": None
    }


@router.post("/reset-password")
@limiter.limit("5/hour")
async def reset_password(
    request: Request,
    data: schemas.PasswordReset,
    db: Session = Depends(get_db)
):
    """
    Complete password reset with token.

    Rate limited to 5 attempts per hour per IP.

    Args:
        data: Reset token and new password

    Returns:
        Success message

    Raises:
        400: Invalid token or password validation failure
    """
    logger.info("Password reset attempt")

    success, error = password_reset.complete_password_reset(
        db=db,
        token=data.token,
        new_password=data.new_password
    )

    if not success:
        raise exceptions.ValidationException(error)

    return {"message": "Password reset successfully. You can now login with your new password."}


# ============================================
# Two-Factor Authentication Endpoints
# ============================================

from features.auth import two_factor


@router.post("/2fa/setup", response_model=schemas.TwoFactorSetupResponse)
async def setup_2fa_endpoint(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Initialize 2FA setup for the current user.

    Returns QR code and backup codes. User must verify with a code
    before 2FA is fully enabled.

    Returns:
        Secret, QR code (base64), and backup codes
    """
    if not two_factor.is_2fa_available():
        raise exceptions.ProcessingException(
            "2FA is not available. Required packages (pyotp, qrcode) not installed."
        )

    secret, qr_code, backup_codes = two_factor.setup_2fa(db, current_user)

    return {
        "secret": secret,
        "qr_code": qr_code,
        "backup_codes": backup_codes
    }


@router.post("/2fa/enable")
async def enable_2fa_endpoint(
    data: schemas.TwoFactorEnable,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Enable 2FA after setup.

    Requires a valid TOTP code to confirm setup was successful.

    Args:
        data: TOTP code for verification

    Returns:
        Success message
    """
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
    """
    Disable 2FA for the current user.

    Requires both a valid TOTP code and password for security.

    Args:
        data: TOTP code and password

    Returns:
        Success message
    """
    success, error = two_factor.disable_2fa(
        db, current_user, data.code, data.password
    )

    if not success:
        raise exceptions.ValidationException(error)

    return {"message": "Two-factor authentication disabled"}


@router.get("/2fa/status", response_model=schemas.TwoFactorStatus)
async def get_2fa_status(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Get 2FA status for the current user.

    Returns:
        2FA enabled status and backup codes availability
    """
    status = two_factor.get_2fa_status(db, current_user)
    return status


@router.post("/2fa/regenerate-backup-codes")
async def regenerate_backup_codes(
    password_data: dict,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Regenerate backup codes for 2FA.

    Requires password confirmation. Previous backup codes are invalidated.

    Args:
        password_data: Dictionary with "password" key

    Returns:
        New backup codes
    """
    password = password_data.get("password", "")

    success, codes, error = two_factor.regenerate_backup_codes(
        db, current_user, password
    )

    if not success:
        raise exceptions.ValidationException(error)

    return {"backup_codes": codes}
