"""
blueprints/notifications/__init__.py
======================================
Notifications Blueprint — in-app notifications and alerts.

Manages:
    - In-app notification inbox
    - Read/unread state management
    - Notification preference settings
    - Notification count badge (via AJAX endpoint)

URL prefix: /notifications
"""

from flask import Blueprint

notifications_bp = Blueprint(
    "notifications",
    __name__,
    template_folder="templates",
    static_folder="static",
    url_prefix="/notifications",
)

from . import routes  # noqa: E402, F401
