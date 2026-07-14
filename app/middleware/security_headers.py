"""
app/middleware/security_headers.py
====================================
Security HTTP response headers middleware.

Injects security headers on every outgoing response to protect against
common web vulnerabilities:

    X-Content-Type-Options     — prevent MIME-type sniffing
    X-Frame-Options            — clickjacking protection
    X-XSS-Protection           — legacy XSS filter hint
    Referrer-Policy            — control referrer leakage
    Permissions-Policy         — disable unused browser features
    Strict-Transport-Security  — enforce HTTPS (production only)
    Content-Security-Policy    — control resource loading sources
    Cache-Control              — prevent caching sensitive pages

Headers are read from app.config["SECURITY_HEADERS"] so that
production and development can have different policies.
"""

import logging

logger = logging.getLogger(__name__)


def register_security_headers(app) -> None:
    """
    Register the after_request hook that injects security headers.

    Args:
        app: The Flask application instance.
    """

    @app.after_request
    def apply_security_headers(response):
        """
        Inject security headers from configuration into every response.

        Skips static file responses to avoid performance overhead on
        cached assets (browsers respect cache headers on statics).

        Args:
            response: The outgoing Flask Response object.

        Returns:
            Modified Response with security headers applied.
        """
        from flask import request  # noqa: PLC0415

        # Skip static assets — they don't need security headers
        if request.path.startswith("/static/"):
            return response

        headers = app.config.get("SECURITY_HEADERS", {})
        for header_name, header_value in headers.items():
            response.headers[header_name] = header_value

        # Prevent browsers from caching authenticated page responses
        if _is_authenticated_route(request):
            response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0"
            response.headers["Pragma"] = "no-cache"
            response.headers["Expires"] = "0"

        return response

    logger.debug("Security headers middleware registered.")


def _is_authenticated_route(request) -> bool:
    """
    Determine if the current request is an authenticated application route.

    Returns False for public pages (login, static, health check) so that
    those pages can still benefit from browser caching.

    Args:
        request: The Flask request object.

    Returns:
        True if the route requires authentication.
    """
    public_prefixes = ("/static/", "/auth/", "/health")
    return not any(request.path.startswith(p) for p in public_prefixes)
