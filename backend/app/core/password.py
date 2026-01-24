"""
Password validation and strength checking utilities.

Provides password validation against configurable requirements.
"""

import re
from typing import List, Tuple
from core import config


def validate_password(password: str) -> Tuple[bool, List[str]]:
    """
    Validate password against configured requirements.

    Args:
        password: Plain text password to validate

    Returns:
        Tuple of (is_valid, list_of_errors)
    """
    errors = []

    # Length check
    if len(password) < config.PASSWORD_MIN_LENGTH:
        errors.append(f"Password must be at least {config.PASSWORD_MIN_LENGTH} characters")

    # Uppercase check
    if config.PASSWORD_REQUIRE_UPPERCASE and not re.search(r'[A-Z]', password):
        errors.append("Password must contain at least one uppercase letter")

    # Lowercase check
    if config.PASSWORD_REQUIRE_LOWERCASE and not re.search(r'[a-z]', password):
        errors.append("Password must contain at least one lowercase letter")

    # Digit check
    if config.PASSWORD_REQUIRE_DIGIT and not re.search(r'\d', password):
        errors.append("Password must contain at least one number")

    # Special character check
    if config.PASSWORD_REQUIRE_SPECIAL and not re.search(r'[!@#$%^&*()_+\-=\[\]{}|;:,.<>?]', password):
        errors.append("Password must contain at least one special character (!@#$%^&*()_+-=[]{}|;:,.<>?)")

    return len(errors) == 0, errors


def get_password_strength(password: str) -> dict:
    """
    Calculate password strength score and feedback.

    Args:
        password: Plain text password to check

    Returns:
        Dictionary with score (0-100), strength level, and feedback
    """
    score = 0
    feedback = []

    # Length scoring (max 30 points)
    length = len(password)
    if length >= 8:
        score += 10
    if length >= 12:
        score += 10
    if length >= 16:
        score += 10

    # Character variety scoring (max 40 points)
    if re.search(r'[a-z]', password):
        score += 10
    if re.search(r'[A-Z]', password):
        score += 10
    if re.search(r'\d', password):
        score += 10
    if re.search(r'[!@#$%^&*()_+\-=\[\]{}|;:,.<>?]', password):
        score += 10

    # Entropy bonus (max 30 points)
    unique_chars = len(set(password))
    if unique_chars >= 6:
        score += 10
    if unique_chars >= 10:
        score += 10
    if unique_chars >= 14:
        score += 10

    # Determine strength level
    if score < 30:
        strength = "weak"
        feedback.append("Consider using a longer password")
    elif score < 50:
        strength = "fair"
        feedback.append("Add more variety to strengthen your password")
    elif score < 70:
        strength = "good"
        feedback.append("Good password, but could be stronger")
    elif score < 90:
        strength = "strong"
    else:
        strength = "excellent"

    return {
        "score": min(score, 100),
        "strength": strength,
        "feedback": feedback
    }


def get_password_requirements() -> dict:
    """
    Get the current password requirements configuration.

    Returns:
        Dictionary describing password requirements
    """
    return {
        "min_length": config.PASSWORD_MIN_LENGTH,
        "require_uppercase": config.PASSWORD_REQUIRE_UPPERCASE,
        "require_lowercase": config.PASSWORD_REQUIRE_LOWERCASE,
        "require_digit": config.PASSWORD_REQUIRE_DIGIT,
        "require_special": config.PASSWORD_REQUIRE_SPECIAL,
        "special_characters": "!@#$%^&*()_+-=[]{}|;:,.<>?"
    }
