"""
blueprints/leave/__init__.py
==============================
Leave Blueprint — leave request lifecycle and balance management.

Manages:
    - Leave applications by employees
    - Approval workflow (Manager → HR)
    - Leave balance tracking per employee per type
    - Leave policy configuration
    - Team leave calendar

URL prefix: /leave
"""

from flask import Blueprint

leave_bp = Blueprint(
    "leave",
    __name__,
    template_folder="templates",
    static_folder="static",
    url_prefix="/leave",
)

from . import routes  # noqa: E402, F401
