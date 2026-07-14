"""
app/models/login_history.py
=============================
LoginHistory — records every authentication attempt (success or failure)
for security auditing and account activity display.
"""

from datetime import datetime
from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.extensions.database import db


class LoginHistory(db.Model):
    __tablename__ = "login_history"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int | None] = mapped_column(Integer, ForeignKey("users.id"), nullable=True, index=True)
    email_attempted: Mapped[str] = mapped_column(String(254), nullable=False)
    success: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    ip_address: Mapped[str | None] = mapped_column(String(45), nullable=True)
    user_agent: Mapped[str | None] = mapped_column(String(255), nullable=True)
    failure_reason: Mapped[str | None] = mapped_column(String(100), nullable=True)
    timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)

    user = relationship("User", backref="login_history", foreign_keys=[user_id], lazy="select")

    def __repr__(self) -> str:
        return f"<LoginHistory id={self.id} user_id={self.user_id} success={self.success}>"
