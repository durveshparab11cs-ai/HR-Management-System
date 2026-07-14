"""
app/models/notification.py
============================
Notification model — in-app notifications for employees.
"""

from datetime import datetime
from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.extensions.database import db


class Notification(db.Model):
    """In-app notification record per user."""
    __tablename__ = "notifications"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), nullable=False, index=True)

    # Content
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    message: Mapped[str] = mapped_column(Text, nullable=False)
    category: Mapped[str] = mapped_column(String(50), nullable=False, default="info")
    # info | success | warning | danger | leave | attendance | payroll | system

    # Action link (optional)
    action_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    action_label: Mapped[str | None] = mapped_column(String(100), nullable=True)

    # State
    is_read: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, index=True)
    read_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=datetime.utcnow, index=True
    )

    # Source tracking
    triggered_by: Mapped[int | None] = mapped_column(Integer, ForeignKey("users.id"), nullable=True)

    user = relationship("User", foreign_keys=[user_id], lazy="select")

    @property
    def icon(self) -> str:
        icons = {
            "info":       "bi-info-circle-fill",
            "success":    "bi-check-circle-fill",
            "warning":    "bi-exclamation-triangle-fill",
            "danger":     "bi-x-circle-fill",
            "leave":      "bi-calendar-x-fill",
            "attendance": "bi-clock-fill",
            "payroll":    "bi-cash-stack",
            "system":     "bi-gear-fill",
        }
        return icons.get(self.category, "bi-bell-fill")

    @property
    def color(self) -> str:
        colors = {
            "info": "primary", "success": "success", "warning": "warning",
            "danger": "danger", "leave": "warning", "attendance": "info",
            "payroll": "success", "system": "secondary",
        }
        return colors.get(self.category, "primary")

    def __repr__(self) -> str:
        return f"<Notification id={self.id} user={self.user_id} read={self.is_read}>"
