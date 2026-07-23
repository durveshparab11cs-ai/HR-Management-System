"""
app/models/office_settings.py
================================
OfficeSettings model — stores configurable office/branch parameters
including GPS geofence coordinates, attendance timing rules, and policies.

One row per branch/office location. The default branch (id=1) applies
to all employees who have no explicit branch assignment.
"""

from sqlalchemy import Boolean, Float, Integer, String, Text, Time
from sqlalchemy.orm import Mapped, mapped_column
import datetime

from app.core.base_model import BaseModel


class OfficeSettings(BaseModel):
    __tablename__ = "office_settings"

    # ── Identity ────────────────────────────────────────────────────
    name: Mapped[str] = mapped_column(String(100), nullable=False, default="Head Office")
    address: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_default: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

    # ── GPS Geofence ────────────────────────────────────────────────
    latitude: Mapped[float] = mapped_column(Float, nullable=False, default=18.520430)
    longitude: Mapped[float] = mapped_column(Float, nullable=False, default=73.856743)
    radius_metres: Mapped[int] = mapped_column(Integer, nullable=False, default=100)
    # Minimum GPS accuracy required from browser before allowing attendance.
    # 50m is a good default — rejects clearly poor WiFi-based locations.
    # NOTE: Uses try/except in property for backward compat with existing DB rows.
    _min_gps_accuracy_metres: Mapped[int] = mapped_column(
        "min_gps_accuracy_metres",
        Integer, nullable=True, default=50
    )

    @property
    def min_gps_accuracy_metres(self) -> int:
        """Safe access — returns 50 if column not yet in DB."""
        try:
            val = self._min_gps_accuracy_metres
            return val if val is not None else 50
        except Exception:
            return 50

    @min_gps_accuracy_metres.setter
    def min_gps_accuracy_metres(self, value: int) -> None:
        self._min_gps_accuracy_metres = value

    # ── Office Timing ───────────────────────────────────────────────
    office_start_time: Mapped[datetime.time] = mapped_column(
        Time, nullable=False, default=datetime.time(9, 0)
    )
    office_end_time: Mapped[datetime.time] = mapped_column(
        Time, nullable=False, default=datetime.time(18, 0)
    )
    grace_period_minutes: Mapped[int] = mapped_column(Integer, nullable=False, default=10)
    half_day_threshold_minutes: Mapped[int] = mapped_column(Integer, nullable=False, default=300)  # 5 hours
    overtime_threshold_minutes: Mapped[int] = mapped_column(Integer, nullable=False, default=30)

    # ── Policy ──────────────────────────────────────────────────────
    allow_remote_checkin: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    selfie_required: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    auto_checkout_enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    auto_checkout_time: Mapped[datetime.time | None] = mapped_column(Time, nullable=True)

    def __repr__(self) -> str:
        return f"<OfficeSettings id={self.id} name={self.name!r}>"
