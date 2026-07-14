"""
app/middleware/request_logger.py
==================================
Structured request/response logging middleware.

Logs every HTTP request with:
    - HTTP method and path
    - Authenticated user ID
    - Client IP address
    - Response status code
    - Request duration in milliseconds

Uses Python's standard logging routed to application.log.
Sensitive paths (login, password reset) are logged but their
POST bodies are never logged.
"""

import logging
import time

logger = logging.getLogger("application")

# Paths whose response bodies must never be logged
_SENSITIVE_PATHS = {
    "/auth/login",
    "/auth/register",
    "/auth/reset-password",
    "/auth/change-password",
    "/api/v1/auth/login",
    "/api/v1/auth/token",
}


def register_request_logger(app) -> None:
    """
    Register before_request and after_request hooks for request logging.

    Args:
        app: The Flask application instance.
    """

    @app.before_request
    def log_request_start():
        """Record the request start time for duration calculation."""
        from flask import g, request  # noqa: PLC0415
        g.request_start_time = time.monotonic()
        g.request_id = _generate_request_id()

        # Skip logging for health checks and static files to reduce noise
        if request.path in ("/health", "/favicon.ico") or \
           request.path.startswith("/static/"):
            return

        logger.debug(
            "REQUEST | id=%s | %s %s | ip=%s | ua=%s",
            g.request_id,
            request.method,
            request.path,
            _get_client_ip(request),
            request.user_agent.string[:100] if request.user_agent else "unknown",
        )

    @app.after_request
    def log_request_end(response):
        """Log the completed request with status code and duration."""
        from flask import g, request  # noqa: PLC0415

        if request.path in ("/health", "/favicon.ico") or \
           request.path.startswith("/static/"):
            return response

        start_time = getattr(g, "request_start_time", None)
        duration_ms = round((time.monotonic() - start_time) * 1000, 2) if start_time else -1
        request_id = getattr(g, "request_id", "unknown")

        user_id = _get_current_user_id()

        log_fn = logger.warning if response.status_code >= 400 else logger.info
        log_fn(
            "RESPONSE | id=%s | %s %s | status=%d | user=%s | ip=%s | duration=%sms",
            request_id,
            request.method,
            request.path,
            response.status_code,
            user_id,
            _get_client_ip(request),
            duration_ms,
        )

        return response

    logger.debug("Request logger middleware registered.")


def _get_client_ip(request) -> str:
    """
    Extract the real client IP from the request.

    Checks X-Forwarded-For first (set by Nginx/load balancer via ProxyFix),
    then falls back to remote_addr.

    Args:
        request: The Flask request object.

    Returns:
        IP address string.
    """
    forwarded_for = request.headers.get("X-Forwarded-For")
    if forwarded_for:
        return forwarded_for.split(",")[0].strip()
    return request.remote_addr or "unknown"


def _get_current_user_id() -> str:
    """Safely get the current user's ID string for logging."""
    try:
        from flask_login import current_user  # noqa: PLC0415
        if current_user and current_user.is_authenticated:
            return str(current_user.id)
    except Exception:  # noqa: BLE001
        pass
    return "anonymous"


def _generate_request_id() -> str:
    """Generate a short unique ID for request correlation in logs."""
    import uuid  # noqa: PLC0415
    return uuid.uuid4().hex[:12]
