"""
attendance/office_settings_service.py
========================================
OfficeSettings management service.

Single responsibility: CRUD operations for office geofence and
attendance policy configuration. Maintains an audit trail of every
settings change.

Only HR Managers and Admins should call these methods (enforce in routes).
"""

import logging
from datetime import datetime, timezone
from typing import Optional, Tuple

from app.extensions.database import db
from app.models.office_settings import OfficeSettings
from .repository import AttendanceRepository

logger = logging.getLogger("audit")
_repo = AttendanceRepository()


class OfficeSettingsService:
    """
    Manages creation, retrieval, and updates of OfficeSettings records.

    Each method validates its inputs before writing to the database.
    Every successful write is recorded in the audit logger.
    """

    def get_default(self) -> Optional[OfficeSettings]:
        """Return the default office settings record."""
        return _repo.get_default_office()

    def get_or_create_default(self) -> OfficeSettings:
        """
        Return the default office, creating it with sensible defaults if absent.

        Returns:
            OfficeSettings instance (always non-None).
        """
        office = _repo.get_default_office()
        if not office:
            office = OfficeSettings(
                name="Head Office",
                is_default=True,
                latitude=18.520430,
                longitude=73.856743,
                radius_metres=100,
            )
            _repo.save_office(office)
            logger.info("OFFICE_CREATED | id=%s | name=%s", office.id, office.name)
        return office

    def get_all(self) -> list:
        """Return all active office settings records."""
        return OfficeSettings.query.filter_by(is_deleted=False).order_by(OfficeSettings.name).all()

    def update(
        self,
        office_id: int,
        data: dict,
        updated_by: int,
    ) -> Tuple[bool, str]:
        """
        Apply a validated settings update to an OfficeSettings record.

        Args:
            office_id:   ID of the OfficeSettings to update.
            data:        Dictionary of fields to update.
            updated_by:  User ID of the HR user making the change.

        Returns:
            (success: bool, message: str)
        """
        office = OfficeSettings.query.filter_by(id=office_id, is_deleted=False).first()
        if not office:
            return False, "Office settings record not found."

        # Validate critical fields before applying
        ok, msg = self._validate(data)
        if not ok:
            return False, msg

        old_radius = office.radius_metres
        old_lat    = office.latitude
        old_lon    = office.longitude

        for key, value in data.items():
            if hasattr(office, key) and value is not None:
                setattr(office, key, value)

        office.updated_by = updated_by
        try:
            db.session.add(office)
            db.session.commit()

            logger.info(
                "OFFICE_UPDATED | id=%s | by_user=%s | radius: %s->%s | lat: %s->%s | lon: %s->%s",
                office_id, updated_by,
                old_radius, office.radius_metres,
                old_lat, office.latitude,
                old_lon, office.longitude,
            )
            return True, "Office settings updated successfully."
        except Exception as exc:  # noqa: BLE001
            db.session.rollback()
            logger.error("OFFICE_UPDATE_FAILED | id=%s | error=%s", office_id, exc)
            return False, "Failed to save settings. Please try again."

    def _validate(self, data: dict) -> Tuple[bool, str]:
        """Validate office settings data before writing."""
        import datetime

        lat = data.get("latitude")
        if lat is not None:
            try:
                lat = float(lat)
                if not (-90 <= lat <= 90):
                    return False, "Latitude must be between -90 and 90."
            except (ValueError, TypeError):
                return False, "Invalid latitude value."

        lon = data.get("longitude")
        if lon is not None:
            try:
                lon = float(lon)
                if not (-180 <= lon <= 180):
                    return False, "Longitude must be between -180 and 180."
            except (ValueError, TypeError):
                return False, "Invalid longitude value."

        radius = data.get("radius_metres")
        if radius is not None:
            try:
                radius = int(radius)
                if not (10 <= radius <= 5000):
                    return False, "Radius must be between 10 and 5000 metres."
            except (ValueError, TypeError):
                return False, "Invalid radius value."

        grace = data.get("grace_period_minutes")
        if grace is not None:
            try:
                grace = int(grace)
                if not (0 <= grace <= 60):
                    return False, "Grace period must be between 0 and 60 minutes."
            except (ValueError, TypeError):
                return False, "Invalid grace period."

        start = data.get("office_start_time")
        end   = data.get("office_end_time")
        if start and end and isinstance(start, datetime.time) and isinstance(end, datetime.time):
            if start >= end:
                return False, "Office start time must be before end time."

        return True, ""
