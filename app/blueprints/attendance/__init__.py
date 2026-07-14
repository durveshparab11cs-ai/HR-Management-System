"""
blueprints/attendance/__init__.py
===================================
Attendance Blueprint — daily attendance tracking and management.

Manages:
    - Employee check-in / check-out (GPS-verified)
    - Daily attendance records
    - Attendance correction requests
    - Bulk attendance import
    - Monthly attendance summaries

URL prefix: /attendance
"""

from flask import Blueprint

attendance_bp = Blueprint(
    "attendance",
    __name__,
    template_folder="templates",
    static_folder="static",
    url_prefix="/attendance",
)

from . import routes  # noqa: E402, F401
