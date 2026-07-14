"""
blueprints/dashboard/__init__.py
==================================
Dashboard Blueprint — main landing page after login.

Displays summary statistics, quick-action cards, recent activity,
and charts. Data is provided by DashboardService.

URL prefix: /dashboard
"""

from flask import Blueprint

dashboard_bp = Blueprint(
    "dashboard",
    __name__,
    template_folder="templates",
    static_folder="static",
    url_prefix="/dashboard",
)

from . import routes  # noqa: E402, F401
