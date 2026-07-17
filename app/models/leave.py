"""
app/models/leave.py
=====================
LeaveType, LeaveRequest, HalfDayRequest, EarlyLeaveRequest models.
"""

import datetime
from sqlalchemy import Boolean, Date, DateTime, ForeignKey, Integer, String, Text, Time
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.base_model import BaseModel
from app.extensions.database import db


class LeaveType(db.Model):
    """Configurable leave types (Casual, Sick, Paid, LOP, CompOff…)"""
    __tablename__ = "leave_types"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(50), nullable=False, unique=True)
    code: Mapped[str] = mapped_column(String(10), nullable=False, unique=True)
    max_days_per_year: Mapped[int] = mapped_column(Integer, nullable=False, default=12)
    carry_forward: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    requires_document: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    is_paid: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    color: Mapped[str] = mapped_column(String(7), nullable=False, default="#1a3c6e")
    description: Mapped[str | None] = mapped_column(Text, nullable=True)

    def __repr__(self) -> str:
        return f"<LeaveType {self.code!r}>"


class LeaveRequest(BaseModel):
    """Employee leave application with approval workflow."""
    __tablename__ = "leave_requests"

    employee_id: Mapped[int] = mapped_column(Integer, ForeignKey("employees.id"), nullable=False, index=True)
    leave_type_id: Mapped[int] = mapped_column(Integer, ForeignKey("leave_types.id"), nullable=False)

    start_date: Mapped[datetime.date] = mapped_column(Date, nullable=False)
    end_date: Mapped[datetime.date] = mapped_column(Date, nullable=False)
    total_days: Mapped[float] = mapped_column(Integer, nullable=False, default=1)

    reason: Mapped[str] = mapped_column(Text, nullable=False)
    attachment: Mapped[str | None] = mapped_column(String(255), nullable=True)

    # Workflow
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="pending", index=True)
    # pending | approved | rejected | cancelled | withdrawn

    applied_on: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=datetime.datetime.utcnow
    )
    reviewed_by: Mapped[int | None] = mapped_column(Integer, ForeignKey("users.id"), nullable=True)
    reviewed_on: Mapped[datetime.datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    reviewer_comment: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Reporting Manager
    reporting_manager_code: Mapped[str | None] = mapped_column(String(30), nullable=True, index=True)
    reporting_manager_name: Mapped[str | None] = mapped_column(String(200), nullable=True)

    # Relationships
    employee = relationship("Employee", foreign_keys=[employee_id], lazy="joined")
    leave_type = relationship("LeaveType", foreign_keys=[leave_type_id], lazy="joined")
    reviewer = relationship("User", foreign_keys=[reviewed_by], lazy="select")

    @property
    def duration_display(self) -> str:
        days = self.total_days
        return f"{days} day{'s' if days != 1 else ''}"

    def __repr__(self) -> str:
        return f"<LeaveRequest id={self.id} emp={self.employee_id} status={self.status!r}>"


class HalfDayRequest(BaseModel):
    """Half-day work request — morning or afternoon."""
    __tablename__ = "half_day_requests"

    employee_id: Mapped[int] = mapped_column(Integer, ForeignKey("employees.id"), nullable=False, index=True)
    date: Mapped[datetime.date] = mapped_column(Date, nullable=False)
    half_type: Mapped[str] = mapped_column(String(10), nullable=False)  # morning | afternoon
    reason: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="pending", index=True)
    applied_on: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=datetime.datetime.utcnow
    )
    reviewed_by: Mapped[int | None] = mapped_column(Integer, ForeignKey("users.id"), nullable=True)
    reviewed_on: Mapped[datetime.datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    reviewer_comment: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Reporting Manager fields
    reporting_manager_code: Mapped[str | None] = mapped_column(String(30), nullable=True, index=True)
    reporting_manager_name: Mapped[str | None] = mapped_column(String(200), nullable=True)

    employee = relationship("Employee", foreign_keys=[employee_id], lazy="joined")
    reviewer = relationship("User", foreign_keys=[reviewed_by], lazy="select")

    def __repr__(self) -> str:
        return f"<HalfDayRequest id={self.id} emp={self.employee_id} date={self.date}>"


class EarlyLeaveRequest(BaseModel):
    """Early leave request — leave before office closing time."""
    __tablename__ = "early_leave_requests"

    employee_id: Mapped[int] = mapped_column(Integer, ForeignKey("employees.id"), nullable=False, index=True)
    date: Mapped[datetime.date] = mapped_column(Date, nullable=False)
    requested_leave_time: Mapped[datetime.time] = mapped_column(Time, nullable=False)
    reason: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="pending", index=True)
    applied_on: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=datetime.datetime.utcnow
    )
    reviewed_by: Mapped[int | None] = mapped_column(Integer, ForeignKey("users.id"), nullable=True)
    reviewed_on: Mapped[datetime.datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    reviewer_comment: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Reporting Manager fields
    reporting_manager_code: Mapped[str | None] = mapped_column(String(30), nullable=True, index=True)
    reporting_manager_name: Mapped[str | None] = mapped_column(String(200), nullable=True)

    employee = relationship("Employee", foreign_keys=[employee_id], lazy="joined")
    reviewer = relationship("User", foreign_keys=[reviewed_by], lazy="select")

    def __repr__(self) -> str:
        return f"<EarlyLeaveRequest id={self.id} emp={self.employee_id} date={self.date}>"
