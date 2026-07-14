"""
app/middleware/__init__.py
==========================
Request/response middleware pipeline.

Middleware components hook into Flask's before_request, after_request,
and teardown_request lifecycle to apply cross-cutting concerns:

    security_headers   — inject security HTTP headers on every response
    request_logger     — log every incoming request with timing
    ProxyFix           — trust X-Forwarded-For from reverse proxy

All middleware is registered via register_middleware(app) called
from the application factory.
"""

from .request_logger import register_request_logger
from .security_headers import register_security_headers
from .proxy import register_proxy_fix

__all__ = [
    "register_request_logger",
    "register_security_headers",
    "register_proxy_fix",
]


def register_middleware(app) -> None:
    """
    Register all middleware components with the Flask application.

    Called from create_app() after extension initialization.

    Args:
        app: The Flask application instance.
    """
    register_proxy_fix(app)
    register_security_headers(app)
    register_request_logger(app)
