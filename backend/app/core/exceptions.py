"""
Custom exception classes for the application.

All exceptions inherit from AppException for consistent error handling.
"""

from fastapi import status


class AppException(Exception):
    """Base exception class for application errors."""

    def __init__(self, message: str, status_code: int = 500):
        self.message = message
        self.status_code = status_code
        super().__init__(self.message)


class DatabaseException(AppException):
    """Exception raised for database-related errors."""

    def __init__(self, message: str = "Database operation failed"):
        super().__init__(message, status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)


class OllamaServiceException(AppException):
    """Exception raised when Ollama AI service is unavailable or fails."""

    def __init__(self, message: str = "AI service unavailable"):
        super().__init__(message, status_code=status.HTTP_503_SERVICE_UNAVAILABLE)


class FileUploadException(AppException):
    """Exception raised for file upload errors."""

    def __init__(self, message: str = "File upload failed"):
        super().__init__(message, status_code=status.HTTP_400_BAD_REQUEST)


class FileNotFoundException(AppException):
    """Exception raised when a file is not found."""

    def __init__(self, message: str = "File not found"):
        super().__init__(message, status_code=status.HTTP_404_NOT_FOUND)


class AuthenticationException(AppException):
    """Exception raised for authentication errors."""

    def __init__(self, message: str = "Authentication failed"):
        super().__init__(message, status_code=status.HTTP_401_UNAUTHORIZED)


class AuthorizationException(AppException):
    """Exception raised for authorization errors."""

    def __init__(self, message: str = "Not authorized"):
        super().__init__(message, status_code=status.HTTP_403_FORBIDDEN)


class ValidationException(AppException):
    """Exception raised for validation errors."""

    def __init__(self, message: str = "Validation failed"):
        super().__init__(message, status_code=status.HTTP_400_BAD_REQUEST)


class ResourceNotFoundException(AppException):
    """Exception raised when a requested resource is not found."""

    def __init__(self, resource_type: str, resource_id: int):
        message = f"{resource_type} with id {resource_id} not found"
        super().__init__(message, status_code=status.HTTP_404_NOT_FOUND)


class AIAnalysisException(AppException):
    """Exception raised when AI analysis fails."""

    def __init__(self, message: str = "AI analysis failed"):
        super().__init__(message, status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)


class ProcessingException(AppException):
    """Exception raised when processing fails."""

    def __init__(self, message: str = "Processing failed"):
        super().__init__(message, status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)


class NotFoundException(AppException):
    """Exception raised when a resource is not found."""

    def __init__(self, message: str = "Resource not found"):
        super().__init__(message, status_code=status.HTTP_404_NOT_FOUND)
