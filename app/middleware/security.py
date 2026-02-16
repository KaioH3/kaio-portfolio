"""
Security Middleware - OWASP Top 10 Protection
Implements security headers, input validation, and attack prevention
"""
from fastapi import Request, Response
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp
from typing import Callable
import logging
import re
from urllib.parse import urlparse

logger = logging.getLogger(__name__)


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """
    Add security headers to all responses
    OWASP recommendations + modern browser security
    """

    def __init__(self, app: ASGIApp, environment: str = "development"):
        super().__init__(app)
        self.environment = environment

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        response = await call_next(request)

        # Content Security Policy (CSP)
        # Prevent XSS attacks by controlling resource loading
        csp_directives = [
            "default-src 'self'",
            "script-src 'self' 'unsafe-inline' https://gc.zgo.at https://fonts.googleapis.com",
            "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com",
            "font-src 'self' https://fonts.gstatic.com",
            "img-src 'self' data: https:",
            "connect-src 'self' https://gc.zgo.at",
            "frame-ancestors 'none'",
            "base-uri 'self'",
            "form-action 'self'",
        ]
        response.headers["Content-Security-Policy"] = "; ".join(csp_directives)

        # HSTS (HTTP Strict Transport Security)
        # Force HTTPS for 1 year, include subdomains
        if self.environment == "production":
            response.headers["Strict-Transport-Security"] = (
                "max-age=31536000; includeSubDomains; preload"
            )

        # X-Frame-Options
        # Prevent clickjacking attacks
        response.headers["X-Frame-Options"] = "DENY"

        # X-Content-Type-Options
        # Prevent MIME type sniffing
        response.headers["X-Content-Type-Options"] = "nosniff"

        # X-XSS-Protection (legacy browsers)
        # Enable XSS filter
        response.headers["X-XSS-Protection"] = "1; mode=block"

        # Referrer-Policy
        # Control referrer information
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"

        # Permissions-Policy (Feature-Policy replacement)
        # Disable unnecessary browser features
        permissions = [
            "geolocation=()",
            "microphone=()",
            "camera=()",
            "payment=()",
            "usb=()",
            "magnetometer=()",
            "gyroscope=()",
            "accelerometer=()",
        ]
        response.headers["Permissions-Policy"] = ", ".join(permissions)

        # X-Permitted-Cross-Domain-Policies
        # Restrict cross-domain policies
        response.headers["X-Permitted-Cross-Domain-Policies"] = "none"

        # X-DNS-Prefetch-Control
        # Control DNS prefetching
        response.headers["X-DNS-Prefetch-Control"] = "off"

        # Cache-Control for sensitive endpoints
        if request.url.path.startswith(("/api/", "/admin/")):
            response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, private"
            response.headers["Pragma"] = "no-cache"
            response.headers["Expires"] = "0"

        return response


class InputSanitizationMiddleware(BaseHTTPMiddleware):
    """
    Sanitize and validate all user inputs
    Protect against injection attacks (XSS, SQL, NoSQL, etc)
    """

    # Patterns for common attacks
    XSS_PATTERNS = [
        r'<script[^>]*>.*?</script>',
        r'javascript:',
        r'onerror\s*=',
        r'onload\s*=',
        r'eval\(',
        r'expression\(',
    ]

    SQL_PATTERNS = [
        r'(\bUNION\b.*\bSELECT\b)',
        r'(\bSELECT\b.*\bFROM\b)',
        r'(\bDROP\b.*\bTABLE\b)',
        r'(\bINSERT\b.*\bINTO\b)',
        r'(\bDELETE\b.*\bFROM\b)',
        r'(\bUPDATE\b.*\bSET\b)',
        r'(--|;|\/\*|\*\/)',
    ]

    NOSQL_PATTERNS = [
        r'\$ne',
        r'\$gt',
        r'\$lt',
        r'\$where',
        r'\$regex',
        r'\{\s*\$',
    ]

    def __init__(self, app: ASGIApp):
        super().__init__(app)
        self.xss_regex = [re.compile(p, re.IGNORECASE) for p in self.XSS_PATTERNS]
        self.sql_regex = [re.compile(p, re.IGNORECASE) for p in self.SQL_PATTERNS]
        self.nosql_regex = [re.compile(p, re.IGNORECASE) for p in self.NOSQL_PATTERNS]

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Skip static files and health checks
        if request.url.path.startswith(("/static/", "/favicon", "/api/health", "/api/ready")):
            return await call_next(request)

        # Check query parameters
        for param, value in request.query_params.items():
            if self._is_malicious(value):
                logger.warning(
                    f"Malicious input detected in query param '{param}' from {request.client.host}: {value[:100]}"
                )
                return JSONResponse(
                    status_code=400,
                    content={"error": "Invalid input detected", "detail": "Request contains potentially malicious content"}
                )

        # Check form data (if POST/PUT/PATCH)
        if request.method in ("POST", "PUT", "PATCH"):
            try:
                # For JSON requests
                if request.headers.get("content-type", "").startswith("application/json"):
                    body = await request.body()
                    if body and self._check_json_payload(body.decode("utf-8")):
                        logger.warning(f"Malicious JSON payload from {request.client.host}")
                        return JSONResponse(
                            status_code=400,
                            content={"error": "Invalid input detected", "detail": "Request body contains potentially malicious content"}
                        )
            except Exception as e:
                logger.error(f"Error checking request body: {e}")

        return await call_next(request)

    def _is_malicious(self, value: str) -> bool:
        """Check if value contains malicious patterns"""
        value_lower = value.lower()

        # Check XSS patterns
        for regex in self.xss_regex:
            if regex.search(value):
                return True

        # Check SQL injection patterns
        for regex in self.sql_regex:
            if regex.search(value):
                return True

        # Check NoSQL injection patterns
        for regex in self.nosql_regex:
            if regex.search(value):
                return True

        # Check for path traversal
        if '../' in value or '..\\' in value:
            return True

        # Check for command injection
        dangerous_chars = ['|', '&', ';', '`', '$', '(', ')', '{', '}']
        if any(char in value for char in dangerous_chars):
            return True

        return False

    def _check_json_payload(self, payload: str) -> bool:
        """Check JSON payload for malicious content"""
        # Simple check for common attack patterns in JSON
        return self._is_malicious(payload)


