"""
app/models/attendance_master.py
===============================
AttendanceMaster — daily attendance record for EmployeeMaster (I-prefix) employees.
"""

from datetime import date, datetime
from sqlalchemy import Boolean, Date, DateTime, Float, ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.extensions.database import db


class AttendanceMaster(db.Model):
    """Daily attendance record for EmployeeMaster (I-prefix) employees."""

    __tablename__ = "attendance_master"
    __table_args__ = (
        UniqueConstraint("employee_master_id", "date", name="uq_attendance_master_emp_date"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    employee_master_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("employee_master.id"), nullable=False, index=True
    )
    employee_code: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    date: Mapped[date] = mapped_column(Date, nullable=False, index=True)

    # Status
    status: Mapped[str] = mapped_column(String(30), nullable=False, default="present")

    # Check In
    check_in_time: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    check_in_latitude: Mapped[float | None] = mapped_column(Float, nullable=True)
    check_in_longitude: Mapped[float | None] = mapped_column(Float, nullable=True)
    check_in_accuracy: Mapped[float | None] = mapped_column(Float, nullable=True)

    # Check Out
    check_out_time: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    check_out_latitude: Mapped[float | None] = mapped_column(Float, nullable=True)
    check_out_longitude: Mapped[float | None] = mapped_column(Float, nullable=True)
    check_out_accuracy: Mapped[float | None] = mapped_column(Float, nullable=True)

    # Biometric Face Verification
    face_verified: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    face_match_score: Mapped[float | None] = mapped_column(Float, nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=datetime.utcnow
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    # Relationships
    employee_master = relationship("EmployeeMaster", backref="attendance_records", lazy="select", foreign_keys=[employee_master_id])

    @property
    def working_hours_display(self) -> str:
        if self.check_in_time and self.check_out_time:
            try:
                diff = (self.check_out_time - self.check_in_time).total_seconds()
                if diff > 0:
                    mins = int(diff // 60)
                    h, m = divmod(mins, 60)
                    if h > 0:
                        return f"{h}h {m}m" if m > 0 else f"{h}h"
                    return f"{m}m" if m > 0 else "< 1m"
            except Exception:
                pass
        return "—"

    def __repr__(self) -> str:
        return f"<AttendanceMaster id={self.id} emp_master={self.employee_master_id} date={self.date}>"
