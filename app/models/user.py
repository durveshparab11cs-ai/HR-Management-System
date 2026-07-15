"""
app/models/user.py
===================
User model — authentication, authorization, and account management.

This is the central identity model for the entire system. Every other
module references users by foreign key.

Inherits from BaseModel providing:
    - id, created_at, updated_at, is_deleted, deleted_at (audit columns)
    - save(), soft_delete(), to_dict() convenience methods

Implements Flask-Login's UserMixin interface for session management.

Security practices:
    - Passwords are NEVER stored in plaintext.
    - bcrypt hash is stored; comparison uses check_password_hash().
    - Failed login attempts are tracked with automatic lockout.
    - Last login IP and timestamp are recorded for audit.
"""

from datetime import datetime, timezone

from flask_login import UserMixin
from sqlalchemy import Boolean, DateTime, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.core.base_model import BaseModel
from app.constants.enums import UserRole, UserStatus
from app.constants.limits import Limits


class User(UserMixin, BaseModel):
    """
    Represents a system user (employee, HR, admin, etc.).

    A User is the authentication identity. The Employee model (built later)
    holds HR-specific profile data and references back to User via foreign key.
    This separation allows non-employee admin accounts to exist cleanly.
    """

    __tablename__ = "users"

    # ------------------------------------------------------------------
    # Identity Fields
    # ------------------------------------------------------------------
    email: Mapped[str] = mapped_column(
        String(Limits.String.EMAIL),
        unique=True,
        nullable=False,
        index=True,
        doc="Unique email address used as login credential.",
    )

    username: Mapped[str] = mapped_column(
        String(Limits.String.SHORT),
        unique=True,
        nullable=False,
        index=True,
        doc="Unique username for display and mentions.",
    )

    first_name: Mapped[str] = mapped_column(
        String(Limits.String.SHORT),
        nullable=False,
        doc="User's first name.",
    )

    last_name: Mapped[str] = mapped_column(
        String(Limits.String.SHORT),
        nullable=False,
        doc="User's last name.",
    )

    # ------------------------------------------------------------------
    # Authentication Fields
    # ------------------------------------------------------------------
    password_hash: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        doc="bcrypt hash of the user's password. Never store plaintext.",
    )

    role: Mapped[str] = mapped_column(
        String(Limits.String.SHORT),
        nullable=False,
        default=UserRole.EMPLOYEE.value,
        doc="User's system role (maps to UserRole enum).",
    )

    status: Mapped[str] = mapped_column(
        String(Limits.String.SHORT),
        nullable=False,
        default=UserStatus.PENDING_VERIFICATION.value,
        doc="Account lifecycle status.",
    )

    # ------------------------------------------------------------------
    # Security Tracking Fields
    # ------------------------------------------------------------------
    failed_login_attempts: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
        doc="Count of consecutive failed login attempts since last success.",
    )

    locked_until: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        doc="Timestamp until which this account is locked out.",
    )

    last_login_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        doc="UTC timestamp of the most recent successful login.",
    )

    last_login_ip: Mapped[str | None] = mapped_column(
        String(Limits.String.IP_ADDRESS),
        nullable=True,
        doc="IP address from the most recent successful login.",
    )

    password_changed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        doc="UTC timestamp when the password was last changed.",
    )

    # ------------------------------------------------------------------
    # Verification Fields
    # ------------------------------------------------------------------
    email_verified: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        doc="True if the user's email address has been verified.",
    )

    email_verified_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        doc="UTC timestamp when email was verified.",
    )

    verification_token: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
        doc="One-time email verification token (hashed).",
    )

    password_reset_token: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
        doc="Password reset token (hashed). Cleared after use.",
    )

    password_reset_expires_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        doc="Expiry timestamp for the password reset token.",
    )

    # ------------------------------------------------------------------
    # Profile Fields
    # ------------------------------------------------------------------
    profile_photo: Mapped[str | None] = mapped_column(
        String(Limits.String.LONG),
        nullable=True,
        doc="Relative path to the user's profile photo.",
    )

    phone: Mapped[str | None] = mapped_column(
        String(Limits.String.PHONE),
        nullable=True,
        doc="User's primary phone number.",
    )

    # ------------------------------------------------------------------
    # Flask-Login Interface
    # ------------------------------------------------------------------

    @property
    def is_active(self) -> bool:
        """
        Flask-Login requires this. Returns True only for active, unlocked accounts.
        """
        if self.status != UserStatus.ACTIVE.value:
            return False
        if self.locked_until:
            locked = self.locked_until
            if locked.tzinfo is not None:
                locked = locked.replace(tzinfo=None)
            if locked > datetime.utcnow():
                return False
        return not self.is_deleted

    def get_id(self) -> str:
        """Flask-Login requires this. Returns the user's PK as a string."""
        return str(self.id)

    # ------------------------------------------------------------------
    # Password Methods
    # ------------------------------------------------------------------

    def set_password(self, plaintext_password: str) -> None:
        """
        Hash and store a plaintext password using bcrypt.

        Args:
            plaintext_password: The user's new password in plaintext.
        """
        from werkzeug.security import generate_password_hash  # noqa: PLC0415
        self.password_hash = generate_password_hash(plaintext_password)
        self.password_changed_at = datetime.utcnow()

    def check_password(self, plaintext_password: str) -> bool:
        """
        Verify a plaintext password against the stored bcrypt hash.

        Args:
            plaintext_password: The password to verify.

        Returns:
            True if the password matches, False otherwise.
        """
        from werkzeug.security import check_password_hash  # noqa: PLC0415
        return check_password_hash(self.password_hash, plaintext_password)

    # ------------------------------------------------------------------
    # Account Lock Methods
    # ------------------------------------------------------------------

    def record_failed_login(self) -> None:
        """Increment failed login counter and lock if threshold exceeded."""
        from datetime import timedelta  # noqa: PLC0415
        self.failed_login_attempts += 1
        if self.failed_login_attempts >= Limits.Password.MAX_FAILED_ATTEMPTS:
            # Store as naive UTC — SQLite does not preserve tzinfo
            self.locked_until = datetime.utcnow() + timedelta(
                minutes=Limits.Password.LOCKOUT_DURATION_MINUTES
            )

    def record_successful_login(self, ip_address: str | None = None) -> None:
        """Reset failed counter and record login metadata."""
        self.failed_login_attempts = 0
        self.locked_until = None
        self.last_login_at = datetime.utcnow()
        self.last_login_ip = ip_address

    def is_locked(self) -> bool:
        """Return True if this account is currently locked."""
        if self.locked_until is None:
            return False
        locked = self.locked_until
        # Normalize both sides to naive UTC for SQLite compatibility
        if locked.tzinfo is not None:
            locked = locked.replace(tzinfo=None)
        return locked > datetime.utcnow()

    # ------------------------------------------------------------------
    # Role / Permission Helpers
    # ------------------------------------------------------------------

    def has_role(self, *roles: UserRole) -> bool:
        """
        Check whether the user holds any of the given roles.

        Args:
            *roles: UserRole enum values to check against.

        Returns:
            True if the user's role matches any of the provided roles.
        """
        return self.role in [r.value for r in roles]

    def has_permission(self, permission: str) -> bool:
        """
        Fine-grained permission check.

        Currently implemented as role-based; extend with a permissions
        table when fine-grained ACL is required.

        Args:
            permission: Dot-notation permission string (e.g., 'payroll.approve').

        Returns:
            True if the user's role grants the permission.
        """
        # Super admin has every permission
        if self.role == UserRole.SUPER_ADMIN.value:
            return True

        # Permission matrix — extend as modules are added
        _role_permissions: dict[str, set[str]] = {
            UserRole.ADMIN.value: {
                "employees.view", "employees.create", "employees.update", "employees.delete",
                "leave.approve", "leave.view_all",
                "attendance.view_all", "attendance.update",
                "payroll.view", "payroll.approve",
                "reports.view", "reports.export",
                "settings.view", "settings.update",
            },
            UserRole.HR_MANAGER.value: {
                "employees.view", "employees.create", "employees.update",
                "leave.approve", "leave.view_all",
                "attendance.view_all", "attendance.update",
                "payroll.view",
                "reports.view", "reports.export",
            },
            UserRole.HR_STAFF.value: {
                "employees.view", "employees.create",
                "leave.view_all",
                "attendance.view_all",
            },
            UserRole.MANAGER.value: {
                "employees.view",
                "leave.approve",
                "attendance.view_team",
                "reports.view",
            },
            UserRole.EMPLOYEE.value: {
                "leave.apply", "leave.view_own",
                "attendance.mark_own", "attendance.view_own",
            },
        }

        role_perms = _role_permissions.get(self.role, set())
        return permission in role_perms

    # ------------------------------------------------------------------
    # Display Helpers
    # ------------------------------------------------------------------

    @property
    def full_name(self) -> str:
        """Return the user's full name."""
        return f"{self.first_name} {self.last_name}".strip()

    @property
    def display_role(self) -> str:
        """Return a human-readable role label."""
        return self.role.replace("_", " ").title()

    def __repr__(self) -> str:
        return f"<User id={self.id} email={self.email!r} role={self.role!r}>"
