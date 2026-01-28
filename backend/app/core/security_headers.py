"""
Security headers middleware.

Adds security-related HTTP headers to all responses to protect against
common web vulnerabilities like clickjacking, XSS, MIME sniffing, etc.
"""

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """
    Middleware that adds security headers to all HTTP responses.

    Headers added:
    - X-Content-Type-Options: Prevents MIME type sniffing
    - X-Frame-Options: Prevents clickjacking attacks
    - X-XSS-Protection: Legacy XSS protection for older browsers
    - Referrer-Policy: Controls referrer information sent with requests
    - Permissions-Policy: Restricts browser features
    - Content-Security-Policy: Controls resource loading (configurable)
    - Strict-Transport-Security: Forces HTTPS (only in production)
    """

    def __init__(self, app, enable_hsts: bool = False, csp_policy: str = None):
        """
        Initialize security headers middleware.

        Args:
            app: The ASGI application
            enable_hsts: Enable HSTS header (only for production with HTTPS)
            csp_policy: Custom Content-Security-Policy, or None for default
        """
        super().__init__(app)
        self.enable_hsts = enable_hsts
        self.csp_policy = csp_policy or self._default_csp()

    def _default_csp(self) -> str:
        """
        Default Content-Security-Policy.

        Allows:
        - Self-hosted resources
        - Inline styles (needed for some React components)
        - Data URIs for images (blur hash placeholders)
        - WebSocket connections to self
        """
        return "; ".join([
            "default-src 'self'",
            "script-src 'self'",
            "style-src 'self' 'unsafe-inline'",  # Inline styles for React
            "img-src 'self' data: blob:",  # Allow data URIs and blobs for images
            "font-src 'self'",
            "connect-src 'self' ws: wss:",  # WebSocket for live updates
            "frame-ancestors 'none'",  # Prevent framing (clickjacking)
            "base-uri 'self'",
            "form-action 'self'",
        ])

    async def dispatch(self, request: Request, call_next) -> Response:
        """Add security headers to the response."""
        response = await call_next(request)

        # Prevent MIME type sniffing
        response.headers["X-Content-Type-Options"] = "nosniff"

        # Prevent clickjacking - DENY means page cannot be displayed in iframe
        response.headers["X-Frame-Options"] = "DENY"

        # Legacy XSS protection for older browsers
        response.headers["X-XSS-Protection"] = "1; mode=block"

        # Control referrer information
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"

        # Restrict browser features/APIs
        response.headers["Permissions-Policy"] = (
            "accelerometer=(), "
            "camera=(), "
            "geolocation=(), "
            "gyroscope=(), "
            "magnetometer=(), "
            "microphone=(), "
            "payment=(), "
            "usb=()"
        )

        # Content Security Policy
        response.headers["Content-Security-Policy"] = self.csp_policy

        # HSTS - only enable in production with valid HTTPS
        if self.enable_hsts:
            # max-age=31536000 = 1 year
            response.headers["Strict-Transport-Security"] = (
                "max-age=31536000; includeSubDomains"
            )

        # Prevent caching of sensitive data
        if request.url.path.startswith(("/login", "/register", "/me", "/2fa")):
            response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate"
            response.headers["Pragma"] = "no-cache"

        return response
