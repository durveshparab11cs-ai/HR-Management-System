"""
attendance/service.py
=======================
Attendance service — orchestrates the full check-in / check-out workflow.

Responsibilities:
    - Delegate GPS validation to GPSService
    - Enforce duplicate-check prevention
    - Compute attendance metadata via attendance_engine
    - Persist records and audit logs
    - Delegate photo upload to PhotoService

Routes call this. This never touches HTTP directly.
"""

import logging
from datetime import datetime, date, timezone
from typing import Optional, Tuple

from flask import request

from app.extensions.database import db
from app.models.attendance import Attendance
from app.models.attendance_log import AttendanceLog
from app.models.employee import Employee
from werkzeug.datastructures import FileStorage

from .attendance_engine import compute_check_in_meta, compute_check_out_meta
from .constants import AttendanceStatus, LogAction
from .gps_service import GPSService
from .photo_service import PhotoService
from .repository import AttendanceRepository

logger = logging.getLogger("attendance")

_repo  = AttendanceRepository()
_gps   = GPSService()
_photo = PhotoService()


class AttendanceService:
    """Full check-in/out workflow with GPS verification, photo, and audit logging."""

    # ── Check In ─────────────────────────────────────────────────────

    def check_in(
        self,
        employee: Employee,
        lat_str: str,
        lon_str: str,
        accuracy_str: str = "",
    ) -> Tuple[bool, str, Optional[Attendance], Optional[dict]]:
        """
        Check-in workflow:
            1. GPS verification (Haversine via GPSService)
            2. Duplicate prevention
            3. Create / update Attendance record
            4. Audit log

        Returns:
            (success, message, attendance_or_None, gps_detail_or_None)
            gps_detail contains distance/office info for UI display on rejection.
        """
        today  = date.today()
        office = _repo.get_office_for_employee(employee)
        if not office:
            return False, "Office configuration not found. Contact HR.", None, None

        # GPS verification
        gps = _gps.verify(employee, office, lat_str, lon_str, accuracy_str, LogAction.CHECK_IN)

        if not gps.success:
            _repo.log_action(AttendanceLog(
                employee_id=employee.id,
                action=LogAction.REJECTED_CHECKIN,
                latitude=gps.lat,
                longitude=gps.lon,
                distance_metres=gps.distance_metres,
                within_radius=False,
                ip_address=self._get_ip(),
                user_agent=self._get_ua(),
                rejection_reason=gps.error,
            ))
            gps_detail = self._build_gps_detail(gps, office)
            return False, gps.error, None, gps_detail

        # Duplicate check
        existing = _repo.get_today(employee.id, today)
        if existing and existing.check_in_time:
            return False, "You have already checked in today.", None, None

        now = datetime.utcnow()
        is_late, late_minutes = compute_check_in_meta(now, office)

        if existing:
            attendance = existing
        else:
            attendance = Attendance(
                employee_id=employee.id,
                date=today,
                status=AttendanceStatus.PRESENT,
                created_by=employee.user_id,
            )

        attendance.check_in_time              = now
        attendance.check_in_latitude          = gps.lat
        attendance.check_in_longitude         = gps.lon
        attendance.check_in_distance_metres   = gps.distance_metres
        attendance.check_in_ip                = self._get_ip()
        attendance.check_in_device            = self._get_ua()
        attendance.is_late                    = is_late
        attendance.late_minutes               = late_minutes

        if existing:
            _repo.update(attendance)
        else:
            _repo.create(attendance)

        _repo.log_action(AttendanceLog(
            employee_id=employee.id,
            attendance_id=attendance.id,
            action=LogAction.CHECK_IN,
            latitude=gps.lat,
            longitude=gps.lon,
            distance_metres=gps.distance_metres,
            within_radius=True,
            ip_address=self._get_ip(),
            user_agent=self._get_ua(),
        ))

        import pytz  # noqa: PLC0415
        IST = pytz.timezone("Asia/Kolkata")
        ist_time = datetime.now(IST).strftime("%H:%M")
        late_msg = f" You are late by {late_minutes} min." if is_late else ""
        logger.info("CHECK_IN | emp=%s | dist=%.0fm | late=%s", employee.id, gps.distance_metres, is_late)
        gps_detail = self._build_gps_detail(gps, office)
        return True, f"Check-in recorded at {ist_time} IST.{late_msg}", attendance, gps_detail

    # ── Check Out ────────────────────────────────────────────────────

    def check_out(
        self,
        employee: Employee,
        lat_str: str,
        lon_str: str,
        accuracy_str: str = "",
    ) -> Tuple[bool, str, Optional[Attendance], Optional[dict]]:
        """
        Check-out workflow with working hours computation.

        Returns:
            (success, message, attendance_or_None, gps_detail_or_None)
        """
        today  = date.today()
        office = _repo.get_office_for_employee(employee)
        if not office:
            return False, "Office configuration not found.", None, None

        gps = _gps.verify(employee, office, lat_str, lon_str, accuracy_str, LogAction.CHECK_OUT)

        if not gps.success:
            _repo.log_action(AttendanceLog(
                employee_id=employee.id,
                action=LogAction.REJECTED_CHECKOUT,
                latitude=gps.lat,
                longitude=gps.lon,
                distance_metres=gps.distance_metres,
                within_radius=False,
                ip_address=self._get_ip(),
                user_agent=self._get_ua(),
                rejection_reason=gps.error,
            ))
            return False, gps.error, None, self._build_gps_detail(gps, office)

        attendance = _repo.get_today(employee.id, today)
        if not attendance or not attendance.check_in_time:
            return False, "No check-in found for today. Please check in first.", None, None
        if attendance.check_out_time:
            return False, "You have already checked out today.", None, None

        now  = datetime.utcnow()
        meta = compute_check_out_meta(attendance, now, office)

        attendance.check_out_time              = now
        attendance.check_out_latitude          = gps.lat
        attendance.check_out_longitude         = gps.lon
        attendance.check_out_distance_metres   = gps.distance_metres
        attendance.working_minutes             = meta["working_minutes"]
        attendance.overtime_minutes            = meta["overtime_minutes"]
        attendance.is_half_day                 = meta["is_half_day"]
        attendance.is_early_leave              = meta["is_early_leave"]
        attendance.status                      = meta["status"]
        _repo.update(attendance)

        _repo.log_action(AttendanceLog(
            employee_id=employee.id,
            attendance_id=attendance.id,
            action=LogAction.CHECK_OUT,
            latitude=gps.lat,
            longitude=gps.lon,
            distance_metres=gps.distance_metres,
            within_radius=True,
            ip_address=self._get_ip(),
            user_agent=self._get_ua(),
        ))

        h, m = divmod(meta["working_minutes"], 60)
        overtime = meta["overtime_minutes"]
        ot_msg = f" (+{overtime}m overtime)" if overtime > 0 else ""
        logger.info("CHECK_OUT | emp=%s | worked=%dh%dm", employee.id, h, m)
        return (
            True,
            f"Checked out. You worked {h}h {m}m today.{ot_msg}",
            attendance,
            self._build_gps_detail(gps, office),
        )

    # ── Photo upload ─────────────────────────────────────────────────

    def upload_photo(
        self,
        employee: Employee,
        file: FileStorage,
    ) -> Tuple[bool, str, Optional[str]]:
        """
        Save a proof photo for today's check-in.

        Args:
            employee: Employee making the upload.
            file:     FileStorage from request.files.

        Returns:
            (success, message, photo_url_or_None)
        """
        today = date.today()
        attendance = _repo.get_today(employee.id, today)
        if not attendance or not attendance.check_in_time:
            return False, "No check-in found for today. Check in first.", None

        ok, msg, photo = _photo.save_check_in_photo(attendance, employee.id, file)
        if not ok:
            return False, msg, None

        photo_url = _photo.get_photo_url(photo)
        return True, msg, photo_url

    # ── Today status ─────────────────────────────────────────────────

    def get_today_status(self, employee: Employee) -> dict:
        from app.models.attendance_photo import AttendancePhoto  # noqa: PLC0415
        today      = date.today()
        attendance = _repo.get_today(employee.id, today)
        office     = _repo.get_office_for_employee(employee)

        # Check photo using DB query — not the backref (which may be stale)
        has_photo = False
        if attendance and attendance.id:
            has_photo = AttendancePhoto.query.filter_by(
                attendance_id=attendance.id
            ).first() is not None

        # Photo can be uploaded after check-in OR after checkout (proof of day)
        can_upload = bool(
            attendance
            and attendance.check_in_time
            and not has_photo
        )

        return {
            "attendance":       attendance,
            "office":           office,
            "can_check_in":     not (attendance and attendance.check_in_time),
            "can_check_out":    bool(
                attendance and attendance.check_in_time and not attendance.check_out_time
            ),
            "can_upload_photo": can_upload,
            "has_photo":        has_photo,
        }

    # ── Helpers ──────────────────────────────────────────────────────

    def _build_gps_detail(self, gps, office) -> dict:
        """Build a dict of GPS/distance detail for JSON responses."""
        return {
            "employee_lat":     gps.lat,
            "employee_lon":     gps.lon,
            "accuracy":         gps.accuracy,
            "distance_metres":  gps.distance_metres,
            "office_lat":       office.latitude if office else None,
            "office_lon":       office.longitude if office else None,
            "allowed_radius":   office.radius_metres if office else None,
            "within_radius":    gps.within_radius,
        }

    def _get_ip(self) -> str:
        xff = request.headers.get("X-Forwarded-For", "")
        return xff.split(",")[0].strip() if xff else (request.remote_addr or "unknown")

    def _get_ua(self) -> str:
        return (request.user_agent.string or "")[:255]
