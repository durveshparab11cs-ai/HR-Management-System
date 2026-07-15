"""
app/models/attendance.py
==========================
Attendance — daily attendance record per employee.
One row per employee per date.
"""

import datetime
from sqlalchemy import Boolean, Date, DateTime, Float, ForeignKey, Integer, String, Time
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.base_model import BaseModel


class Attendance(BaseModel):
    __tablename__ = "attendance"

    # ── Core ──────────────────────────────────────────────────────────
    employee_id: Mapped[int] = mapped_column(Integer, ForeignKey("employees.id"), nullable=False, index=True)
    date: Mapped[datetime.date] = mapped_column(Date, nullable=False, index=True)

    # ── Check In ──────────────────────────────────────────────────────
    check_in_time: Mapped[datetime.datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    check_in_latitude: Mapped[float | None] = mapped_column(Float, nullable=True)
    check_in_longitude: Mapped[float | None] = mapped_column(Float, nullable=True)
    check_in_accuracy: Mapped[float | None] = mapped_column(Float, nullable=True)
    check_in_distance_metres: Mapped[float | None] = mapped_column(Float, nullable=True)
    check_in_ip: Mapped[str | None] = mapped_column(String(45), nullable=True)
    check_in_device: Mapped[str | None] = mapped_column(String(255), nullable=True)
    # ── Photo proof ───────────────────────────────────────────────────
    check_in_selfie: Mapped[str | None] = mapped_column(String(255), nullable=True)
    # Deprecated: use AttendancePhoto model for photo storage.
    # Retained for backward compatibility with existing rows.

    # ── Check Out ─────────────────────────────────────────────────────
    check_out_time: Mapped[datetime.datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    check_out_latitude: Mapped[float | None] = mapped_column(Float, nullable=True)
    check_out_longitude: Mapped[float | None] = mapped_column(Float, nullable=True)
    check_out_accuracy: Mapped[float | None] = mapped_column(Float, nullable=True)
    check_out_distance_metres: Mapped[float | None] = mapped_column(Float, nullable=True)

    # ── Computed ──────────────────────────────────────────────────────
    working_minutes: Mapped[int | None] = mapped_column(Integer, nullable=True)
    overtime_minutes: Mapped[int | None] = mapped_column(Integer, nullable=True)
    late_minutes: Mapped[int | None] = mapped_column(Integer, nullable=True)
    is_late: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    is_half_day: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    is_early_leave: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    # ── Status ────────────────────────────────────────────────────────
    status: Mapped[str] = mapped_column(String(30), nullable=False, default="present", index=True)
    # Values: present | absent | half_day | on_leave | holiday | weekend | work_from_home

    # ── Regularisation ────────────────────────────────────────────────
    is_regularised: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    regularised_by: Mapped[int | None] = mapped_column(Integer, ForeignKey("users.id"), nullable=True)
    regularisation_reason: Mapped[str | None] = mapped_column(String(255), nullable=True)

    # ── Relationships ─────────────────────────────────────────────────
    employee = relationship("Employee", backref="attendance_records", lazy="joined", foreign_keys=[employee_id])

    @property
    def working_hours_display(self) -> str:
        if not self.working_minutes:
            return "—"
        h, m = divmod(self.working_minutes, 60)
        return f"{h}h {m}m"

    def __repr__(self) -> str:
        return f"<Attendance id={self.id} emp={self.employee_id} date={self.date} status={self.status!r}>"
