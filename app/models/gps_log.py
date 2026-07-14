"""
app/models/gps_log.py
=======================
GPSLog — records every geolocation data point received from the browser,
regardless of success/failure. Used for security auditing.
"""

import datetime
from sqlalchemy import DateTime, Float, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.extensions.database import db


class GPSLog(db.Model):
    __tablename__ = "gps_logs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    employee_id: Mapped[int | None] = mapped_column(Integer, ForeignKey("employees.id"), nullable=True)
    latitude: Mapped[float | None] = mapped_column(Float, nullable=True)
    longitude: Mapped[float | None] = mapped_column(Float, nullable=True)
    accuracy_metres: Mapped[float | None] = mapped_column(Float, nullable=True)
    distance_from_office: Mapped[float | None] = mapped_column(Float, nullable=True)
    action: Mapped[str] = mapped_column(String(30), nullable=False)   # check_in | check_out
    ip_address: Mapped[str | None] = mapped_column(String(45), nullable=True)
    timestamp: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=datetime.datetime.utcnow
    )

    def __repr__(self) -> str:
        return f"<GPSLog id={self.id} user={self.user_id} action={self.action!r}>"
