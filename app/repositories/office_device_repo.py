"""
app/repositories/office_device_repo.py
=========================================
Repository for OfficeDevice model operations.
"""

import logging
from typing import List, Optional

from app.extensions.database import db
from app.models.office_device import OfficeDevice

logger = logging.getLogger("attendance")


class OfficeDeviceRepository:
    """Repository for office device operations."""

    def get_all_active(self) -> List[OfficeDevice]:
        """Get all active office devices."""
        return db.session.query(OfficeDevice).filter_by(is_active=True).all()

    def get_all(self) -> List[OfficeDevice]:
        """Get all office devices (active and inactive)."""
        return db.session.query(OfficeDevice).all()

    def get_by_ip(self, ip_address: str) -> Optional[OfficeDevice]:
        """Get device by IP address."""
        return db.session.query(OfficeDevice).filter_by(ip_address=ip_address).first()

    def get_by_id(self, device_id: int) -> Optional[OfficeDevice]:
        """Get device by ID."""
        return db.session.query(OfficeDevice).filter_by(id=device_id).first()

    def create(self, ip_address: str, device_name: str, description: str = None) -> OfficeDevice:
        """Create a new office device."""
        device = OfficeDevice(
            ip_address=ip_address,
            device_name=device_name,
            description=description,
            is_active=True,
        )
        db.session.add(device)
        db.session.commit()
        logger.info(f"OfficeDevice created: ip={ip_address}, name={device_name}")
        return device

    def update(self, device: OfficeDevice) -> OfficeDevice:
        """Update an office device."""
        db.session.merge(device)
        db.session.commit()
        logger.info(f"OfficeDevice updated: ip={device.ip_address}")
        return device

    def delete(self, device_id: int) -> bool:
        """Delete an office device."""
        device = self.get_by_id(device_id)
        if device:
            db.session.delete(device)
            db.session.commit()
            logger.info(f"OfficeDevice deleted: id={device_id}")
            return True
        return False

    def is_ip_allowed(self, ip_address: str) -> bool:
        """Check if an IP address is allowed for attendance."""
        device = self.get_by_ip(ip_address)
        return device is not None and device.is_active

    def get_allowed_ips(self) -> List[str]:
        """Get list of all allowed IP addresses."""
        devices = self.get_all_active()
        return [d.ip_address for d in devices]
