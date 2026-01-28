"""
Authentication and authorization module.

Provides JWT token handling, password hashing, and user authentication dependencies.

Supports both:
1. Cookie-based auth (httpOnly cookie 'access_token') - preferred for browser clients
2. Header-based auth (Authorization: Bearer <token>) - for API clients

Cookie-based auth is more secure against XSS attacks as the token cannot be
accessed by JavaScript.
"""

from datetime import datetime, timedelta
from typing import Optional
from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi import Depends, HTTPException, status, Request
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from core.database import SessionLocal
from core import config
import models

# Cookie name for JWT token
AUTH_COOKIE_NAME = "access_token"

# Password hashing configuration
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# OAuth2 scheme for header-based auth (still supported for API clients)
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login", auto_error=False)

# Alias for backward compatibility (oauth2_scheme already has auto_error=False)
oauth2_scheme_optional = oauth2_scheme


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a plain password against a hashed password."""
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """Hash a password using bcrypt."""
    return pwd_context.hash(password)


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Create a JWT access token."""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, config.SECRET_KEY, algorithm=config.ALGORITHM)
    return encoded_jwt


def verify_token(token: str) -> Optional[str]:
    """Verify a JWT token and return the username."""
    try:
        payload = jwt.decode(token, config.SECRET_KEY, algorithms=[config.ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            return None
        # Check if this is a temp token requiring 2FA
        if payload.get("requires_2fa"):
            return None  # Don't accept temp tokens as full auth
        return username
    except JWTError:
        return None


def get_db():
    """Database dependency."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def extract_token_from_request(request: Request, header_token: Optional[str]) -> Optional[str]:
    """
    Extract JWT token from request, checking both cookie and header.

    Priority:
    1. Authorization header (Bearer token) - for API clients
    2. httpOnly cookie - for browser clients

    Args:
        request: The FastAPI request object
        header_token: Token from OAuth2 scheme (Authorization header)

    Returns:
        JWT token string or None
    """
    # First check Authorization header
    if header_token:
        return header_token

    # Then check cookie
    cookie_token = request.cookies.get(AUTH_COOKIE_NAME)
    if cookie_token:
        return cookie_token

    return None


async def get_current_user(
    request: Request,
    header_token: Optional[str] = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
) -> models.User:
    """
    Get the current authenticated user from JWT token.

    Checks both Authorization header and httpOnly cookie for the token.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    # Extract token from header or cookie
    token = extract_token_from_request(request, header_token)
    if not token:
        raise credentials_exception

    username = verify_token(token)
    if username is None:
        raise credentials_exception

    user = db.query(models.User).filter(models.User.username == username).first()
    if user is None:
        raise credentials_exception

    return user


async def get_current_active_user(
    current_user: models.User = Depends(get_current_user)
) -> models.User:
    """
    Get the current active user.

    Checks that the user account is active and not locked.
    """
    # Check if user is active
    if hasattr(current_user, 'is_active') and not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is deactivated"
        )

    # Check if user is locked
    if hasattr(current_user, 'is_locked') and current_user.is_locked:
        # Check if lock has expired
        if hasattr(current_user, 'locked_until') and current_user.locked_until:
            from datetime import timezone
            now = datetime.now(timezone.utc)
            if current_user.locked_until > now:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Account is temporarily locked"
                )

    # Check if account is scheduled for deletion
    if hasattr(current_user, 'deleted_at') and current_user.deleted_at:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is pending deletion"
        )

    return current_user


async def get_current_user_optional(
    request: Request,
    header_token: Optional[str] = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
) -> Optional[models.User]:
    """
    Get the current user if authenticated, None otherwise.

    Does not raise exceptions - useful for endpoints that work with
    or without authentication.
    """
    token = extract_token_from_request(request, header_token)
    if not token:
        return None

    try:
        username = verify_token(token)
        if username is None:
            return None

        user = db.query(models.User).filter(models.User.username == username).first()
        return user
    except Exception:
        return None


def set_auth_cookie(response, token: str, secure: bool = False) -> None:
    """
    Set the authentication cookie on a response.

    Args:
        response: FastAPI response object
        token: JWT token to set
        secure: Whether to set the Secure flag (True for HTTPS in production)
    """
    response.set_cookie(
        key=AUTH_COOKIE_NAME,
        value=token,
        httponly=True,  # Prevent JavaScript access
        samesite="lax",  # Prevent CSRF
        secure=secure,  # Only send over HTTPS in production
        max_age=config.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        path="/",
    )


def clear_auth_cookie(response) -> None:
    """
    Clear the authentication cookie on a response (for logout).

    Args:
        response: FastAPI response object
    """
    response.delete_cookie(
        key=AUTH_COOKIE_NAME,
        path="/",
    )
