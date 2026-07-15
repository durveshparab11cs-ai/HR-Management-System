"""
app/models/employee_master.py
================================
EmployeeMaster — pre-seeded employee records imported from Excel.

This table is the SOURCE OF TRUTH for valid employee codes.
An employee can only REGISTER if their code exists here.

Lifecycle:
    1. HR imports Excel → rows created here with is_registered=False
    2. Employee visits /auth/register, enters their code
    3. System finds the record here, shows their name
    4. Employee sets password → User record created, is_registered=True
    5. Login uses employee_code + password

This is separate from the Employee (HR profile) table so that
employee master data can be imported before full HR profiles are created.
"""

from datetime import datetime
from sqlalchemy import Boolean, DateTime, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.extensions.database import db


class EmployeeMaster(db.Model):
    """Pre-seeded employee code registry from HR's Excel master data."""

    __tablename__ = "employee_master"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    employee_code: Mapped[str] = mapped_column(
        String(30),
        unique=True,
        nullable=False,
        index=True,
        doc="Unique employee code (e.g. E-2603028). Imported from Excel."
    )

    employee_name: Mapped[str] = mapped_column(
        String(200),
        nullable=False,
        doc="Full employee name from Excel."
    )

    department: Mapped[str | None] = mapped_column(String(100), nullable=True)
    designation: Mapped[str | None] = mapped_column(String(100), nullable=True)

    # Registration state
    is_registered: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        index=True,
        doc="True once the employee has completed self-registration and set a password."
    )

    # Linked User (populated after registration)
    user_id: Mapped[int | None] = mapped_column(Integer, nullable=True)

    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

    imported_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        default=datetime.utcnow,
    )

    registered_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    def __repr__(self) -> str:
        return f"<EmployeeMaster code={self.employee_code!r} name={self.employee_name!r} registered={self.is_registered}>"
