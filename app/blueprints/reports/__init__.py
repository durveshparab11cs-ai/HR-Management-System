"""
blueprints/reports/__init__.py
================================
Reports Blueprint — business intelligence and data exports.

Provides:
    - Attendance reports (daily, monthly, summary)
    - Leave reports (utilization, balance)
    - Payroll reports (cost summary, department-wise)
    - Employee reports (headcount, turnover)
    - Custom date-range exports (CSV, Excel, PDF)

URL prefix: /reports
"""

from flask import Blueprint

reports_bp = Blueprint(
    "reports",
    __name__,
    template_folder="templates",
    static_folder="static",
    url_prefix="/reports",
)

from . import routes  # noqa: E402, F401
