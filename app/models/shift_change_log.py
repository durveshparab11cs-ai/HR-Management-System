"""
app/models/shift_change_log.py
================================
Audit log for shift and office location changes made by FOSS.
One row per change event.
"""

from datetime import datetime
from sqlalchemy import DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.extensions.database import db


class ShiftChangeLog(db.Model):
    """Immutable history of every shift / office-location change."""

    __tablename__ = "shift_change_logs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    employee_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("employees.id"), nullable=False, index=True
    )
    changed_by_user_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id"), nullable=False
    )

    # ── Shift fields ──────────────────────────────────────────────────
    old_shift_name: Mapped[str | None] = mapped_column(String(100), nullable=True)
    new_shift_name: Mapped[str | None] = mapped_column(String(100), nullable=True)
    old_start_time: Mapped[str | None] = mapped_column(String(8), nullable=True)   # HH:MM
    new_start_time: Mapped[str | None] = mapped_column(String(8), nullable=True)
    old_end_time:   Mapped[str | None] = mapped_column(String(8), nullable=True)
    new_end_time:   Mapped[str | None] = mapped_column(String(8), nullable=True)
    old_grace_minutes: Mapped[int | None] = mapped_column(Integer, nullable=True)
    new_grace_minutes: Mapped[int | None] = mapped_column(Integer, nullable=True)

    # ── Office location fields ─────────────────────────────────────────
    old_office_name: Mapped[str | None] = mapped_column(String(100), nullable=True)
    new_office_name: Mapped[str | None] = mapped_column(String(100), nullable=True)
    old_latitude:   Mapped[str | None] = mapped_column(String(20), nullable=True)
    new_latitude:   Mapped[str | None] = mapped_column(String(20), nullable=True)
    old_longitude:  Mapped[str | None] = mapped_column(String(20), nullable=True)
    new_longitude:  Mapped[str | None] = mapped_column(String(20), nullable=True)
    old_radius:     Mapped[int | None] = mapped_column(Integer, nullable=True)
    new_radius:     Mapped[int | None] = mapped_column(Integer, nullable=True)

    # ── Meta ──────────────────────────────────────────────────────────
    change_type: Mapped[str] = mapped_column(
        String(20), nullable=False, default="shift"
    )  # "shift" | "location" | "both"
    reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    effective_date: Mapped[str | None] = mapped_column(String(12), nullable=True)
    changed_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, default=datetime.utcnow
    )

    # Relationships
    employee    = relationship("Employee", foreign_keys=[employee_id], lazy="select")
    changed_by  = relationship("User",     foreign_keys=[changed_by_user_id], lazy="select")

    def __repr__(self) -> str:
        return f"<ShiftChangeLog id={self.id} emp={self.employee_id} type={self.change_type}>"
