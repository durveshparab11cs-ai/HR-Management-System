"""
attendance/attendance_engine.py
================================
Core attendance computation logic.
Handles: late detection, overtime, half-day, working hours calculation.
Pure business logic — no HTTP, no Flask context.
"""

from datetime import datetime, date, timezone, timedelta
from typing import Optional, Tuple

from app.models.office_settings import OfficeSettings
from app.models.attendance import Attendance
from .constants import AttendanceStatus


def compute_check_in_meta(
    check_in_time: datetime,
    office: OfficeSettings,
) -> Tuple[bool, int]:
    """
    Determine whether a check-in is late and by how many minutes.

    Returns:
        (is_late: bool, late_minutes: int)
    """
    grace_end = _combine_date_time(
        check_in_time.date(),
        office.office_start_time,
    ) + timedelta(minutes=office.grace_period_minutes)

    if check_in_time > grace_end:
        delta = check_in_time - grace_end
        return True, int(delta.total_seconds() / 60)
    return False, 0


def compute_check_out_meta(
    attendance: Attendance,
    check_out_time: datetime,
    office: OfficeSettings,
) -> dict:
    """
    Compute working hours, overtime, half-day flag on check-out.

    Returns dict with keys:
        working_minutes, overtime_minutes, is_half_day,
        is_early_leave, status
    """
    check_in = attendance.check_in_time
    if not check_in:
        return {
            "working_minutes": 0,
            "overtime_minutes": 0,
            "is_half_day": False,
            "is_early_leave": False,
            "status": AttendanceStatus.PRESENT,
        }

    # Normalize to naive UTC for arithmetic
    ci = _ensure_naive(check_in)
    co = _ensure_naive(check_out_time)

    working_minutes = max(0, int((co - ci).total_seconds() / 60))

    # Office end for overtime calculation
    office_end_dt = _combine_date_time(attendance.date, office.office_end_time)
    office_end_naive = _ensure_naive(office_end_dt)

    overtime_minutes = max(0, int((co - office_end_naive).total_seconds() / 60)) if co > office_end_naive else 0

    # Half-day check
    is_half_day = working_minutes < office.half_day_threshold_minutes

    # Early leave check (checkout before office_end minus grace)
    early_leave_threshold = office_end_naive - timedelta(minutes=office.grace_period_minutes)
    is_early_leave = co < early_leave_threshold

    status = AttendanceStatus.HALF_DAY if is_half_day else AttendanceStatus.PRESENT

    return {
        "working_minutes": working_minutes,
        "overtime_minutes": overtime_minutes,
        "is_half_day": is_half_day,
        "is_early_leave": is_early_leave,
        "status": status,
    }


def _combine_date_time(d: date, t) -> datetime:
    return datetime(d.year, d.month, d.day, t.hour, t.minute, t.second, tzinfo=timezone.utc)


def _ensure_naive(dt: datetime) -> datetime:
    if dt.tzinfo is not None:
        dt = dt.astimezone(timezone.utc).replace(tzinfo=None)
    return dt