class RateLimitByIPMiddleware(BaseHTTPMiddleware):
    """
    IP-based rate limiting for all endpoints
    Prevents brute force and DoS attacks
    """

    def __init__(self, app: ASGIApp, max_requests: int = 100, window_seconds: int = 60):
        super().__init__(app)
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self._requests: dict = {}  # {ip: [(timestamp, path), ...]}

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Skip health checks
        if request.url.path in ("/api/health", "/api/ready"):
            return await call_next(request)

        client_ip = request.client.host
        current_time = self._get_current_time()

        # Clean old requests
        if client_ip in self._requests:
            self._requests[client_ip] = [
                (ts, path)
                for ts, path in self._requests[client_ip]
                if current_time - ts < self.window_seconds
            ]

        # Check rate limit
        if client_ip not in self._requests:
            self._requests[client_ip] = []

        if len(self._requests[client_ip]) >= self.max_requests:
            logger.warning(
                f"Rate limit exceeded for IP {client_ip}: "
                f"{len(self._requests[client_ip])} requests in {self.window_seconds}s"
            )
            return JSONResponse(
                status_code=429,
                content={
                    "error": "Too Many Requests",
                    "detail": f"Rate limit exceeded. Max {self.max_requests} requests per {self.window_seconds} seconds.",
                    "retry_after": self.window_seconds
                },
                headers={"Retry-After": str(self.window_seconds)}
            )

        # Record request
        self._requests[client_ip].append((current_time, request.url.path))

        return await call_next(request)

    def _get_current_time(self) -> float:
        """Get current timestamp (mockable for testing)"""
        import time
        return time.time()


class HostHeaderValidationMiddleware(BaseHTTPMiddleware):
    """
    Validate Host header to prevent host header injection attacks
    """

    def __init__(self, app: ASGIApp, allowed_hosts: list = None):
        super().__init__(app)
        self.allowed_hosts = allowed_hosts or ["localhost", "127.0.0.1", "kaio.ia.br", "*.kaio.ia.br"]

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        host = request.headers.get("host", "")

        # Extract hostname (remove port)
        hostname = host.split(":")[0]

        # Check if host is allowed
        if not self._is_allowed_host(hostname):
            logger.warning(f"Invalid Host header: {host} from {request.client.host}")
            return JSONResponse(
                status_code=400,
                content={"error": "Invalid Host header"}
            )

        return await call_next(request)

    def _is_allowed_host(self, hostname: str) -> bool:
        """Check if hostname is in allowed list"""
        for allowed in self.allowed_hosts:
            if allowed.startswith("*."):
                # Wildcard subdomain
                domain = allowed[2:]
                if hostname.endswith(domain):
                    return True
            elif hostname == allowed:
                return True
        return False


def setup_security_middleware(app, environment: str = "development", allowed_hosts: list = None):
    """
    Setup all security middleware
    Call this in app/main.py
    """
    # Security headers (OWASP recommendations)
    app.add_middleware(SecurityHeadersMiddleware, environment=environment)

    # Input sanitization (XSS, SQL injection, etc)
    app.add_middleware(InputSanitizationMiddleware)

    # Rate limiting (DoS protection)
    max_requests = 200 if environment == "production" else 500
    app.add_middleware(RateLimitByIPMiddleware, max_requests=max_requests, window_seconds=60)

    # Host header validation (Host header injection)
    if allowed_hosts:
        app.add_middleware(HostHeaderValidationMiddleware, allowed_hosts=allowed_hosts)

    logger.info(f"Security middleware enabled ({environment} mode)")
