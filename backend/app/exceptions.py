"""
DEPRECATED: This module is a backward compatibility shim.

All exceptions have moved to core.exceptions.
Import from core.exceptions directly in new code.
"""

# Re-export everything from core.exceptions for backward compatibility
from core.exceptions import (
    AppException,
    DatabaseException,
    OllamaServiceException,
    FileUploadException,
    FileNotFoundException,
    AuthenticationException,
    AuthorizationException,
    ValidationException,
    ResourceNotFoundException,
    AIAnalysisException,
    ProcessingException,
    NotFoundException,
)

__all__ = [
    "AppException",
    "DatabaseException",
    "OllamaServiceException",
    "FileUploadException",
    "FileNotFoundException",
    "AuthenticationException",
    "AuthorizationException",
    "ValidationException",
    "ResourceNotFoundException",
    "AIAnalysisException",
    "ProcessingException",
    "NotFoundException",
]
