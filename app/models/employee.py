"""
app/models/employee.py
========================
Employee model — HR profile data, linked 1-to-1 with User.

Separation of concerns:
    User  — authentication, credentials, role, account status
    Employee — HR data: department, branch, shift, manager, personal info
"""

from datetime import date
from sqlalchemy import Date, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship, backref as sa_backref

from app.core.base_model import BaseModel
from app.constants.enums import EmploymentType, Gender


class Employee(BaseModel):
    __tablename__ = "employees"

    # ── Link to User account ─────────────────────────────────────────
    user_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id"), unique=True, nullable=False, index=True
    )

    # ── Identity ─────────────────────────────────────────────────────
    employee_code: Mapped[str] = mapped_column(String(20), unique=True, nullable=False, index=True)
    date_of_birth: Mapped[date | None] = mapped_column(Date, nullable=True)
    gender: Mapped[str | None] = mapped_column(String(20), nullable=True)
    nationality: Mapped[str | None] = mapped_column(String(50), nullable=True)
    national_id: Mapped[str | None] = mapped_column(String(50), nullable=True)

    # ── Contact ───────────────────────────────────────────────────────
    personal_email: Mapped[str | None] = mapped_column(String(254), nullable=True)
    mobile: Mapped[str | None] = mapped_column(String(20), nullable=True)
    address: Mapped[str | None] = mapped_column(Text, nullable=True)
    emergency_contact_name: Mapped[str | None] = mapped_column(String(100), nullable=True)
    emergency_contact_phone: Mapped[str | None] = mapped_column(String(20), nullable=True)

    # ── Employment ────────────────────────────────────────────────────
    department: Mapped[str | None] = mapped_column(String(100), nullable=True, index=True)
    designation: Mapped[str | None] = mapped_column(String(100), nullable=True)
    branch: Mapped[str | None] = mapped_column(String(100), nullable=True, index=True)
    employment_type: Mapped[str] = mapped_column(String(30), nullable=False, default=EmploymentType.FULL_TIME.value)
    date_joined: Mapped[date | None] = mapped_column(Date, nullable=True)
    date_of_leaving: Mapped[date | None] = mapped_column(Date, nullable=True)
    probation_end_date: Mapped[date | None] = mapped_column(Date, nullable=True)

    # ── Shift & Office ───────────────────────────────────────────────
    shift_name: Mapped[str | None] = mapped_column(String(50), nullable=True)
    office_settings_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("office_settings.id"), nullable=True
    )

    # ── Hierarchy ─────────────────────────────────────────────────────
    manager_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("employees.id"), nullable=True
    )

    # ── Photo ─────────────────────────────────────────────────────────
    profile_photo: Mapped[str | None] = mapped_column(String(255), nullable=True)

    # ── Relationships ─────────────────────────────────────────────────
    # uselist=False on the backref makes user.employee return a single
    # Employee object instead of an InstrumentedList — required because
    # user_id has unique=True (one User → one Employee, 1-to-1).
    user = relationship("User", backref=sa_backref("employee", uselist=False), lazy="joined", foreign_keys=[user_id])
    manager = relationship("Employee", remote_side="Employee.id", foreign_keys=[manager_id], lazy="select")
    office = relationship("OfficeSettings", foreign_keys=[office_settings_id], lazy="select")

    @property
    def full_name(self) -> str:
        return self.user.full_name if self.user else f"Employee #{self.id}"

    @property
    def email(self) -> str:
        return self.user.email if self.user else ""

    def __repr__(self) -> str:
        return f"<Employee id={self.id} code={self.employee_code!r}>"
