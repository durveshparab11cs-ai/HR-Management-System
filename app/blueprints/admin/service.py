"""
blueprints/admin/service.py
==============================
Admin service — office settings management.
"""

import logging
from typing import Optional, Tuple

from app.blueprints.attendance.repository import AttendanceRepository
from app.models.office_settings import OfficeSettings

logger = logging.getLogger(__name__)
_repo = AttendanceRepository()


class AdminService:

    def get_or_create_default_office(self) -> OfficeSettings:
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
        return office

    def update_office_settings(self, office_id: int, data: dict) -> Tuple[bool, str]:
        from app.extensions.database import db
        from app.models.office_settings import OfficeSettings
        office = OfficeSettings.query.get(office_id)
        if not office:
            return False, "Office settings not found."
        try:
            for key, val in data.items():
                if hasattr(office, key) and val is not None:
                    setattr(office, key, val)
            db.session.commit()
            logger.info("Office settings updated: id=%s", office_id)
            return True, "Office settings saved successfully."
        except Exception as e:
            from app.extensions.database import db
            db.session.rollback()
            logger.error("Office settings update failed: %s", e)
            return False, "Failed to save settings."
