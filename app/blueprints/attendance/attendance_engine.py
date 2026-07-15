"""
attendance/attendance_engine.py
================================
Core attendance computation logic.

IMPORTANT TIMEZONE HANDLING:
    - Check-in/out times are stored as naive UTC in SQLite.
    - Office start/end times (e.g. 10:00) are IST times configured by admin.
    - IST = UTC + 5:30, so to compare: convert office times to UTC by subtracting 5:30.
    - Example: office_start = 10:00 IST → 04:30 UTC
               grace_end   = 10:15 IST → 04:45 UTC
"""

from datetime import datetime, date, timedelta
from typing import Tuple

from app.models.office_settings import OfficeSettings
from app.models.attendance import Attendance
from .constants import AttendanceStatus

# IST offset from UTC: +5:30
IST_OFFSET = timedelta(hours=5, minutes=30)


def compute_check_in_meta(
    check_in_time: datetime,
    office: OfficeSettings,
) -> Tuple[bool, int]:
    """
    Determine whether a check-in is late.
    Returns (is_late, late_minutes).

    check_in_time: naive UTC (from DB)
    office.office_start_time: IST time configured by admin
    grace_period_minutes: configured grace (e.g. 15)

    Late if: check_in_UTC > (office_start_IST - 5:30) + grace_period
    """
    ci = _ensure_naive(check_in_time)

    # Convert office start time (IST) to UTC by subtracting 5:30
    office_start_utc = _naive_combine(ci.date(), office.office_start_time) - IST_OFFSET

    # Grace end in UTC
    grace_end_utc = office_start_utc + timedelta(minutes=office.grace_period_minutes)

    if ci > grace_end_utc:
        delta = ci - grace_end_utc
        return True, int(delta.total_seconds() / 60)
    return False, 0


def compute_check_out_meta(
    attendance: Attendance,
    check_out_time: datetime,
    office: OfficeSettings,
) -> dict:
    """
    Compute working hours, overtime, half-day on check-out.

    All times compared in naive UTC.
    office.office_end_time is IST — converted to UTC for comparison.
    working_minutes = actual time between check-in and check-out (in minutes).
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

    ci = _ensure_naive(check_in)
    co = _ensure_naive(check_out_time)

    # Actual working minutes (check-out minus check-in)
    working_minutes = max(0, int((co - ci).total_seconds() / 60))

    # Convert office end time (IST) to UTC
    office_end_utc = _naive_combine(attendance.date, office.office_end_time) - IST_OFFSET

    # Overtime: worked past office end time
    overtime_minutes = max(0, int((co - office_end_utc).total_seconds() / 60)) \
                       if co > office_end_utc else 0

    # Half-day: worked less than threshold (e.g. 240 min = 4 hours)
    is_half_day = working_minutes < office.half_day_threshold_minutes

    # Early leave: checked out before office end (minus grace)
    early_leave_threshold = office_end_utc - timedelta(minutes=office.grace_period_minutes)
    is_early_leave = co < early_leave_threshold

    status = AttendanceStatus.HALF_DAY if is_half_day else AttendanceStatus.PRESENT

    return {
        "working_minutes": working_minutes,
        "overtime_minutes": overtime_minutes,
        "is_half_day": is_half_day,
        "is_early_leave": is_early_leave,
        "status": status,
    }


def _naive_combine(d: date, t) -> datetime:
    """Combine a date and time object into a naive datetime."""
    return datetime(d.year, d.month, d.day, t.hour, t.minute, t.second)


def _ensure_naive(dt: datetime) -> datetime:
    """Strip timezone info. Converts aware datetime to naive UTC."""
    if dt.tzinfo is not None:
        utc_offset = dt.utcoffset()
        if utc_offset:
            dt = dt - utc_offset
        return dt.replace(tzinfo=None)
    return dt
