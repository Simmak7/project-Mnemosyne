"""
Password validation and strength checking utilities.

Provides password validation against configurable requirements,
including breach checking via haveibeenpwned API.
"""

import re
import hashlib
import logging
from typing import List, Tuple, Optional
import httpx

from core import config

logger = logging.getLogger(__name__)


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
        "special_characters": "!@#$%^&*()_+-=[]{}|;:,.<>?",
        "check_breach": getattr(config, 'PASSWORD_CHECK_BREACH', True),
    }


# =============================================================================
# Password Breach Checking (haveibeenpwned API)
# =============================================================================

HIBP_API_URL = "https://api.pwnedpasswords.com/range/"
HIBP_TIMEOUT = 5.0  # seconds


async def check_password_breach(password: str) -> Tuple[bool, Optional[int]]:
    """
    Check if a password has been exposed in known data breaches.

    Uses the haveibeenpwned API with k-Anonymity model:
    - Only the first 5 characters of the SHA-1 hash are sent
    - The full password is never transmitted
    - Privacy-preserving design

    Args:
        password: Plain text password to check

    Returns:
        Tuple of (is_breached, breach_count)
        - is_breached: True if password found in breaches
        - breach_count: Number of times seen in breaches (None if not found or error)
    """
    # Check if breach checking is enabled
    if not getattr(config, 'PASSWORD_CHECK_BREACH', True):
        return False, None

    try:
        # Hash the password with SHA-1 (required by HIBP API)
        sha1_hash = hashlib.sha1(password.encode('utf-8')).hexdigest().upper()

        # Split into prefix (first 5 chars) and suffix (rest)
        prefix = sha1_hash[:5]
        suffix = sha1_hash[5:]

        # Query the HIBP API with just the prefix (k-Anonymity)
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{HIBP_API_URL}{prefix}",
                timeout=HIBP_TIMEOUT,
                headers={
                    "User-Agent": "Mnemosyne-PasswordChecker",
                    "Add-Padding": "true",  # Request padding for extra privacy
                }
            )

            if response.status_code != 200:
                logger.warning(f"HIBP API returned status {response.status_code}")
                return False, None

            # Parse the response - format is "SUFFIX:COUNT\r\n"
            for line in response.text.splitlines():
                if ":" not in line:
                    continue
                hash_suffix, count = line.split(":")
                if hash_suffix.strip() == suffix:
                    breach_count = int(count.strip())
                    logger.info(f"Password found in {breach_count} breaches")
                    return True, breach_count

            # Password not found in breaches
            return False, None

    except httpx.TimeoutException:
        logger.warning("HIBP API timeout - skipping breach check")
        return False, None
    except httpx.RequestError as e:
        logger.warning(f"HIBP API request error: {e}")
        return False, None
    except Exception as e:
        logger.error(f"Error checking password breach: {e}")
        return False, None


def check_password_breach_sync(password: str) -> Tuple[bool, Optional[int]]:
    """
    Synchronous version of password breach check.

    Uses the haveibeenpwned API with k-Anonymity model.

    Args:
        password: Plain text password to check

    Returns:
        Tuple of (is_breached, breach_count)
    """
    # Check if breach checking is enabled
    if not getattr(config, 'PASSWORD_CHECK_BREACH', True):
        return False, None

    try:
        # Hash the password with SHA-1
        sha1_hash = hashlib.sha1(password.encode('utf-8')).hexdigest().upper()
        prefix = sha1_hash[:5]
        suffix = sha1_hash[5:]

        # Query the HIBP API
        with httpx.Client() as client:
            response = client.get(
                f"{HIBP_API_URL}{prefix}",
                timeout=HIBP_TIMEOUT,
                headers={
                    "User-Agent": "Mnemosyne-PasswordChecker",
                    "Add-Padding": "true",
                }
            )

            if response.status_code != 200:
                return False, None

            for line in response.text.splitlines():
                if ":" not in line:
                    continue
                hash_suffix, count = line.split(":")
                if hash_suffix.strip() == suffix:
                    return True, int(count.strip())

            return False, None

    except Exception as e:
        logger.warning(f"Breach check failed: {e}")
        return False, None


async def validate_password_with_breach_check(password: str) -> Tuple[bool, List[str]]:
    """
    Validate password against requirements AND check for breaches.

    This is the recommended validation function for registration and
    password change flows.

    Args:
        password: Plain text password to validate

    Returns:
        Tuple of (is_valid, list_of_errors)
    """
    # First, validate against regular requirements
    is_valid, errors = validate_password(password)

    # Then check for breaches (if enabled and basic validation passed)
    if is_valid and getattr(config, 'PASSWORD_CHECK_BREACH', True):
        is_breached, breach_count = await check_password_breach(password)
        if is_breached:
            if breach_count and breach_count > 1000:
                errors.append(
                    f"This password has been exposed in data breaches ({breach_count:,} times). "
                    "Please choose a different password."
                )
            else:
                errors.append(
                    "This password has been found in known data breaches. "
                    "Please choose a different password for your security."
                )
            is_valid = False

    return is_valid, errors
