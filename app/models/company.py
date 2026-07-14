"""
app/models/company.py
======================
Company, Department, Position, and Shift models.
"""

import datetime
from sqlalchemy import Boolean, ForeignKey, Integer, String, Text, Time
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.base_model import BaseModel
from app.extensions.database import db


class CompanyProfile(BaseModel):
    """Single-row company profile (singleton pattern — id=1 always)."""
    __tablename__ = "company_profile"

    name: Mapped[str] = mapped_column(String(200), nullable=False, default="My Company")
    logo: Mapped[str | None] = mapped_column(String(255), nullable=True)
    industry: Mapped[str | None] = mapped_column(String(100), nullable=True)
    website: Mapped[str | None] = mapped_column(String(255), nullable=True)
    phone: Mapped[str | None] = mapped_column(String(30), nullable=True)
    email: Mapped[str | None] = mapped_column(String(254), nullable=True)
    address: Mapped[str | None] = mapped_column(Text, nullable=True)
    city: Mapped[str | None] = mapped_column(String(100), nullable=True)
    state: Mapped[str | None] = mapped_column(String(100), nullable=True)
    country: Mapped[str] = mapped_column(String(100), nullable=False, default="India")
    pin_code: Mapped[str | None] = mapped_column(String(20), nullable=True)
    gstin: Mapped[str | None] = mapped_column(String(30), nullable=True)
    pan: Mapped[str | None] = mapped_column(String(20), nullable=True)
    founded_year: Mapped[int | None] = mapped_column(Integer, nullable=True)
    employee_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    timezone: Mapped[str] = mapped_column(String(50), nullable=False, default="Asia/Kolkata")
    currency: Mapped[str] = mapped_column(String(10), nullable=False, default="INR")
    currency_symbol: Mapped[str] = mapped_column(String(5), nullable=False, default="₹")

    def __repr__(self) -> str:
        return f"<CompanyProfile id={self.id} name={self.name!r}>"


class Department(BaseModel):
    """Company department (Engineering, HR, Finance, etc.)"""
    __tablename__ = "departments"

    name: Mapped[str] = mapped_column(String(100), nullable=False, unique=True)
    code: Mapped[str] = mapped_column(String(20), nullable=False, unique=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    head_employee_id: Mapped[int | None] = mapped_column(Integer, ForeignKey("employees.id"), nullable=True)
    parent_department_id: Mapped[int | None] = mapped_column(Integer, ForeignKey("departments.id"), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    color: Mapped[str] = mapped_column(String(7), nullable=False, default="#1a3c6e")

    head = relationship("Employee", foreign_keys=[head_employee_id], lazy="select")
    parent = relationship("Department", remote_side="Department.id", foreign_keys=[parent_department_id], lazy="select")

    def __repr__(self) -> str:
        return f"<Department id={self.id} name={self.name!r}>"


class Position(BaseModel):
    """Job position / designation within a department."""
    __tablename__ = "positions"

    title: Mapped[str] = mapped_column(String(100), nullable=False)
    code: Mapped[str] = mapped_column(String(20), nullable=False, unique=True)
    department_id: Mapped[int | None] = mapped_column(Integer, ForeignKey("departments.id"), nullable=True)
    grade: Mapped[str | None] = mapped_column(String(20), nullable=True)
    min_salary: Mapped[float | None] = mapped_column(db.Float, nullable=True)
    max_salary: Mapped[float | None] = mapped_column(db.Float, nullable=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

    department = relationship("Department", foreign_keys=[department_id], lazy="select")

    def __repr__(self) -> str:
        return f"<Position id={self.id} title={self.title!r}>"


class Shift(BaseModel):
    """Work shift schedule."""
    __tablename__ = "shifts"

    name: Mapped[str] = mapped_column(String(100), nullable=False)
    code: Mapped[str] = mapped_column(String(20), nullable=False, unique=True)
    start_time: Mapped[datetime.time] = mapped_column(Time, nullable=False, default=datetime.time(9, 0))
    end_time: Mapped[datetime.time] = mapped_column(Time, nullable=False, default=datetime.time(18, 0))
    grace_minutes: Mapped[int] = mapped_column(Integer, nullable=False, default=10)
    break_minutes: Mapped[int] = mapped_column(Integer, nullable=False, default=60)
    working_days: Mapped[str] = mapped_column(String(20), nullable=False, default="Mon-Fri")
    is_night_shift: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)

    @property
    def working_hours(self) -> float:
        """Total working hours per day excluding break."""
        import datetime as dt
        start = dt.datetime.combine(dt.date.today(), self.start_time)
        end   = dt.datetime.combine(dt.date.today(), self.end_time)
        if end <= start:
            end += dt.timedelta(days=1)
        total_mins = (end - start).total_seconds() / 60 - self.break_minutes
        return round(total_mins / 60, 2)

    def __repr__(self) -> str:
        return f"<Shift id={self.id} name={self.name!r}>"
