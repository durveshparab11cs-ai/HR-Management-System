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

# Hospital routes - safely import with error handling
try:
    from . import routes_hospital  # noqa: E402, F401
except Exception as e:
    # If hospital tables don't exist yet, skip these routes
    # They will be available after database migration
    import logging
    logging.getLogger(__name__).warning(f"Hospital routes disabled: {e}")
