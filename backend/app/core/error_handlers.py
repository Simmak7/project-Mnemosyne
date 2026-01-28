"""
FastAPI exception handlers for consistent error responses.

Registers handlers for custom exceptions, validation errors, and database errors.

In production, error messages are sanitized to prevent information leakage.
Detailed errors are always logged server-side for debugging.
"""

from fastapi import Request, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from sqlalchemy.exc import SQLAlchemyError
import logging

from core import config
from core.exceptions import (
    AppException,
    DatabaseException,
    OllamaServiceException,
    AuthenticationException,
    AuthorizationException,
    ValidationException,
)

logger = logging.getLogger(__name__)

# Check if we're in production mode
IS_PRODUCTION = config.ENVIRONMENT == "production"

# Generic error messages for production (prevent information leakage)
GENERIC_MESSAGES = {
    400: "Invalid request. Please check your input and try again.",
    401: "Authentication required. Please log in.",
    403: "You don't have permission to perform this action.",
    404: "The requested resource was not found.",
    422: "Invalid input data. Please check and try again.",
    429: "Too many requests. Please slow down.",
    500: "An unexpected error occurred. Please try again later.",
    503: "Service temporarily unavailable. Please try again later.",
}


def get_safe_message(exc: AppException) -> str:
    """
    Get a safe error message for the response.

    In production, returns generic messages to prevent information leakage.
    In development, returns the actual error message for debugging.
    """
    if not IS_PRODUCTION:
        return exc.message

    # In production, use generic messages for server errors (5xx)
    # but allow specific messages for client errors (4xx) that don't leak info
    if exc.status_code >= 500:
        return GENERIC_MESSAGES.get(exc.status_code, GENERIC_MESSAGES[500])

    # For client errors, check if the message contains potentially sensitive info
    sensitive_patterns = [
        "sql", "query", "database", "column", "table", "postgres",
        "redis", "connection", "timeout", "stack", "traceback",
        "file path", "directory", "/app/", "/home/", "\\app\\",
    ]

    message_lower = exc.message.lower()
    for pattern in sensitive_patterns:
        if pattern in message_lower:
            return GENERIC_MESSAGES.get(exc.status_code, GENERIC_MESSAGES[400])

    return exc.message


async def app_exception_handler(request: Request, exc: AppException) -> JSONResponse:
    """Handle custom application exceptions."""
    # Always log the full error server-side
    logger.error(
        f"Application error: {exc.message}",
        extra={
            "path": request.url.path,
            "method": request.method,
            "status_code": exc.status_code,
            "client_ip": request.client.host if request.client else None,
        }
    )

    # Return sanitized message to client
    safe_message = get_safe_message(exc)

    response_content = {
        "error": safe_message,
        "status_code": exc.status_code,
    }

    # Only include path in development
    if not IS_PRODUCTION:
        response_content["path"] = request.url.path

    return JSONResponse(
        status_code=exc.status_code,
        content=response_content
    )


async def validation_exception_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    """Handle request validation errors."""
    errors = []
    for error in exc.errors():
        error_detail = {
            "field": ".".join(str(loc) for loc in error["loc"]),
            "message": error["msg"],
        }
        # Only include error type in development
        if not IS_PRODUCTION:
            error_detail["type"] = error["type"]
        errors.append(error_detail)

    logger.warning(
        f"Validation error on {request.url.path}",
        extra={
            "errors": errors,
            "method": request.method,
            "client_ip": request.client.host if request.client else None,
        }
    )

    response_content = {
        "error": "Validation failed",
        "details": errors,
    }

    if not IS_PRODUCTION:
        response_content["path"] = request.url.path

    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content=response_content
    )


async def database_exception_handler(request: Request, exc: SQLAlchemyError) -> JSONResponse:
    """Handle SQLAlchemy database errors."""
    # Log full error details server-side (never expose to client)
    logger.error(
        f"Database error on {request.url.path}: {str(exc)}",
        extra={
            "method": request.method,
            "client_ip": request.client.host if request.client else None,
        },
        exc_info=True
    )

    # Always return generic message for database errors
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": GENERIC_MESSAGES[500],
            "status_code": 500,
        }
    )


async def generic_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Handle all uncaught exceptions."""
    # Log full error details server-side (never expose to client)
    logger.critical(
        f"Unhandled exception on {request.url.path}: {str(exc)}",
        extra={
            "method": request.method,
            "client_ip": request.client.host if request.client else None,
            "exception_type": type(exc).__name__,
        },
        exc_info=True
    )

    # Always return generic message for unhandled exceptions
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": GENERIC_MESSAGES[500],
            "status_code": 500,
        }
    )


def register_exception_handlers(app):
    """Register all exception handlers with the FastAPI app."""
    app.add_exception_handler(AppException, app_exception_handler)
    app.add_exception_handler(RequestValidationError, validation_exception_handler)
    app.add_exception_handler(SQLAlchemyError, database_exception_handler)
    app.add_exception_handler(Exception, generic_exception_handler)

    env_mode = "PRODUCTION" if IS_PRODUCTION else "DEVELOPMENT"
    logger.info(f"Exception handlers registered ({env_mode} mode - errors {'sanitized' if IS_PRODUCTION else 'verbose'})")
