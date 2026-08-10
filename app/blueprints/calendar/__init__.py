"""
blueprints/calendar/__init__.py
==================================
Calendar Blueprint — company holiday calendar and management.

Manages:
    - Holiday calendar display with month/year navigation
    - Holiday details and listing
    - Excel import functionality (HR/Admin only)

URL prefix: /calendar
"""

from flask import Blueprint

calendar_bp = Blueprint(
    "calendar",
    __name__,
    template_folder="templates",
    static_folder="static",
    url_prefix="/calendar",
)

from . import routes  # noqa: E402, F401
