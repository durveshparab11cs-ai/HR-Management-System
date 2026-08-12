"""
app/models/office_device.py
============================
OfficeDevice model — stores IP addresses of allowed office computers
for check-in/check-out.

Allows restricting attendance marking to specific office devices only.
"""

from datetime import datetime
from sqlalchemy import Boolean, DateTime, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.core.base_model import BaseModel


class OfficeDevice(BaseModel):
    """Office computer/device allowed for attendance check-in/out."""
    __tablename__ = "office_devices"

    ip_address: Mapped[str] = mapped_column(String(45), nullable=False, unique=True, index=True)
    device_name: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True, index=True)
    
    # Track when device was added/modified
    last_checked: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    def __repr__(self) -> str:
        return f"<OfficeDevice ip={self.ip_address} name={self.device_name!r} active={self.is_active}>"

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        return {
            "id": self.id,
            "ip_address": self.ip_address,
            "device_name": self.device_name,
            "description": self.description,
            "is_active": self.is_active,
            "last_checked": self.last_checked.isoformat() if self.last_checked else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
