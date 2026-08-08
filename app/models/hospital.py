"""
app/models/hospital.py
======================
Hospital Master - stores hospital locations with GPS coordinates
"""

import datetime
from sqlalchemy import DateTime, Float, Integer, String, Boolean
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.base_model import BaseModel


class Hospital(BaseModel):
    """Hospital master with GPS coordinates for attendance validation."""
    
    __tablename__ = "hospitals"

    # Hospital identification
    hospital_code: Mapped[str | None] = mapped_column(String(50), unique=True, nullable=True, index=True)
    hospital_name: Mapped[str] = mapped_column(String(200), nullable=False, index=True)
    
    # Location details
    location: Mapped[str | None] = mapped_column(String(200), nullable=True)
    address: Mapped[str | None] = mapped_column(String(500), nullable=True)
    city: Mapped[str | None] = mapped_column(String(100), nullable=True)
    state: Mapped[str | None] = mapped_column(String(100), nullable=True)
    
    # GPS coordinates
    latitude: Mapped[float] = mapped_column(Float, nullable=False)
    longitude: Mapped[float] = mapped_column(Float, nullable=False)
    
    # GPS validation settings
    allowed_radius_metres: Mapped[int] = mapped_column(Integer, nullable=False, default=100)
    
    # Status
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="Active")
    
    # Timestamps
    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=datetime.datetime.utcnow
    )
    updated_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=datetime.datetime.utcnow,
        onupdate=datetime.datetime.utcnow
    )
    
    # Relationships
    # employees relationship disabled until Employee foreign key is restored
    # employees = relationship("Employee", back_populates="hospital", lazy="select")
    
    def __setattr__(self, name, value):
        """Convert empty strings to NULL for hospital_code to avoid UNIQUE constraint violations."""
        if name == 'hospital_code' and value == '':
            value = None
        super().__setattr__(name, value)
    
    @property
    def employee_count(self) -> int:
        """Get count of employees assigned to this hospital."""
        # Note: Hospital-Employee relationship is not yet implemented
        # For now, query from Employee table directly if needed
        try:
            if hasattr(self, 'employees') and self.employees:
                return len(self.employees)
        except (AttributeError, TypeError):
            pass
        return 0
    
    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        return {
            "id": self.id,
            "hospital_code": self.hospital_code,
            "hospital_name": self.hospital_name,
            "location": self.location,
            "address": self.address,
            "city": self.city,
            "state": self.state,
            "latitude": self.latitude,
            "longitude": self.longitude,
            "allowed_radius_metres": self.allowed_radius_metres,
            "is_active": self.is_active,
            "status": self.status,
            "employee_count": self.employee_count,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
    
    def __repr__(self) -> str:
        return f"<Hospital id={self.id} name={self.hospital_name} lat={self.latitude} lng={self.longitude}>"
