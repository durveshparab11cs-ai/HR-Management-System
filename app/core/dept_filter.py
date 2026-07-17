"""
app/core/dept_filter.py
========================
Department-based access control helpers.

Every query that lists employees, attendance, leave, payroll, or reports
must call get_dept_filter() to restrict results to the logged-in user's
department — unless the user has global access (CEO, Proprietor, AGM, Admin).

Usage:
    from app.core.dept_filter import get_dept_filter, apply_emp_dept_filter

    # Get the department string (None = global access, show all)
    dept = get_dept_filter()

    # Apply to an Employee queryset
    q = Employee.query.filter_by(is_deleted=False)
    q = apply_emp_dept_filter(q)
    employees = q.all()
"""

from flask import session
from flask_login import current_user

from app.constants.enums import GLOBAL_ACCESS_DEPARTMENTS, UserRole


def get_dept_filter() -> str | None:
    """
    Return the department string to filter by, or None for global access.

    Returns:
        str  — department name (e.g. "Operations") to filter on
        None — no filter; user can see all departments
    """
    if not current_user or not current_user.is_authenticated:
        return None

    # Super Admin and Admin always see everything
    if current_user.role in (UserRole.SUPER_ADMIN.value, UserRole.ADMIN.value):
        return None

    dept = session.get("login_department", "")
    if not dept:
        # Fall back to the employee's assigned department
        emp = getattr(current_user, "employee", None)
        dept = (emp.department or "") if emp else ""

    # Global-access departments see everything
    if dept in GLOBAL_ACCESS_DEPARTMENTS:
        return None

    return dept or None


def apply_emp_dept_filter(query):
    """
    Apply department filter to an Employee SQLAlchemy query.

    Args:
        query: SQLAlchemy Query object on the Employee model.

    Returns:
        Filtered query (unchanged if user has global access).
    """
    from app.models.employee import Employee  # noqa: PLC0415

    dept = get_dept_filter()
    if dept:
        query = query.filter(Employee.department == dept)
    return query


def can_access_dept(department: str) -> bool:
    """
    Check whether the current user can access a specific department's data.

    Args:
        department: Department name to check.

    Returns:
        True if the user has access.
    """
    dept_filter = get_dept_filter()
    if dept_filter is None:
        return True  # global access
    return (department or "").lower() == dept_filter.lower()


def get_current_dept() -> str:
    """Return the logged-in user's active department (empty string if none)."""
    dept = get_dept_filter()
    if dept is not None:
        return dept
    # Global access — return their own dept for display purposes
    emp = getattr(current_user, "employee", None) if current_user and current_user.is_authenticated else None
    return (emp.department or "") if emp else ""
