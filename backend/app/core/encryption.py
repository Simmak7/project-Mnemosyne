"""
Encryption utilities for sensitive data (API keys).

Uses Fernet symmetric encryption. Key derived from ENCRYPTION_KEY
env var, or falls back to SECRET_KEY.
"""

import base64
import hashlib
import logging
import os

from cryptography.fernet import Fernet

from core import config

logger = logging.getLogger(__name__)

_fernet_instance = None


def _get_fernet() -> Fernet:
    """Get or create the Fernet cipher instance."""
    global _fernet_instance
    if _fernet_instance is not None:
        return _fernet_instance

    raw_key = os.getenv("ENCRYPTION_KEY", "") or config.SECRET_KEY
    # Derive a 32-byte key via SHA-256, then base64-encode for Fernet
    key_bytes = hashlib.sha256(raw_key.encode("utf-8")).digest()
    fernet_key = base64.urlsafe_b64encode(key_bytes)
    _fernet_instance = Fernet(fernet_key)
    return _fernet_instance


def encrypt_api_key(plaintext: str) -> str:
    """Encrypt an API key string. Returns base64-encoded ciphertext."""
    fernet = _get_fernet()
    return fernet.encrypt(plaintext.encode("utf-8")).decode("utf-8")


def decrypt_api_key(ciphertext: str) -> str:
    """Decrypt an API key string. Returns plaintext."""
    fernet = _get_fernet()
    return fernet.decrypt(ciphertext.encode("utf-8")).decode("utf-8")


def make_key_hint(api_key: str) -> str:
    """Create a safe hint from an API key (e.g., 'sk-...abc1')."""
    if len(api_key) <= 8:
        return "****"
    return f"{api_key[:3]}...{api_key[-4:]}"
