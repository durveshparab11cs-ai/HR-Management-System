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

SHIFT INTEGRATION:
    - Each employee can have a custom shift assigned via Shift Change Management.
    - If employee has a shift assignment for the attendance date, use shift timings.
    - Otherwise, fall back to office settings default shift.
"""

from datetime import datetime, date, timedelta
from typing import Tuple, Optional

from app.models.office_settings import OfficeSettings
from app.models.attendance import Attendance
from .constants import AttendanceStatus

# IST offset from UTC: +5:30
IST_OFFSET = timedelta(hours=5, minutes=30)


def get_employee_shift_for_date(employee_id: int, attendance_date: date) -> Optional[dict]:
    """
    Get employee's active shift for a specific date.
    
    Returns:
        Dict with shift timings or None (fallback to office settings)
    """
    try:
        from app.blueprints.shift_change.service import ShiftChangeService
        service = ShiftChangeService()
        return service.get_shift_for_attendance(employee_id, attendance_date)
    except Exception:
        # If shift_change module not available or error, return None
        return None


def compute_check_in_meta(
    check_in_time: datetime,
    office: OfficeSettings,
    employee_id: int = None,
    attendance_date: date = None,
) -> Tuple[bool, int]:
    """
    Determine whether a check-in is late.
    Returns (is_late, late_minutes).

    check_in_time: naive UTC (from DB)
    office.office_start_time: IST time configured by admin
    grace_period_minutes: configured grace (e.g. 15)
    employee_id: Optional - to lookup employee-specific shift
    attendance_date: Optional - date to check shift assignment

    Late if: check_in_UTC > (shift_start_IST - 5:30) + grace_period
    """
    ci = _ensure_naive(check_in_time)
    
    # Try to get employee-specific shift
    shift_start_time = office.office_start_time
    grace_period = office.grace_period_minutes
    
    if employee_id and attendance_date:
        shift_info = get_employee_shift_for_date(employee_id, attendance_date)
        if shift_info:
            shift_start_time = shift_info.get("start_time", office.office_start_time)
            # Use shift-specific grace if available (for future enhancement)
            # grace_period = shift_info.get("grace_period", office.grace_period_minutes)

    # Convert shift start time (IST) to UTC by subtracting 5:30
    shift_start_utc = _naive_combine(ci.date(), shift_start_time) - IST_OFFSET

    # Grace end in UTC
    grace_end_utc = shift_start_utc + timedelta(minutes=grace_period)

    if ci > grace_end_utc:
        delta = ci - grace_end_utc
        return True, int(delta.total_seconds() / 60)
    return False, 0


def compute_check_out_meta(
    attendance: Attendance,
    check_out_time: datetime,
    office: OfficeSettings,
    employee_id: int = None,
) -> dict:
    """
    Compute working hours, overtime, half-day on check-out.

    All times compared in naive UTC.
    office.office_end_time is IST — converted to UTC for comparison.
    working_minutes = actual time between check-in and check-out (in minutes).
    
    If employee has custom shift for this date, use shift timings instead of office settings.
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

    # Try to get employee-specific shift
    shift_end_time = office.office_end_time
    half_day_threshold = office.half_day_threshold_minutes
    grace_period = office.grace_period_minutes
    
    if employee_id:
        shift_info = get_employee_shift_for_date(employee_id, attendance.date)
        if shift_info:
            shift_end_time = shift_info.get("end_time", office.office_end_time)
            # Note: half_day_threshold comes from office settings (applies to all shifts)
            # Future: could be shift-specific

    # Convert shift end time (IST) to UTC
    shift_end_utc = _naive_combine(attendance.date, shift_end_time) - IST_OFFSET

    # Overtime: worked past shift end time
    overtime_minutes = max(0, int((co - shift_end_utc).total_seconds() / 60)) \
                       if co > shift_end_utc else 0

    # Half-day: worked less than threshold (e.g. 300 min = 5 hours)
    is_half_day = working_minutes < half_day_threshold

    # Early leave: checked out before shift end (minus grace)
    early_leave_threshold = shift_end_utc - timedelta(minutes=grace_period)
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

