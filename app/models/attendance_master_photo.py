"""
app/models/attendance_master_photo.py
======================================
AttendanceMasterPhoto — stores proof photos for EmployeeMaster (I-prefix) employees.
Separate table from AttendancePhoto for E-prefix employees.
"""

from datetime import datetime
from sqlalchemy import DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.extensions.database import db


class AttendanceMasterPhoto(db.Model):
    """Proof photo for EmployeeMaster (I-prefix) attendance."""

    __tablename__ = "attendance_master_photos"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    # Link to AttendanceMaster record
    attendance_master_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("attendance_master.id"), nullable=False, unique=True, index=True
    )
    employee_master_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("employee_master.id"), nullable=False, index=True
    )

    # File path (kept for backward compatibility)
    file_path: Mapped[str] = mapped_column(String(255), nullable=True, default="")
    original_filename: Mapped[str] = mapped_column(String(255), nullable=True)
    file_size_bytes: Mapped[int] = mapped_column(Integer, nullable=True)
    mime_type: Mapped[str] = mapped_column(String(50), nullable=True)

    # Base64-encoded image data
    image_data: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Check-out photo
    checkout_image_data: Mapped[str | None] = mapped_column(Text, nullable=True)

    uploaded_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=datetime.utcnow
    )
    ip_address: Mapped[str | None] = mapped_column(String(45), nullable=True)

    # Relationships
    attendance_master = relationship("AttendanceMaster", backref="photo", uselist=False, lazy="select")
    employee_master = relationship("EmployeeMaster", foreign_keys=[employee_master_id], lazy="select")

    def __repr__(self) -> str:
        return f"<AttendanceMasterPhoto id={self.id} att_master={self.attendance_master_id}>"
