"""
Auth Feature - Core Authentication Endpoints

Register, login, logout, token refresh, and user info.
"""

import logging
from datetime import timedelta

from fastapi import APIRouter, Depends, Request, Response
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from core import config
from core.database import get_db
from core.auth import (
    create_access_token,
    create_refresh_token,
    get_current_active_user,
    set_auth_cookie,
    set_refresh_cookie,
    clear_auth_cookie,
    clear_refresh_cookie,
    verify_token,
    REFRESH_COOKIE_NAME,
)
from core import exceptions
from core.password import validate_password_with_breach_check

from features.auth import schemas
from features.auth import service
from features.auth import security
from features.auth import sessions
from features.auth import two_factor
from features.auth.models import User

from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)
logger = logging.getLogger(__name__)

router = APIRouter(prefix="", tags=["Authentication"])


@router.post("/register", response_model=schemas.UserResponse)
@limiter.limit("5/hour")
async def register_user(request: Request, user: schemas.UserCreate, db: Session = Depends(get_db)):
    """Register a new user account. Rate limited to 5/hour."""
    logger.info(f"Registration attempt for username: {user.username}")

    try:
        db_user = service.get_user_by_username(db, username=user.username)
        if db_user:
            raise exceptions.ValidationException("Username already registered")

        db_user = service.get_user_by_email(db, email=user.email)
        if db_user:
            raise exceptions.ValidationException("Email already registered")

        is_valid, errors = await validate_password_with_breach_check(user.password)
        if not is_valid:
            raise exceptions.ValidationException(errors[0] if errors else "Password validation failed")

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
    response: Response,
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
):
    """Login and get JWT access token. Implements account lockout."""
    logger.info(f"Login attempt for username: {form_data.username}")

    ip_address = request.client.host if request.client else None
    user_agent = request.headers.get("user-agent")

    try:
        user = service.get_user_by_username(db, form_data.username)

        if user:
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

        authenticated_user = service.authenticate_user(db, form_data.username, form_data.password)

        if not authenticated_user:
            if user:
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
            raise exceptions.AuthenticationException("Incorrect username or password")

        security.handle_successful_login(db, authenticated_user)
        security.record_login_attempt(db, authenticated_user, form_data.username, ip_address, user_agent, success=True)

        tfa_status = two_factor.get_2fa_status(db, authenticated_user)
        if tfa_status.get("is_enabled"):
            temp_token = create_access_token(
                data={"sub": authenticated_user.username, "requires_2fa": True},
                expires_delta=timedelta(minutes=5)
            )
            return {"requires_2fa": True, "temp_token": temp_token}

        access_token_expires = timedelta(minutes=config.ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = create_access_token(data={"sub": authenticated_user.username}, expires_delta=access_token_expires)
        refresh_token = create_refresh_token(data={"sub": authenticated_user.username})

        sessions.create_session(db=db, user=authenticated_user, token=access_token, device_info=user_agent, ip_address=ip_address)

        secure_cookie = config.ENVIRONMENT == "production"
        set_auth_cookie(response, access_token, secure=secure_cookie)
        set_refresh_cookie(response, refresh_token, secure=secure_cookie)

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
    response: Response,
    data: schemas.Login2FARequest,
    db: Session = Depends(get_db)
):
    """Complete login with 2FA code."""
    from jose import JWTError, jwt

    try:
        payload = jwt.decode(data.temp_token, config.SECRET_KEY, algorithms=[config.ALGORITHM])
        username = payload.get("sub")
        requires_2fa = payload.get("requires_2fa")

        if not username or not requires_2fa:
            raise exceptions.AuthenticationException("Invalid temp token")

        user = service.get_user_by_username(db, username)
        if not user:
            raise exceptions.AuthenticationException("User not found")

        success, error = two_factor.verify_2fa_code(db, user, data.code)
        if not success:
            raise exceptions.AuthenticationException(error or "Invalid 2FA code")

        ip_address = request.client.host if request.client else None
        user_agent = request.headers.get("user-agent")

        access_token_expires = timedelta(minutes=config.ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = create_access_token(data={"sub": user.username}, expires_delta=access_token_expires)
        refresh_token = create_refresh_token(data={"sub": user.username})

        sessions.create_session(db=db, user=user, token=access_token, device_info=user_agent, ip_address=ip_address)

        secure_cookie = config.ENVIRONMENT == "production"
        set_auth_cookie(response, access_token, secure=secure_cookie)
        set_refresh_cookie(response, refresh_token, secure=secure_cookie)

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
    """Get current authenticated user's information."""
    return current_user


@router.post("/logout")
async def logout(response: Response, current_user: User = Depends(get_current_active_user), db: Session = Depends(get_db)):
    """Logout the current user."""
    logger.info(f"User logout: {current_user.username}")
    clear_auth_cookie(response)
    clear_refresh_cookie(response)
    return {"message": "Logged out successfully"}


@router.post("/auth/refresh")
async def refresh_token(request: Request, response: Response, db: Session = Depends(get_db)):
    """Refresh the access token using a refresh token cookie."""
    refresh_token_value = request.cookies.get(REFRESH_COOKIE_NAME)
    if not refresh_token_value:
        raise exceptions.AuthenticationException("Refresh token missing")

    username = verify_token(refresh_token_value, expected_type="refresh")
    if not username:
        clear_refresh_cookie(response)
        raise exceptions.AuthenticationException("Invalid or expired refresh token")

    user = service.get_user_by_username(db, username)
    if not user:
        clear_refresh_cookie(response)
        raise exceptions.AuthenticationException("User not found")

    if hasattr(user, 'is_active') and not user.is_active:
        clear_refresh_cookie(response)
        raise exceptions.AuthorizationException("Account is deactivated")

    if hasattr(user, 'deleted_at') and user.deleted_at:
        clear_refresh_cookie(response)
        raise exceptions.AuthorizationException("Account is pending deletion")

    ip_address = request.client.host if request.client else None
    user_agent = request.headers.get("user-agent")

    access_token_expires = timedelta(minutes=config.ACCESS_TOKEN_EXPIRE_MINUTES)
    new_access_token = create_access_token(data={"sub": user.username}, expires_delta=access_token_expires)
    new_refresh_token = create_refresh_token(data={"sub": user.username})

    sessions.create_session(db=db, user=user, token=new_access_token, device_info=user_agent, ip_address=ip_address)

    secure_cookie = config.ENVIRONMENT == "production"
    set_auth_cookie(response, new_access_token, secure=secure_cookie)
    set_refresh_cookie(response, new_refresh_token, secure=secure_cookie)

    logger.info(f"Token refreshed for user: {user.username}")
    return {"access_token": new_access_token, "token_type": "bearer"}
