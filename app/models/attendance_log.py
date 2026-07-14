"""
app/models/attendance_log.py
==============================
AttendanceLog — immutable audit trail of every GPS attempt,
including rejected attempts. Never delete rows from this table.
"""

import datetime
from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.extensions.database import db


class AttendanceLog(db.Model):
    __tablename__ = "attendance_logs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    employee_id: Mapped[int] = mapped_column(Integer, ForeignKey("employees.id"), nullable=False, index=True)
    attendance_id: Mapped[int | None] = mapped_column(Integer, ForeignKey("attendance.id"), nullable=True)

    # Action: check_in | check_out | rejected_checkin | rejected_checkout
    action: Mapped[str] = mapped_column(String(30), nullable=False)

    # GPS data
    latitude: Mapped[float | None] = mapped_column(Float, nullable=True)
    longitude: Mapped[float | None] = mapped_column(Float, nullable=True)
    distance_metres: Mapped[float | None] = mapped_column(Float, nullable=True)
    within_radius: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    # Request metadata
    ip_address: Mapped[str | None] = mapped_column(String(45), nullable=True)
    user_agent: Mapped[str | None] = mapped_column(String(255), nullable=True)
    rejection_reason: Mapped[str | None] = mapped_column(String(255), nullable=True)

    timestamp: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=datetime.datetime.utcnow
    )

    employee = relationship("Employee", foreign_keys=[employee_id], lazy="select")

    def __repr__(self) -> str:
        return f"<AttendanceLog id={self.id} emp={self.employee_id} action={self.action!r}>"
