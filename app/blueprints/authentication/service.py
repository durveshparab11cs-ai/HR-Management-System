"""
blueprints/authentication/service.py
=======================================
Authentication service — all login/logout business logic.
Routes call this; never contain logic themselves.
"""

import logging
from datetime import datetime, timezone
from typing import Optional, Tuple

from flask import request
from flask_login import login_user, logout_user

from app.constants.enums import UserRole, UserStatus
from app.constants.limits import Limits
from app.models.user import User
from .repository import AuthRepository

logger = logging.getLogger("security")
auth_repo = AuthRepository()


class AuthService:

    def attempt_login(
        self,
        email: str,
        password: str,
        remember: bool = False,
    ) -> Tuple[bool, str, Optional[User]]:
        """
        Validate credentials and log the user in.

        Returns:
            (success, message, user_or_none)
        """
        ip = self._get_ip()
        ua = request.user_agent.string if request.user_agent else None

        user = auth_repo.get_by_email(email)

        if not user:
            auth_repo.record_login(None, email, False, ip, ua, "user_not_found")
            logger.warning("LOGIN_FAILED | email=%s | reason=user_not_found | ip=%s", email, ip)
            return False, "Invalid email or password.", None

        if user.is_deleted:
            auth_repo.record_login(user.id, email, False, ip, ua, "account_deleted")
            return False, "Account not found.", None

        if user.status == UserStatus.SUSPENDED.value:
            auth_repo.record_login(user.id, email, False, ip, ua, "account_suspended")
            return False, "Your account has been suspended. Contact HR.", None

        if user.status == UserStatus.INACTIVE.value:
            auth_repo.record_login(user.id, email, False, ip, ua, "account_inactive")
            return False, "Your account is inactive. Contact your administrator.", None

        if user.is_locked():
            auth_repo.record_login(user.id, email, False, ip, ua, "account_locked")
            return False, f"Account locked. Try again after {Limits.Password.LOCKOUT_DURATION_MINUTES} minutes.", None

        if not user.check_password(password):
            user.record_failed_login()
            auth_repo.update_user(user)
            auth_repo.record_login(user.id, email, False, ip, ua, "wrong_password")
            logger.warning("LOGIN_FAILED | user_id=%s | reason=wrong_password | ip=%s", user.id, ip)
            remaining = Limits.Password.MAX_FAILED_ATTEMPTS - user.failed_login_attempts
            if remaining <= 0:
                return False, "Account locked due to too many failed attempts.", None
            return False, f"Invalid password. {remaining} attempt(s) remaining.", None

        if user.status == UserStatus.PENDING_VERIFICATION.value:
            auth_repo.record_login(user.id, email, False, ip, ua, "email_not_verified")
            return False, "Please verify your email address before signing in.", None

        # Success
        user.record_successful_login(ip_address=ip)
        auth_repo.update_user(user)
        auth_repo.record_login(user.id, email, True, ip, ua)

        login_user(user, remember=remember)
        logger.info("LOGIN_SUCCESS | user_id=%s | role=%s | ip=%s", user.id, user.role, ip)
        return True, "Welcome back!", user

    def logout_current_user(self) -> None:
        logout_user()

    def register_first_user(
        self,
        first_name: str,
        last_name: str,
        email: str,
        password: str,
        role: str,
    ) -> Tuple[bool, str, Optional["Employee"]]:
        """
        Self-registration — creates both User and Employee profile.
        Anyone can register; the first registrant typically becomes admin.
        """
        from app.constants.enums import UserStatus  # noqa: PLC0415
        from app.models.user import User  # noqa: PLC0415
        from app.models.employee import Employee  # noqa: PLC0415
        from app.extensions.database import db  # noqa: PLC0415

        email = email.lower().strip()
        existing = auth_repo.get_by_email(email)
        if existing:
            return False, "This email is already registered. Please sign in.", None

        # First registered user becomes SUPER_ADMIN automatically
        from app.models.user import User as _User  # noqa: PLC0415
        is_first = _User.query.count() == 0

        actual_role = "super_admin" if is_first else role

        try:
            user = User(
                email=email,
                username=self._generate_username(first_name, last_name),
                first_name=first_name.strip(),
                last_name=last_name.strip(),
                role=actual_role,
                status=UserStatus.ACTIVE.value,
                email_verified=True,
            )
            user.set_password(password)
            auth_repo.create_user(user)

            # Create matching Employee profile
            from app.blueprints.employees.repository import EmployeeRepository  # noqa: PLC0415
            emp_repo = EmployeeRepository()
            code = emp_repo.get_next_employee_code()
            employee = Employee(
                user_id=user.id,
                employee_code=code,
                created_by=user.id,
            )
            db.session.add(employee)
            db.session.commit()

            role_label = "Super Admin" if is_first else role.replace("_", " ").title()
            msg = f"Account created as {role_label}. You can now sign in."
            logger.info("REGISTER | user_id=%s | role=%s | is_first=%s", user.id, actual_role, is_first)
            return True, msg, employee

        except Exception as e:
            db.session.rollback()
            logger.error("Registration failed: %s", e, exc_info=True)
            return False, "Registration failed. Please try again.", None

    def _generate_username(self, first: str, last: str) -> str:
        from app.models.user import User as _User  # noqa: PLC0415
        base = f"{first.lower().strip()}.{last.lower().strip()}".replace(" ", "")
        username = base
        counter = 1
        while _User.query.filter_by(username=username).first():
            username = f"{base}{counter}"
            counter += 1
        return username

    def get_dashboard_url(self, user: User) -> str:
        """Return the appropriate post-login redirect URL based on role."""
        role_map = {
            UserRole.SUPER_ADMIN.value: "/admin/",
            UserRole.ADMIN.value:       "/admin/",
            UserRole.HR_MANAGER.value:  "/admin/",
            UserRole.HR_STAFF.value:    "/admin/",
            UserRole.MANAGER.value:     "/dashboard/",
            UserRole.EMPLOYEE.value:    "/dashboard/",
        }
        return role_map.get(user.role, "/dashboard/")

    def _get_ip(self) -> str:
        xff = request.headers.get("X-Forwarded-For")
        if xff:
            return xff.split(",")[0].strip()
        return request.remote_addr or "unknown"
