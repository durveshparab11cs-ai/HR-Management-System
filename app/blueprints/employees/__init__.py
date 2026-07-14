"""
blueprints/employees/__init__.py
==================================
Employees Blueprint — employee lifecycle management.

Manages:
    - Employee profiles (personal, contact, emergency, bank)
    - Employment records (hire, transfer, promotion, termination)
    - Document management (ID proofs, certificates, contracts)
    - Profile photo upload
    - Employee search and filtering

URL prefix: /employees
"""

from flask import Blueprint

employees_bp = Blueprint(
    "employees",
    __name__,
    template_folder="templates",
    static_folder="static",
    url_prefix="/employees",
)

from . import routes  # noqa: E402, F401
