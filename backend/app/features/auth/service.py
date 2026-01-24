"""
Auth Feature - Business Logic / Service Layer

CRUD operations and business logic for user authentication.
"""

import logging
from typing import Optional, Union
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from fastapi import HTTPException

from core.auth import get_password_hash, verify_password
from features.auth.models import User
from features.auth import schemas

logger = logging.getLogger(__name__)


def get_user(db: Session, user_id: int) -> Optional[User]:
    """
    Get a user by ID.

    Args:
        db: Database session
        user_id: User's primary key

    Returns:
        User object or None if not found
    """
    return db.query(User).filter(User.id == user_id).first()


def get_user_by_email(db: Session, email: str) -> Optional[User]:
    """
    Get a user by email address.

    Args:
        db: Database session
        email: User's email address

    Returns:
        User object or None if not found
    """
    return db.query(User).filter(User.email == email).first()


def get_user_by_username(db: Session, username: str) -> Optional[User]:
    """
    Get a user by username.

    Args:
        db: Database session
        username: User's username

    Returns:
        User object or None if not found
    """
    return db.query(User).filter(User.username == username).first()


def create_user(db: Session, user: schemas.UserCreate) -> User:
    """
    Create a new user account.

    Args:
        db: Database session
        user: User creation data (username, email, password)

    Returns:
        Created User object

    Raises:
        HTTPException: If username/email already exists or database error
    """
    hashed_password = get_password_hash(user.password)
    db_user = User(
        username=user.username,
        email=user.email,
        hashed_password=hashed_password
    )
    db.add(db_user)

    try:
        db.commit()
        db.refresh(db_user)
        logger.info(f"User created successfully: {user.username}")
        return db_user
    except IntegrityError as e:
        db.rollback()
        logger.error(f"Integrity error creating user {user.username}: {e}")
        raise HTTPException(
            status_code=409,
            detail="User with this username or email already exists"
        )
    except Exception as e:
        db.rollback()
        logger.exception(f"Unexpected error creating user {user.username}: {e}")
        raise HTTPException(status_code=500, detail="Failed to create user")


def authenticate_user(
    db: Session,
    username: str,
    password: str
) -> Union[User, bool]:
    """
    Authenticate a user by username and password.

    Args:
        db: Database session
        username: User's username
        password: Plain text password to verify

    Returns:
        User object if authentication successful, False otherwise
    """
    user = get_user_by_username(db, username)

    if not user:
        logger.debug(f"Authentication failed: User '{username}' not found")
        return False

    if not verify_password(password, user.hashed_password):
        logger.debug(f"Authentication failed: Invalid password for '{username}'")
        return False

    logger.info(f"User authenticated successfully: {username}")
    return user
