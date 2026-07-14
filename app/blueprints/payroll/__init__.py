"""
blueprints/payroll/__init__.py
================================
Payroll Blueprint — payroll processing, payslips, and salary management.

Manages:
    - Monthly payroll runs
    - Salary structure and components (basic, HRA, allowances, deductions)
    - Payslip generation and PDF download
    - Tax computation
    - Bank transfer export

URL prefix: /payroll
"""

from flask import Blueprint

payroll_bp = Blueprint(
    "payroll",
    __name__,
    template_folder="templates",
    static_folder="static",
    url_prefix="/payroll",
)

from . import routes  # noqa: E402, F401
