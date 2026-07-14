"""
blueprints/employees/validators.py
=====================================
Business-rule validators for employee data.
"""

import re
from datetime import date
from typing import Optional, Tuple

from app.utils.validation_utils import is_valid_email, is_valid_phone


def validate_employee_code(code: str, exclude_id: Optional[int] = None) -> Tuple[bool, str]:
    if not code or not re.match(r'^[A-Za-z0-9\-]{3,20}$', code.strip()):
        return False, "Employee code must be 3–20 alphanumeric characters."
    from .repository import EmployeeRepository
    repo = EmployeeRepository()
    existing = repo.get_by_employee_code(code)
    if existing and existing.id != exclude_id:
        return False, f"Employee code '{code.upper()}' is already in use."
    return True, ""


def validate_email_unique(email: str, exclude_user_id: Optional[int] = None) -> Tuple[bool, str]:
    if not is_valid_email(email):
        return False, "Please enter a valid email address."
    from .repository import EmployeeRepository
    repo = EmployeeRepository()
    existing = repo.get_user_by_email(email)
    if existing and existing.id != exclude_user_id:
        return False, f"Email '{email}' is already registered."
    return True, ""


def validate_join_date(join_date: Optional[date], dob: Optional[date]) -> Tuple[bool, str]:
    if not join_date:
        return True, ""
    if join_date > date.today():
        return False, "Date of joining cannot be in the future."
    if dob and join_date <= dob:
        return False, "Date of joining must be after date of birth."
    return True, ""


def validate_phone(phone: str) -> Tuple[bool, str]:
    if not phone:
        return True, ""
    cleaned = re.sub(r'[\s\-\(\)]', '', phone)
    if not re.match(r'^\+?[0-9]{7,15}$', cleaned):
        return False, "Enter a valid phone number (7–15 digits)."
    return True, ""
