"""
blueprints/authentication/__init__.py
======================================
Authentication Blueprint — login, logout, registration, password reset,
email verification, and session management.

URL prefix: /auth
"""

from flask import Blueprint

authentication_bp = Blueprint(
    "authentication",
    __name__,
    static_folder="static",
    url_prefix="/auth",
)

# Import routes after blueprint creation to avoid circular imports.
from . import routes  # noqa: E402, F401
