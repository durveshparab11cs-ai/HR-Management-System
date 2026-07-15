"""
blueprints/authentication/repository.py
==========================================
Authentication repository — database access for employee-code-based auth.
"""

from datetime import datetime
from typing import Optional

from app.extensions.database import db
from app.models.user import User
from app.models.employee_master import EmployeeMaster
from app.models.login_history import LoginHistory


class AuthRepository:

    # ── Employee Master ───────────────────────────────────────────────

    def get_master_by_code(self, employee_code: str) -> Optional[EmployeeMaster]:
        """Find an EmployeeMaster record by employee code (case-insensitive)."""
        return EmployeeMaster.query.filter_by(
            employee_code=employee_code.strip().upper(),
            is_active=True,
        ).first()

    def mark_registered(self, master: EmployeeMaster, user_id: int) -> EmployeeMaster:
        """Mark the EmployeeMaster record as registered after password setup."""
        master.is_registered = True
        master.user_id = user_id
        master.registered_at = datetime.utcnow()
        db.session.add(master)
        db.session.commit()
        return master

    # ── User ──────────────────────────────────────────────────────────

    def get_by_employee_code(self, employee_code: str) -> Optional[User]:
        """
        Find a User by their employee_code stored in the Employee table.
        Falls back to email-placeholder lookup if Employee record is missing.
        """
        from app.models.employee import Employee  # noqa: PLC0415
        code = employee_code.strip().upper()

        # Primary path: join User → Employee
        result = (
            db.session.query(User)
            .join(Employee, Employee.user_id == User.id)
            .filter(
                Employee.employee_code == code,
                Employee.is_deleted == False,
                User.is_deleted == False,
            )
            .first()
        )
        if result:
            return result

        # Fallback: look up by the internal email placeholder generated at registration
        # Format: {lowercase_code_no_dash}@hrms.internal  e.g. e2606026@hrms.internal
        placeholder = f"{code.lower().replace('-', '')}@hrms.internal"
        result = User.query.filter(
            User.email == placeholder,
            User.is_deleted == False,
        ).first()

        # If found via placeholder but Employee row is missing, create it now
        if result:
            existing_emp = Employee.query.filter_by(user_id=result.id, is_deleted=False).first()
            if not existing_emp:
                try:
                    emp = Employee(
                        user_id=result.id,
                        employee_code=code,
                        created_by=result.id,
                    )
                    db.session.add(emp)
                    db.session.commit()
                except Exception:
                    db.session.rollback()

        return result

    def get_by_email(self, email: str) -> Optional[User]:
        """Legacy email lookup — kept for existing admin accounts."""
        return User.query.filter_by(email=email.lower().strip(), is_deleted=False).first()

    def get_by_id(self, user_id: int) -> Optional[User]:
        return User.query.filter_by(id=user_id, is_deleted=False).first()

    def create_user(self, user: User) -> User:
        db.session.add(user)
        db.session.commit()
        return user

    def update_user(self, user: User) -> User:
        db.session.add(user)
        db.session.commit()
        return user

    # ── Login History ─────────────────────────────────────────────────

    def record_login(
        self,
        user_id: Optional[int],
        identifier: str,       # employee_code used instead of email
        success: bool,
        ip: Optional[str],
        user_agent: Optional[str],
        failure_reason: Optional[str] = None,
    ) -> LoginHistory:
        entry = LoginHistory(
            user_id=user_id,
            email_attempted=identifier[:254],   # reuse field for employee_code
            success=success,
            ip_address=ip,
            user_agent=user_agent[:255] if user_agent else None,
            failure_reason=failure_reason,
            timestamp=datetime.utcnow(),
        )
        db.session.add(entry)
        db.session.commit()
        return entry

    def get_login_history(self, user_id: int, limit: int = 20):
        return (
            LoginHistory.query
            .filter_by(user_id=user_id)
            .order_by(LoginHistory.timestamp.desc())
            .limit(limit)
            .all()
        )

    # ── Password Reset ────────────────────────────────────────────────

    def set_reset_token(self, user: User, token_hash: str, expires_at: datetime) -> User:
        user.password_reset_token = token_hash
        user.password_reset_expires_at = expires_at
        db.session.add(user)
        db.session.commit()
        return user

    def get_user_by_reset_token(self, token_hash: str) -> Optional[User]:
        return User.query.filter_by(
            password_reset_token=token_hash,
            is_deleted=False,
        ).first()

    def clear_reset_token(self, user: User) -> User:
        user.password_reset_token = None
        user.password_reset_expires_at = None
        db.session.add(user)
        db.session.commit()
        return user
