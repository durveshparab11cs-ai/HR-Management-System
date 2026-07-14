"""
blueprints/admin/__init__.py
==============================
Admin Blueprint — super-admin system management panel.

Provides:
    - User account management (create, activate, suspend, assign roles)
    - System health overview
    - Audit log viewer
    - Database maintenance utilities
    - Application configuration override

URL prefix: /admin
Access: SUPER_ADMIN only
"""

from flask import Blueprint

admin_bp = Blueprint(
    "admin",
    __name__,
    template_folder="templates",
    static_folder="static",
    url_prefix="/admin",
)

from . import routes  # noqa: E402, F401
