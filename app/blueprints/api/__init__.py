"""
blueprints/api/__init__.py
============================
API Blueprint — RESTful JSON API for mobile clients and integrations.

Provides versioned REST endpoints under /api/v1/.
All responses use the standardized envelope from response_utils.

Authentication: Bearer token (JWT) — CSRF exempt.
Rate limiting: Stricter than web routes (60 req/min default).

URL prefix: /api/v1
"""

from flask import Blueprint

api_bp = Blueprint(
    "api",
    __name__,
    url_prefix="/api/v1",
)

from .v1 import routes  # noqa: E402, F401
