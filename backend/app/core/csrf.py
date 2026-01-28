"""
CSRF (Cross-Site Request Forgery) Protection Middleware.

Provides double-submit cookie pattern for CSRF protection when using
httpOnly cookies for authentication.

How it works:
1. On login, server generates a CSRF token and sets it in:
   - An httpOnly cookie (csrf_token) - cannot be read by JS
   - Response header (X-CSRF-Token) - JS stores this in memory
2. On state-changing requests (POST, PUT, DELETE, PATCH):
   - Client sends the token in X-CSRF-Token header
   - Server compares header value with cookie value
   - Request is rejected if they don't match

This prevents CSRF because:
- Attacker can't read the CSRF token (httpOnly cookie + SameSite)
- Attacker can't set custom headers in cross-origin requests
"""

import secrets
import logging
from typing import Optional
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response, JSONResponse

logger = logging.getLogger(__name__)

# Token configuration
CSRF_TOKEN_LENGTH = 32
CSRF_COOKIE_NAME = "csrf_token"
CSRF_HEADER_NAME = "X-CSRF-Token"

# Methods that require CSRF validation
CSRF_PROTECTED_METHODS = {"POST", "PUT", "DELETE", "PATCH"}

# Paths exempt from CSRF validation (e.g., login endpoints that set the token)
CSRF_EXEMPT_PATHS = {
    "/login",
    "/login/2fa",
    "/register",
    "/health",
    "/",
    "/docs",
    "/openapi.json",
    "/redoc",
    "/forgot-password",
    "/reset-password",
    "/verify-reset-token/*",
}


def generate_csrf_token() -> str:
    """Generate a cryptographically secure CSRF token."""
    return secrets.token_urlsafe(CSRF_TOKEN_LENGTH)


def set_csrf_cookie(response: Response, token: str, secure: bool = False) -> None:
    """
    Set the CSRF token cookie on the response.

    Args:
        response: The response to set the cookie on
        token: The CSRF token value
        secure: Whether to set the Secure flag (True for HTTPS in production)
    """
    response.set_cookie(
        key=CSRF_COOKIE_NAME,
        value=token,
        httponly=True,  # Prevent JS access
        samesite="lax",  # Prevent cross-site requests
        secure=secure,  # Only send over HTTPS in production
        max_age=86400,  # 24 hours
        path="/",
    )


class CSRFMiddleware(BaseHTTPMiddleware):
    """
    CSRF protection middleware using double-submit cookie pattern.

    For state-changing requests (POST, PUT, DELETE, PATCH), validates that
    the X-CSRF-Token header matches the csrf_token cookie.
    """

    def __init__(self, app, secure_cookies: bool = False, exempt_paths: set = None):
        """
        Initialize CSRF middleware.

        Args:
            app: The ASGI application
            secure_cookies: Set Secure flag on cookies (use True in production with HTTPS)
            exempt_paths: Additional paths to exempt from CSRF validation
        """
        super().__init__(app)
        self.secure_cookies = secure_cookies
        self.exempt_paths = CSRF_EXEMPT_PATHS.copy()
        if exempt_paths:
            self.exempt_paths.update(exempt_paths)

    def _is_exempt(self, path: str) -> bool:
        """Check if the path is exempt from CSRF validation."""
        # Exact match
        if path in self.exempt_paths:
            return True

        # Check if path starts with any exempt prefix
        for exempt in self.exempt_paths:
            if exempt.endswith("*") and path.startswith(exempt[:-1]):
                return True

        return False

    def _get_csrf_from_cookie(self, request: Request) -> Optional[str]:
        """Extract CSRF token from cookie."""
        return request.cookies.get(CSRF_COOKIE_NAME)

    def _get_csrf_from_header(self, request: Request) -> Optional[str]:
        """Extract CSRF token from header."""
        return request.headers.get(CSRF_HEADER_NAME)

    async def dispatch(self, request: Request, call_next) -> Response:
        """Process the request with CSRF validation."""
        method = request.method.upper()
        path = request.url.path

        # Skip CSRF validation for safe methods and exempt paths
        if method not in CSRF_PROTECTED_METHODS or self._is_exempt(path):
            response = await call_next(request)

            # Generate new CSRF token if one doesn't exist
            if not self._get_csrf_from_cookie(request):
                token = generate_csrf_token()
                set_csrf_cookie(response, token, self.secure_cookies)
                response.headers[CSRF_HEADER_NAME] = token

            return response

        # Validate CSRF token for protected methods
        cookie_token = self._get_csrf_from_cookie(request)
        header_token = self._get_csrf_from_header(request)

        # If no cookie token exists, this might be a first request or cookie expired
        # Generate a new token and reject the request
        if not cookie_token:
            logger.warning(f"CSRF validation failed: No cookie token for {method} {path}")
            response = JSONResponse(
                status_code=403,
                content={"detail": "CSRF token missing. Please refresh and try again."}
            )
            token = generate_csrf_token()
            set_csrf_cookie(response, token, self.secure_cookies)
            response.headers[CSRF_HEADER_NAME] = token
            return response

        # Validate header token matches cookie token
        if not header_token:
            logger.warning(f"CSRF validation failed: No header token for {method} {path}")
            return JSONResponse(
                status_code=403,
                content={"detail": "CSRF token header missing."}
            )

        if not secrets.compare_digest(cookie_token, header_token):
            logger.warning(f"CSRF validation failed: Token mismatch for {method} {path}")
            return JSONResponse(
                status_code=403,
                content={"detail": "CSRF token invalid."}
            )

        # CSRF validation passed, continue with request
        response = await call_next(request)

        # Optionally rotate CSRF token on successful state-changing request
        # (disabled by default to avoid complexity, but can be enabled for higher security)
        # token = generate_csrf_token()
        # set_csrf_cookie(response, token, self.secure_cookies)
        # response.headers[CSRF_HEADER_NAME] = token

        return response
