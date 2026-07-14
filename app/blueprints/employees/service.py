"""
blueprints/employees/service.py
==================================
Employee service — all business logic for employee lifecycle management.
"""

import logging
import os
from datetime import datetime, timezone
from typing import Optional, Tuple

from flask import current_app
from werkzeug.datastructures import FileStorage

from app.constants.enums import UserRole, UserStatus
from app.extensions.database import db
from app.models.employee import Employee
from app.models.user import User
from app.utils.password_utils import generate_secure_token, generate_password
from app.utils.file_utils import save_file, delete_file
from app.utils.image_utils import generate_thumbnail
from .repository import EmployeeRepository
from .validators import validate_employee_code, validate_email_unique, validate_join_date, validate_phone

logger = logging.getLogger(__name__)
emp_repo = EmployeeRepository()


class EmployeeService:

    def create_employee(self, form_data: dict, photo: Optional[FileStorage] = None) -> Tuple[bool, str, Optional[Employee]]:
        """Create user account + employee profile in one transaction."""

        # Validate email uniqueness
        ok, msg = validate_email_unique(form_data["email"])
        if not ok:
            return False, msg, None

        # Always auto-generate employee code — never accept manual input
        code = emp_repo.get_next_employee_code()

        # Phone validation
        mobile = form_data.get("mobile", "").strip()
        if mobile:
            ok, msg = validate_phone(mobile)
            if not ok:
                return False, msg, None

        # Date validation
        join_date = form_data.get("date_joined")
        dob = form_data.get("date_of_birth")
        ok, msg = validate_join_date(join_date, dob)
        if not ok:
            return False, msg, None

        # Determine password
        plain_password = form_data.get("temp_password", "").strip()
        if not plain_password:
            plain_password = generate_password(12)

        try:
            # Create User
            user = User(
                email=form_data["email"].lower().strip(),
                username=self._generate_username(form_data["first_name"], form_data["last_name"]),
                first_name=form_data["first_name"].strip(),
                last_name=form_data["last_name"].strip(),
                role=form_data.get("role", UserRole.EMPLOYEE.value),
                status=UserStatus.ACTIVE.value,
                email_verified=True,
                created_by=form_data.get("created_by"),
            )
            user.set_password(plain_password)
            emp_repo.create_user(user)

            # Create Employee profile
            employee = Employee(
                user_id=user.id,
                employee_code=code,
                department=form_data.get("department", "").strip() or None,
                designation=form_data.get("designation", "").strip() or None,
                branch=form_data.get("branch", "").strip() or None,
                employment_type=form_data.get("employment_type", "full_time"),
                shift_name=form_data.get("shift_name", "").strip() or None,
                date_joined=join_date,
                date_of_birth=dob,
                gender=form_data.get("gender") or None,
                mobile=mobile or None,
                nationality=form_data.get("nationality", "").strip() or None,
                manager_id=form_data.get("manager_id") or None,
                created_by=form_data.get("created_by"),
            )

            # Handle photo
            if photo and photo.filename:
                try:
                    rel_path = save_file(photo, "profile_photos",
                                        max_bytes=5 * 1024 * 1024,
                                        allowed_extensions={"jpg", "jpeg", "png", "webp"})
                    employee.profile_photo = rel_path
                except Exception as e:
                    logger.warning("Photo upload failed during create: %s", e)

            emp_repo.create(employee)
            logger.info("Employee created: code=%s user_id=%s", code, user.id)
            return True, f"Employee {user.full_name} created. Temp password: {plain_password}", employee

        except Exception as e:
            db.session.rollback()
            logger.error("Employee create failed: %s", e, exc_info=True)
            return False, "Failed to create employee. Please try again.", None

    def update_employee(self, emp_id: int, form_data: dict, photo: Optional[FileStorage] = None) -> Tuple[bool, str]:
        employee = emp_repo.get_by_id(emp_id)
        if not employee:
            return False, "Employee not found."

        user = emp_repo.get_user_by_id(employee.user_id)
        if not user:
            return False, "Associated user account not found."

        # Email uniqueness
        new_email = form_data["email"].lower().strip()
        if new_email != user.email:
            ok, msg = validate_email_unique(new_email, exclude_user_id=user.id)
            if not ok:
                return False, msg

        # Phone
        mobile = form_data.get("mobile", "").strip()
        if mobile:
            ok, msg = validate_phone(mobile)
            if not ok:
                return False, msg

        # Dates
        join_date = form_data.get("date_joined")
        dob = form_data.get("date_of_birth")
        ok, msg = validate_join_date(join_date, dob)
        if not ok:
            return False, msg

        try:
            # Update User
            user.first_name = form_data["first_name"].strip()
            user.last_name = form_data["last_name"].strip()
            user.email = new_email
            user.role = form_data.get("role", user.role)
            user.status = form_data.get("status", user.status)
            emp_repo.update_user(user)

            # Update Employee
            employee.department = form_data.get("department", "").strip() or None
            employee.designation = form_data.get("designation", "").strip() or None
            employee.branch = form_data.get("branch", "").strip() or None
            employee.employment_type = form_data.get("employment_type", employee.employment_type)
            employee.shift_name = form_data.get("shift_name", "").strip() or None
            employee.date_joined = join_date
            employee.date_of_birth = dob
            employee.gender = form_data.get("gender") or None
            employee.mobile = mobile or None
            employee.nationality = form_data.get("nationality", "").strip() or None
            employee.personal_email = form_data.get("personal_email", "").strip() or None
            employee.address = form_data.get("address", "").strip() or None
            employee.emergency_contact_name = form_data.get("emergency_contact_name", "").strip() or None
            employee.emergency_contact_phone = form_data.get("emergency_contact_phone", "").strip() or None
            employee.manager_id = form_data.get("manager_id") or None

            # Photo update
            if photo and photo.filename:
                # Delete old photo
                if employee.profile_photo:
                    delete_file(employee.profile_photo)
                try:
                    rel_path = save_file(photo, "profile_photos",
                                        max_bytes=5 * 1024 * 1024,
                                        allowed_extensions={"jpg", "jpeg", "png", "webp"})
                    employee.profile_photo = rel_path
                except Exception as e:
                    logger.warning("Photo upload failed during update: %s", e)

            emp_repo.update(employee)
            logger.info("Employee updated: id=%s", emp_id)
            return True, "Employee profile updated successfully."

        except Exception as e:
            db.session.rollback()
            logger.error("Employee update failed: %s", e, exc_info=True)
            return False, "Failed to update employee."

    def reset_password(self, emp_id: int, new_password: Optional[str] = None) -> Tuple[bool, str]:
        employee = emp_repo.get_by_id(emp_id)
        if not employee:
            return False, "Employee not found."
        user = emp_repo.get_user_by_id(employee.user_id)
        if not user:
            return False, "User account not found."
        plain = new_password or generate_password(12)
        user.set_password(plain)
        user.failed_login_attempts = 0
        user.locked_until = None
        emp_repo.update_user(user)
        return True, f"Password reset. New password: {plain}"

    def toggle_account_status(self, emp_id: int, new_status: str) -> Tuple[bool, str]:
        employee = emp_repo.get_by_id(emp_id)
        if not employee:
            return False, "Employee not found."
        user = emp_repo.get_user_by_id(employee.user_id)
        if not user:
            return False, "User account not found."
        user.status = new_status
        emp_repo.update_user(user)
        return True, f"Account status set to {new_status.replace('_', ' ').title()}."

    def unlock_account(self, emp_id: int) -> Tuple[bool, str]:
        employee = emp_repo.get_by_id(emp_id)
        if not employee:
            return False, "Employee not found."
        user = emp_repo.get_user_by_id(employee.user_id)
        if not user:
            return False, "User account not found."
        user.failed_login_attempts = 0
        user.locked_until = None
        emp_repo.update_user(user)
        return True, "Account unlocked."

    def delete_employee(self, emp_id: int, deleted_by: int) -> Tuple[bool, str]:
        employee = emp_repo.get_by_id(emp_id)
        if not employee:
            return False, "Employee not found."
        user = emp_repo.get_user_by_id(employee.user_id)
        if user:
            user.status = UserStatus.INACTIVE.value
            emp_repo.update_user(user)
        emp_repo.soft_delete(employee, deleted_by)
        return True, "Employee removed."

    def get_managers_choices(self, exclude_id: Optional[int] = None) -> list:
        employees = emp_repo.get_all_active()
        choices = [(0, "— No Manager —")]
        for emp in employees:
            if emp.id != exclude_id:
                choices.append((emp.id, f"{emp.full_name} ({emp.employee_code})"))
        return choices

    def _generate_username(self, first: str, last: str) -> str:
        from app.models.user import User as _User
        base = f"{first.lower().strip()}.{last.lower().strip()}".replace(" ", "")
        username = base
        counter = 1
        while _User.query.filter_by(username=username).first():
            username = f"{base}{counter}"
            counter += 1
        return username
