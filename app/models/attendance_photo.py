"""
app/models/attendance_photo.py
================================
AttendancePhoto — stores one proof photo per attendance check-in.

The photo is NOT used for biometric verification — it is a visual
proof record accessible to HR for audit purposes only.

Architecture note:
    Photo is stored in uploads/attendance/<employee_id>/<filename>
    This model stores only the relative path, not the binary.
"""

from datetime import datetime
from sqlalchemy import DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.extensions.database import db


class AttendancePhoto(db.Model):
    """Proof photo uploaded after successful GPS check-in."""

    __tablename__ = "attendance_photos"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    attendance_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("attendance.id"), nullable=False, unique=True, index=True
    )
    employee_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("employees.id"), nullable=False, index=True
    )

    # Relative path from UPLOAD_FOLDER — kept for backward compatibility
    file_path: Mapped[str] = mapped_column(String(255), nullable=False, default="")
    original_filename: Mapped[str] = mapped_column(String(255), nullable=True)
    file_size_bytes: Mapped[int] = mapped_column(Integer, nullable=True)
    mime_type: Mapped[str] = mapped_column(String(50), nullable=True)

    # Base64-encoded data URL — "data:image/jpeg;base64,..."
    # Stored in DB so photos survive Render redeploys (ephemeral filesystem).
    # Takes priority over file_path when present.
    image_data: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Check-out proof photo (stored separately in same row)
    checkout_image_data: Mapped[str | None] = mapped_column(Text, nullable=True)

    uploaded_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=datetime.utcnow
    )
    ip_address: Mapped[str | None] = mapped_column(String(45), nullable=True)

    # Relationships
    attendance = relationship("Attendance", backref="photo", uselist=False, lazy="select")
    employee   = relationship("Employee", foreign_keys=[employee_id], lazy="select")

    def __repr__(self) -> str:
        return f"<AttendancePhoto id={self.id} att={self.attendance_id}>"
