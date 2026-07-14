"""
app/core/security.py
=====================
Role-based access control (RBAC) decorators and permission helpers.

Provides decorators to protect routes based on user roles, replacing
scattered manual role-checks with a declarative, reusable API.

Usage:
    from app.core.security import roles_required, admin_required

    @employees_bp.route("/create")
    @login_required
    @roles_required(UserRole.HR_MANAGER, UserRole.ADMIN)
    def create_employee():
        ...
"""

import functools
import logging
from typing import Callable

from flask import abort, flash, redirect, request, url_for
from flask_login import current_user

from app.constants.enums import UserRole
from app.constants.messages import Messages

logger = logging.getLogger(__name__)


def roles_required(*roles: UserRole) -> Callable:
    """
    Decorator that restricts a route to users with specific roles.

    Must be applied AFTER @login_required so current_user is populated.

    Args:
        *roles: One or more UserRole enum values that are permitted.

    Returns:
        Decorated view function.

    Example:
        @login_required
        @roles_required(UserRole.ADMIN, UserRole.HR_MANAGER)
        def protected_view():
            ...
    """
    def decorator(fn: Callable) -> Callable:
        @functools.wraps(fn)
        def wrapper(*args, **kwargs):
            if not current_user.is_authenticated:
                return redirect(url_for("authentication.login", next=request.url))

            user_role = getattr(current_user, "role", None)
            if user_role not in roles:
                logger.warning(
                    "Authorization denied | user_id=%s | role=%s | endpoint=%s | required=%s",
                    current_user.id,
                    user_role,
                    request.endpoint,
                    [r.value for r in roles],
                )
                # Log a security event
                security_logger = logging.getLogger("security")
                security_logger.warning(
                    "UNAUTHORIZED_ACCESS | user_id=%s | role=%s | ip=%s | endpoint=%s",
                    current_user.id,
                    user_role,
                    request.remote_addr,
                    request.endpoint,
                )
                abort(403)
            return fn(*args, **kwargs)
        return wrapper
    return decorator


def admin_required(fn: Callable) -> Callable:
    """
    Convenience decorator restricting a route to SUPER_ADMIN and ADMIN only.

    Shortcut for @roles_required(UserRole.SUPER_ADMIN, UserRole.ADMIN).
    """
    @functools.wraps(fn)
    def wrapper(*args, **kwargs):
        if not current_user.is_authenticated:
            return redirect(url_for("authentication.login", next=request.url))

        user_role = getattr(current_user, "role", None)
        if user_role not in (UserRole.SUPER_ADMIN, UserRole.ADMIN):
            abort(403)
        return fn(*args, **kwargs)
    return wrapper


def hr_required(fn: Callable) -> Callable:
    """
    Convenience decorator for HR staff and above.

    Permits: SUPER_ADMIN, ADMIN, HR_MANAGER, HR_STAFF.
    """
    @functools.wraps(fn)
    def wrapper(*args, **kwargs):
        if not current_user.is_authenticated:
            return redirect(url_for("authentication.login", next=request.url))

        allowed = (UserRole.SUPER_ADMIN, UserRole.ADMIN, UserRole.HR_MANAGER, UserRole.HR_STAFF)
        user_role = getattr(current_user, "role", None)
        if user_role not in allowed:
            abort(403)
        return fn(*args, **kwargs)
    return wrapper


def manager_required(fn: Callable) -> Callable:
    """
    Convenience decorator for managers and above.

    Permits: SUPER_ADMIN, ADMIN, HR_MANAGER, MANAGER.
    """
    @functools.wraps(fn)
    def wrapper(*args, **kwargs):
        if not current_user.is_authenticated:
            return redirect(url_for("authentication.login", next=request.url))

        allowed = (UserRole.SUPER_ADMIN, UserRole.ADMIN, UserRole.HR_MANAGER, UserRole.MANAGER)
        user_role = getattr(current_user, "role", None)
        if user_role not in allowed:
            abort(403)
        return fn(*args, **kwargs)
    return wrapper


def owner_or_admin_required(get_owner_id_fn: Callable) -> Callable:
    """
    Decorator that allows access only to the resource owner or admins.

    Useful for allowing employees to edit their own profile while
    restricting them from editing others'.

    Args:
        get_owner_id_fn: Callable(*args, **kwargs) → int
            A function that extracts the owner's user_id from the view
            function's arguments. Called with the same args/kwargs as the view.

    Example:
        @login_required
        @owner_or_admin_required(lambda *a, **kw: kw["user_id"])
        def edit_profile(user_id):
            ...
    """
    def decorator(fn: Callable) -> Callable:
        @functools.wraps(fn)
        def wrapper(*args, **kwargs):
            if not current_user.is_authenticated:
                return redirect(url_for("authentication.login", next=request.url))

            owner_id = get_owner_id_fn(*args, **kwargs)
            user_role = getattr(current_user, "role", None)
            is_admin = user_role in (UserRole.SUPER_ADMIN, UserRole.ADMIN)

            if not is_admin and current_user.id != owner_id:
                abort(403)
            return fn(*args, **kwargs)
        return wrapper
    return decorator


def permission_required(permission: str) -> Callable:
    """
    Decorator for fine-grained permission checking.

    Checks whether the current user has a specific permission string.
    Requires the User model to implement a has_permission(permission) method.

    Args:
        permission: Permission string (e.g., 'payroll.approve').

    Returns:
        Decorated view function.
    """
    def decorator(fn: Callable) -> Callable:
        @functools.wraps(fn)
        def wrapper(*args, **kwargs):
            if not current_user.is_authenticated:
                return redirect(url_for("authentication.login", next=request.url))

            if not hasattr(current_user, "has_permission") or \
               not current_user.has_permission(permission):
                flash(Messages.Auth.UNAUTHORIZED, "danger")
                abort(403)
            return fn(*args, **kwargs)
        return wrapper
    return decorator
