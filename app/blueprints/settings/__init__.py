"""
blueprints/settings/__init__.py
=================================
Settings Blueprint — application and user preference configuration.

Manages:
    - Application-level settings (admin only)
    - User profile settings (all users)
    - Notification preferences
    - Security settings (password change, 2FA)
    - Leave policy configuration

URL prefix: /settings
"""

from flask import Blueprint

settings_bp = Blueprint(
    "settings",
    __name__,
    template_folder="templates",
    static_folder="static",
    url_prefix="/settings",
)

from . import routes  # noqa: E402, F401
