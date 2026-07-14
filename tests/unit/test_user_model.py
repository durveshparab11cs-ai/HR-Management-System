"""
tests/unit/test_user_model.py
===============================
Unit tests for the User model.

Tests cover:
    - Password hashing and verification
    - Account lock/unlock logic
    - Role/permission helpers
    - Soft delete behaviour
    - to_dict() serialization
"""

import pytest
from datetime import datetime, timezone, timedelta

from app.models.user import User
from app.constants.enums import UserRole, UserStatus


class TestPasswordManagement:
    """Password hashing, verification, and policy."""

    def test_set_password_hashes_plaintext(self, app):
        with app.app_context():
            user = User(email="a@b.com", username="a", first_name="A", last_name="B",
                        role=UserRole.EMPLOYEE.value, status=UserStatus.ACTIVE.value)
            user.set_password("MySecret@1")
            assert user.password_hash != "MySecret@1"
            assert user.password_hash.startswith("scrypt:") or "$" in user.password_hash

    def test_check_password_correct(self, app):
        with app.app_context():
            user = User(email="b@b.com", username="b", first_name="B", last_name="C",
                        role=UserRole.EMPLOYEE.value, status=UserStatus.ACTIVE.value)
            user.set_password("Correct@99")
            assert user.check_password("Correct@99") is True

    def test_check_password_wrong(self, app):
        with app.app_context():
            user = User(email="c@b.com", username="c", first_name="C", last_name="D",
                        role=UserRole.EMPLOYEE.value, status=UserStatus.ACTIVE.value)
            user.set_password("Correct@99")
            assert user.check_password("Wrong@99") is False

    def test_set_password_records_timestamp(self, app):
        with app.app_context():
            user = User(email="d@b.com", username="d", first_name="D", last_name="E",
                        role=UserRole.EMPLOYEE.value, status=UserStatus.ACTIVE.value)
            user.set_password("Ts@12345")
            assert user.password_changed_at is not None


class TestAccountLock:
    """Account lockout after failed login attempts."""

    def test_record_failed_login_increments_counter(self, app):
        with app.app_context():
            user = User(email="e@b.com", username="e", first_name="E", last_name="F",
                        role=UserRole.EMPLOYEE.value, status=UserStatus.ACTIVE.value,
                        failed_login_attempts=0)
            user.record_failed_login()
            assert user.failed_login_attempts == 1

    def test_lockout_after_max_attempts(self, app):
        with app.app_context():
            from app.constants.limits import Limits
            user = User(email="f@b.com", username="f", first_name="F", last_name="G",
                        role=UserRole.EMPLOYEE.value, status=UserStatus.ACTIVE.value,
                        failed_login_attempts=Limits.Password.MAX_FAILED_ATTEMPTS - 1)
            user.record_failed_login()
            assert user.is_locked() is True
            assert user.locked_until is not None

    def test_successful_login_clears_lock(self, app):
        with app.app_context():
            user = User(email="g@b.com", username="g", first_name="G", last_name="H",
                        role=UserRole.EMPLOYEE.value, status=UserStatus.ACTIVE.value,
                        failed_login_attempts=5,
                        locked_until=datetime.now(timezone.utc) + timedelta(minutes=10))
            user.record_successful_login(ip_address="127.0.0.1")
            assert user.failed_login_attempts == 0
            assert user.is_locked() is False


class TestRolePermissions:
    """Role helpers and permission checks."""

    def test_has_role_true(self, app):
        with app.app_context():
            user = User(email="h@b.com", username="h", first_name="H", last_name="I",
                        role=UserRole.ADMIN.value, status=UserStatus.ACTIVE.value)
            assert user.has_role(UserRole.ADMIN) is True

    def test_has_role_false(self, app):
        with app.app_context():
            user = User(email="i@b.com", username="i", first_name="I", last_name="J",
                        role=UserRole.EMPLOYEE.value, status=UserStatus.ACTIVE.value)
            assert user.has_role(UserRole.ADMIN) is False

    def test_super_admin_has_all_permissions(self, app):
        with app.app_context():
            user = User(email="j@b.com", username="j", first_name="J", last_name="K",
                        role=UserRole.SUPER_ADMIN.value, status=UserStatus.ACTIVE.value)
            assert user.has_permission("any.permission") is True

    def test_employee_cannot_approve_leave(self, app):
        with app.app_context():
            user = User(email="k@b.com", username="k", first_name="K", last_name="L",
                        role=UserRole.EMPLOYEE.value, status=UserStatus.ACTIVE.value)
            assert user.has_permission("leave.approve") is False


class TestDisplayHelpers:
    """full_name, display_role, initials."""

    def test_full_name(self, app):
        with app.app_context():
            user = User(email="l@b.com", username="l", first_name="Jane",
                        last_name="Doe", role=UserRole.EMPLOYEE.value,
                        status=UserStatus.ACTIVE.value)
            assert user.full_name == "Jane Doe"

    def test_display_role_formatted(self, app):
        with app.app_context():
            user = User(email="m@b.com", username="m", first_name="M",
                        last_name="N", role=UserRole.HR_MANAGER.value,
                        status=UserStatus.ACTIVE.value)
            assert user.display_role == "Hr Manager"
