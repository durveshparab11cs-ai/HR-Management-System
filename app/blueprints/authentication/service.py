"""
blueprints/authentication/service.py
=======================================
Authentication service — employee-code-based login and registration.

Login Flow:
    Employee Code + Password → find User via Employee table → verify password

Registration Flow:
    1. Check EmployeeMaster for the code
    2. Verify not already registered
    3. Create User record with name from master
    4. Create Employee profile linked to User
    5. Mark EmployeeMaster as registered
"""

import logging
from datetime import datetime, timedelta
from typing import Optional, Tuple

from flask import request
from flask_login import login_user, logout_user

from app.constants.enums import UserRole, UserStatus
from app.constants.limits import Limits
from app.extensions.database import db
from app.models.user import User
from .repository import AuthRepository

logger = logging.getLogger("security")
auth_repo = AuthRepository()


class AuthService:

    # ── Login ─────────────────────────────────────────────────────────

    def attempt_login(
        self,
        employee_code: str,
        password: str,
        department: str = "",
        remember: bool = False,
    ) -> Tuple[bool, str, Optional[User]]:
        """
        Authenticate using Employee Code + Password + Department.

        1. Look up User via Employee.employee_code
        2. Check account status / lock
        3. Verify password
        4. Validate department matches employee's assigned department
        5. Store department in session
        6. Record login history
        7. Call Flask-Login login_user()
        """
        from flask import session  # noqa: PLC0415
        from app.constants.enums import GLOBAL_ACCESS_DEPARTMENTS  # noqa: PLC0415

        ip = self._get_ip()
        ua = request.user_agent.string if request.user_agent else None
        code = employee_code.strip().upper()

        user = auth_repo.get_by_employee_code(code)

        if not user:
            auth_repo.record_login(None, code, False, ip, ua, "employee_code_not_found")
            logger.warning("LOGIN_FAILED | code=%s | reason=not_found | ip=%s", code, ip)
            return False, "Employee Code not found. Contact HR if you need assistance.", None

        if user.is_deleted:
            auth_repo.record_login(user.id, code, False, ip, ua, "account_deleted")
            return False, "Account not found.", None

        if user.status == UserStatus.SUSPENDED.value:
            auth_repo.record_login(user.id, code, False, ip, ua, "account_suspended")
            return False, "Your account has been suspended. Contact HR.", None

        if user.status == UserStatus.INACTIVE.value:
            auth_repo.record_login(user.id, code, False, ip, ua, "account_inactive")
            return False, "Your account is inactive. Contact your administrator.", None

        if user.is_locked():
            auth_repo.record_login(user.id, code, False, ip, ua, "account_locked")
            return False, f"Account locked. Try again after {Limits.Password.LOCKOUT_DURATION_MINUTES} minutes.", None

        if not user.check_password(password):
            user.record_failed_login()
            auth_repo.update_user(user)
            auth_repo.record_login(user.id, code, False, ip, ua, "wrong_password")
            logger.warning("LOGIN_FAILED | user_id=%s | reason=wrong_password | ip=%s", user.id, ip)
            remaining = Limits.Password.MAX_FAILED_ATTEMPTS - user.failed_login_attempts
            if remaining <= 0:
                return False, "Account locked due to too many failed attempts. Contact HR.", None
            return False, f"Incorrect password. {remaining} attempt(s) remaining.", None

        # ── Department validation ─────────────────────────────────────
        # Super admin and Admin bypass department check
        admin_roles = (UserRole.SUPER_ADMIN.value, UserRole.ADMIN.value)
        if user.role not in admin_roles and department:
            emp = getattr(user, "employee", None)
            emp_dept = (emp.department or "").strip() if emp else ""
            selected_dept = department.strip()

            if emp_dept and emp_dept.lower() != selected_dept.lower():
                auth_repo.record_login(user.id, code, False, ip, ua, "wrong_department")
                logger.warning(
                    "LOGIN_FAILED | user_id=%s | reason=wrong_department"
                    " | selected=%s | assigned=%s | ip=%s",
                    user.id, selected_dept, emp_dept, ip,
                )
                return (
                    False,
                    "You are not authorized to log in under the selected department.",
                    None,
                )

        # ── Success ───────────────────────────────────────────────────
        user.record_successful_login(ip_address=ip)
        auth_repo.update_user(user)
        auth_repo.record_login(user.id, code, True, ip, ua)
        login_user(user, remember=remember)

        # Store department in session for access-control filtering
        emp = getattr(user, "employee", None)
        assigned_dept = (emp.department or "").strip() if emp else ""
        # Admin/Super-Admin with global access store the selected dept or their own
        session["login_department"] = assigned_dept or department or ""

        # ── Auto-sync: if employee profile has no department, save it from login selection
        if emp and not emp.department and department:
            try:
                emp.department = department
                auth_repo.update_user(user)   # flush so it persists
                from app.extensions.database import db as _db  # noqa: PLC0415
                _db.session.commit()
                logger.info("AUTO_SET_DEPT | user=%s | dept=%s", user.id, department)
            except Exception as _exc:  # noqa: BLE001
                logger.warning("Could not auto-set dept: %s", _exc)

        logger.info(
            "LOGIN_SUCCESS | user_id=%s | code=%s | role=%s | dept=%s | ip=%s",
            user.id, code, user.role, session["login_department"], ip,
        )
        return True, f"Welcome back, {user.first_name}!", user

    # ── Registration ──────────────────────────────────────────────────

    def lookup_employee(self, employee_code: str) -> Tuple[bool, str, Optional[dict]]:
        """
        AJAX endpoint: look up employee name from master data.

        Returns:
            (found, message, data_or_None)
            data = {"name": str, "department": str, "is_registered": bool}
        """
        code = employee_code.strip().upper()
        master = auth_repo.get_master_by_code(code)

        if not master:
            return False, "Employee Code not found. Please contact HR.", None

        if master.is_registered:
            return False, "Account already exists. Please Sign In.", None

        return True, "Employee found.", {
            "name":        master.employee_name,
            "department":  master.department or "",
            "code":        master.employee_code,
        }

    def register_by_code(
        self,
        employee_code: str,
        password: str,
    ) -> Tuple[bool, str, Optional[User]]:
        """
        Complete self-registration for an employee using their code.

        1. Validate code exists in EmployeeMaster
        2. Prevent duplicate registration
        3. Create User record
        4. Create Employee profile
        5. Mark master as registered
        """
        from app.models.employee import Employee  # noqa: PLC0415

        code = employee_code.strip().upper()
        master = auth_repo.get_master_by_code(code)

        if not master:
            return False, "Employee Code not found. Please contact HR.", None

        if master.is_registered:
            return False, "Account already exists for this Employee Code. Please Sign In.", None

        # Check no User exists for this code (race condition guard)
        existing = auth_repo.get_by_employee_code(code)
        if existing:
            return False, "Account already exists. Please Sign In.", None

        # First user ever → SUPER_ADMIN, otherwise EMPLOYEE
        is_first = User.query.count() == 0
        role = UserRole.SUPER_ADMIN.value if is_first else UserRole.EMPLOYEE.value

        try:
            # Parse name from master (split on first space)
            name_parts = master.employee_name.strip().split(" ", 1)
            first_name = name_parts[0]
            last_name  = name_parts[1] if len(name_parts) > 1 else "."

            # Generate a unique email placeholder (not used for login)
            email = f"{code.lower().replace('-', '')}@hrms.internal"
            username = code.lower().replace("-", "")

            # Ensure uniqueness
            if User.query.filter_by(email=email).first():
                email = f"{email}.{datetime.utcnow().strftime('%s')}"
            if User.query.filter_by(username=username).first():
                username = f"{username}_{datetime.utcnow().strftime('%f')}"

            user = User(
                email=email,
                username=username,
                first_name=first_name,
                last_name=last_name,
                role=role,
                status=UserStatus.ACTIVE.value,
                email_verified=True,
            )
            user.set_password(password)
            auth_repo.create_user(user)

            # Create Employee profile
            employee = Employee(
                user_id=user.id,
                employee_code=code,
                department=master.department or None,
                designation=master.designation or None,
                created_by=user.id,
            )
            db.session.add(employee)
            db.session.commit()

            # Mark as registered
            auth_repo.mark_registered(master, user.id)

            role_label = "Super Admin" if is_first else "Employee"
            logger.info("REGISTERED | user_id=%s | code=%s | role=%s", user.id, code, role)
            return True, f"Account created as {role_label}. You can now sign in.", user

        except Exception as exc:
            db.session.rollback()
            logger.error("Registration failed | code=%s | error=%s", code, exc, exc_info=True)
            return False, "Registration failed. Please try again.", None

    # ── Forgot Password ───────────────────────────────────────────────

    def initiate_password_reset(self, employee_code: str) -> Tuple[bool, str]:
        """
        Generate a reset token for an employee (admin must deliver it).

        Returns (success, message_or_token).
        In production wire this to admin notification or SMS.
        For now returns the token so admin can copy it.
        """
        from app.utils.password_utils import generate_secure_token, hash_token  # noqa: PLC0415

        code = employee_code.strip().upper()
        user = auth_repo.get_by_employee_code(code)
        if not user:
            # Don't reveal whether code exists
            return False, "If this Employee Code is registered, a reset has been initiated."

        token     = generate_secure_token(32)
        token_hash = hash_token(token)
        expires   = datetime.utcnow() + timedelta(hours=2)
        auth_repo.set_reset_token(user, token_hash, expires)

        logger.info("PASSWORD_RESET_REQUESTED | user_id=%s | code=%s", user.id, code)
        # Return the raw token so admin can give it to the employee
        return True, token

    def reset_password(self, token: str, new_password: str) -> Tuple[bool, str]:
        """Validate a reset token and set new password."""
        from app.utils.password_utils import hash_token  # noqa: PLC0415

        token_hash = hash_token(token)
        user       = auth_repo.get_user_by_reset_token(token_hash)

        if not user:
            return False, "Invalid or expired reset link."

        if user.password_reset_expires_at and user.password_reset_expires_at < datetime.utcnow():
            return False, "Reset link has expired. Request a new one."

        user.set_password(new_password)
        user.failed_login_attempts = 0
        user.locked_until = None
        auth_repo.clear_reset_token(user)
        auth_repo.update_user(user)
        logger.info("PASSWORD_RESET_SUCCESS | user_id=%s", user.id)
        return True, "Password reset successfully. You can now sign in."

    # ── Logout ────────────────────────────────────────────────────────

    def logout_current_user(self) -> None:
        from flask import session  # noqa: PLC0415
        session.pop("login_department", None)
        logout_user()

    # ── Dashboard URL ─────────────────────────────────────────────────

    def get_dashboard_url(self, user: User) -> str:
        """Return the post-login URL based on role."""
        role_map = {
            UserRole.SUPER_ADMIN.value: "/admin/",
            UserRole.ADMIN.value:       "/admin/",
            UserRole.HR_MANAGER.value:  "/admin/",
            UserRole.HR_STAFF.value:    "/admin/",
            UserRole.MANAGER.value:     "/dashboard/",
            UserRole.EMPLOYEE.value:    "/dashboard/",
        }
        return role_map.get(user.role, "/dashboard/")

    # ── Helpers ───────────────────────────────────────────────────────

    def _get_ip(self) -> str:
        xff = request.headers.get("X-Forwarded-For", "")
        return xff.split(",")[0].strip() if xff else (request.remote_addr or "unknown")
