"""
blueprints/company/__init__.py
================================
Company Blueprint — company profile, departments, and positions management.

Manages:
    - Company profile and branding
    - Departments and sub-departments
    - Job positions and grades
    - Work shifts and schedules
    - Office/branch locations with GPS coordinates
    - Holiday calendar

URL prefix: /company
"""

from flask import Blueprint

company_bp = Blueprint(
    "company",
    __name__,
    template_folder="templates",
    static_folder="static",
    url_prefix="/company",
)

from . import routes  # noqa: E402, F401
