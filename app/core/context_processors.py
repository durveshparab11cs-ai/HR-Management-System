"""
app/core/context_processors.py
================================
Jinja2 context processors that inject variables into every template
render context automatically.

Context processors should only inject lightweight, frequently-needed
variables. Avoid expensive database queries here — use cached lookups
or pass data explicitly from route handlers for page-specific data.

Registered in the application factory via:
    app.context_processor(inject_globals)
"""

from datetime import datetime, timezone


def inject_globals() -> dict:
    """
    Inject application-wide variables into every template context.

    Returns:
        Dictionary of variables available in all Jinja2 templates.
    """
    from flask import current_app  # noqa: PLC0415

    return {
        "app_name": current_app.config.get("APP_NAME", "Smart HRMS"),
        "app_version": current_app.config.get("APP_VERSION", "1.0.0"),
        "current_year": datetime.now(timezone.utc).year,
    }


def inject_user_context() -> dict:
    """
    Inject authenticated user information into every template.
    """
    from flask_login import current_user  # noqa: PLC0415
    from app.constants.enums import UserRole, GLOBAL_ACCESS_DEPARTMENTS  # noqa: PLC0415

    context = {
        "is_authenticated": False,
        "current_user_role": None,
        "is_admin": False,
        "is_hr_manager": False,
        "is_manager": False,
        "is_foss": False,
        "login_department": "",
        "has_global_access": False,
        "unread_notification_count": 0,
    }

    try:
        if current_user and current_user.is_authenticated:
            context["is_authenticated"] = True
            context["current_user_role"] = getattr(current_user, "role", None)
            context["is_admin"] = getattr(current_user, "role", None) in (
                UserRole.SUPER_ADMIN, UserRole.ADMIN
            )
            context["is_hr_manager"] = getattr(current_user, "role", None) in (
                UserRole.SUPER_ADMIN, UserRole.ADMIN, UserRole.HR_MANAGER
            )
            context["is_manager"] = getattr(current_user, "role", None) in (
                UserRole.SUPER_ADMIN, UserRole.ADMIN, UserRole.HR_MANAGER, UserRole.MANAGER
            )
            # Safely read session — may not exist right after logout
            dept = ""
            try:
                from flask import session as _sess  # noqa: PLC0415
                dept = _sess.get("login_department", "")
            except Exception:  # noqa: BLE001
                pass
            if not dept:
                emp = getattr(current_user, "employee", None)
                dept = (emp.department or "") if emp else ""
            context["login_department"] = dept
            context["has_global_access"] = (
                current_user.role in (UserRole.SUPER_ADMIN.value, UserRole.ADMIN.value)
                or dept in GLOBAL_ACCESS_DEPARTMENTS
            )
            context["is_foss"] = (
                dept == "FOSS"
                or current_user.role in (UserRole.SUPER_ADMIN.value, UserRole.ADMIN.value)
            )
    except Exception:  # noqa: BLE001
        pass

    return context


def inject_navigation() -> dict:
    """
    Inject the sidebar navigation structure.
    """
    from flask_login import current_user  # noqa: PLC0415
    from app.constants.enums import UserRole  # noqa: PLC0415

    if not (current_user and current_user.is_authenticated):
        return {"nav_items": []}

    role = getattr(current_user, "role", None)

    # Safely get dept from session — may not exist if session was just cleared
    dept = ""
    try:
        from flask import session as _sess  # noqa: PLC0415
        dept = _sess.get("login_department", "")
    except Exception:  # noqa: BLE001
        pass
    if not dept:
        try:
            emp = getattr(current_user, "employee", None)
            dept = (emp.department or "") if emp else ""
        except Exception:  # noqa: BLE001
            pass

    all_items = [
        {"label": "Dashboard",      "icon": "bi-speedometer2",   "url_endpoint": "dashboard.index",     "roles": None},
        {"label": "Employees",      "icon": "bi-people",         "url_endpoint": "employees.index",     "roles": [UserRole.SUPER_ADMIN.value, UserRole.ADMIN.value, UserRole.HR_MANAGER.value, UserRole.HR_STAFF.value, UserRole.MANAGER.value]},
        {"label": "Attendance",     "icon": "bi-calendar-check", "url_endpoint": "attendance.index",    "roles": None},
        {"label": "Leave",          "icon": "bi-calendar-x",     "url_endpoint": "leave.index",         "roles": None},
        {"label": "Leave Approval", "icon": "bi-person-check",   "url_endpoint": "leave.my_approvals",  "roles": None},
        {"label": "Payroll",        "icon": "bi-cash-stack",     "url_endpoint": "payroll.index",       "roles": [UserRole.SUPER_ADMIN.value, UserRole.ADMIN.value, UserRole.HR_MANAGER.value]},
        {"label": "Reports",        "icon": "bi-bar-chart",      "url_endpoint": "reports.index",       "roles": [UserRole.SUPER_ADMIN.value, UserRole.ADMIN.value, UserRole.HR_MANAGER.value, UserRole.MANAGER.value]},
        {"label": "Notifications",  "icon": "bi-bell",           "url_endpoint": "notifications.index", "roles": None},
        {"label": "Company",        "icon": "bi-building",       "url_endpoint": "company.index",       "roles": [UserRole.SUPER_ADMIN.value, UserRole.ADMIN.value]},
        {"label": "Settings",       "icon": "bi-gear",           "url_endpoint": "settings.index",      "roles": [UserRole.SUPER_ADMIN.value, UserRole.ADMIN.value]},
        {"label": "Admin Panel",    "icon": "bi-shield-lock",    "url_endpoint": "admin.index",         "roles": [UserRole.SUPER_ADMIN.value]},
    ]

    # FOSS Shift & Location Management — visible to FOSS dept and Admin
    # Only add if the foss blueprint endpoint is registered (safety guard)
    try:
        from flask import current_app as _app  # noqa: PLC0415
        if "foss.index" in _app.view_functions:
            if dept == "FOSS" or role in (UserRole.SUPER_ADMIN.value, UserRole.ADMIN.value):
                all_items.insert(-1, {
                    "label": "FOSS — Shift & Location",
                    "icon": "bi-geo-fill",
                    "url_endpoint": "foss.index",
                    "roles": None,
                })
    except Exception:  # noqa: BLE001
        pass

    filtered = [
        item for item in all_items
        if item["roles"] is None or role in item["roles"]
    ]
    return {"nav_items": filtered}


def inject_enums() -> dict:
    """
    Inject enum classes into templates for use in select dropdowns
    and display logic without importing them per-template.

    Returns:
        Dictionary of enum classes available in all templates.
    """
    from app.constants.enums import (  # noqa: PLC0415
        AttendanceStatus,
        EmploymentType,
        Gender,
        LeaveStatus,
        LeaveType,
        PayrollStatus,
        UserRole,
        UserStatus,
    )

    return {
        "UserRole": UserRole,
        "UserStatus": UserStatus,
        "EmploymentType": EmploymentType,
        "Gender": Gender,
        "LeaveType": LeaveType,
        "LeaveStatus": LeaveStatus,
        "AttendanceStatus": AttendanceStatus,
        "PayrollStatus": PayrollStatus,
    }


def register_context_processors(app) -> None:
    """
    Register all context processors with the Flask application.

    Called from the application factory after creating the app.

    Args:
        app: The Flask application instance.
    """
    app.context_processor(inject_globals)
    app.context_processor(inject_user_context)
    app.context_processor(inject_navigation)
    app.context_processor(inject_enums)
