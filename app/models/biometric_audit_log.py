"""
app/models/biometric_audit_log.py
==================================
BiometricAuditLog — Immutable security audit trail of all facial biometric
enrollments, re-enrollments, verification attempts, presentation attacks,
and kiosk punches.
"""

from datetime import datetime
from sqlalchemy import Boolean, DateTime, Float, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.extensions.database import db


class BiometricAuditLog(db.Model):
    """Immutable audit log for biometric facial recognition events."""

    __tablename__ = "biometric_audit_logs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    employee_code: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    employee_master_id: Mapped[int | None] = mapped_column(Integer, nullable=True, index=True)
    employee_id: Mapped[int | None] = mapped_column(Integer, nullable=True, index=True)

    # Event Type: ENROLLMENT | RE_ENROLLMENT | VERIFIED_IDENTIFY | VERIFIED_PUNCH | SPOOF_ATTACK | FAILED_MATCH
    event_type: Mapped[str] = mapped_column(String(50), nullable=False, index=True)

    # Status: SUCCESS | REJECTED | BLOCKED | WARNING
    status: Mapped[str] = mapped_column(String(30), nullable=False, default="SUCCESS")

    confidence_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    euclidean_distance: Mapped[float | None] = mapped_column(Float, nullable=True)
    samples_count: Mapped[int] = mapped_column(Integer, nullable=False, default=1)

    # Authorization & Security
    authorized_by: Mapped[str | None] = mapped_column(String(100), nullable=True)
    ip_address: Mapped[str | None] = mapped_column(String(45), nullable=True)
    user_agent: Mapped[str | None] = mapped_column(String(255), nullable=True)

    # Detailed metadata (JSON string or reason)
    details: Mapped[str | None] = mapped_column(Text, nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=datetime.utcnow, index=True
    )

    def __repr__(self) -> str:
        return f"<BiometricAuditLog id={self.id} code={self.employee_code!r} event={self.event_type!r} status={self.status!r}>"
