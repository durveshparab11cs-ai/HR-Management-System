"""
app/utils/time_utils.py
========================
Time-of-day helpers for attendance, shift calculations, and duration formatting.
"""

from datetime import datetime, time, timedelta
from typing import Optional


def parse_time(time_str: str, fmt: str = "%H:%M") -> Optional[time]:
    """
    Parse a time string into a time object.

    Args:
        time_str: String like '09:00' or '14:30:00'.
        fmt: strftime format.

    Returns:
        time object or None if parsing fails.
    """
    try:
        return datetime.strptime(time_str.strip(), fmt).time()
    except (ValueError, AttributeError):
        return None


def format_time(t: Optional[time], fmt: str = "%I:%M %p") -> str:
    """
    Format a time object to a human-readable string.

    Args:
        t: time object or None.
        fmt: strftime format string (default 12-hour with AM/PM).

    Returns:
        Formatted string or empty string.
    """
    if t is None:
        return ""
    return datetime.combine(datetime.today(), t).strftime(fmt)


def duration_in_hours(start: time, end: time) -> float:
    """
    Calculate the duration in hours between two time values on the same day.

    Handles overnight shifts (end < start).

    Args:
        start: Start time.
        end: End time.

    Returns:
        Duration in fractional hours.
    """
    today = datetime.today().date()
    start_dt = datetime.combine(today, start)
    end_dt = datetime.combine(today, end)
    if end_dt <= start_dt:
        # Overnight shift — add one day to end
        end_dt += timedelta(days=1)
    delta = end_dt - start_dt
    return round(delta.total_seconds() / 3600, 2)


def duration_in_minutes(start: time, end: time) -> int:
    """
    Calculate duration in whole minutes between two time values.

    Args:
        start: Start time.
        end: End time.

    Returns:
        Duration in minutes.
    """
    return int(duration_in_hours(start, end) * 60)


def format_duration(minutes: int) -> str:
    """
    Format a duration in minutes to a human-readable 'Xh Ym' string.

    Args:
        minutes: Total duration in minutes.

    Returns:
        String like '8h 30m' or '45m'.
    """
    if minutes <= 0:
        return "0m"
    hours, mins = divmod(minutes, 60)
    if hours == 0:
        return f"{mins}m"
    if mins == 0:
        return f"{hours}h"
    return f"{hours}h {mins}m"


def is_late(check_in: time, expected_start: time, grace_minutes: int = 5) -> bool:
    """
    Determine if a check-in time is considered late.

    Args:
        check_in: Actual check-in time.
        expected_start: Scheduled start of the shift.
        grace_minutes: Minutes of grace period before marking late.

    Returns:
        True if the check-in is past the grace period.
    """
    today = datetime.today().date()
    actual = datetime.combine(today, check_in)
    deadline = datetime.combine(today, expected_start) + timedelta(minutes=grace_minutes)
    return actual > deadline


def overtime_hours(total_worked: float, standard_hours: float = 8.0) -> float:
    """
    Calculate overtime hours beyond standard shift.

    Args:
        total_worked: Total hours worked.
        standard_hours: Standard hours per shift (default 8).

    Returns:
        Overtime hours (0 if no overtime).
    """
    return max(0.0, round(total_worked - standard_hours, 2))


def time_to_seconds(t: time) -> int:
    """Convert a time object to total seconds since midnight."""
    return t.hour * 3600 + t.minute * 60 + t.second


def seconds_to_time(seconds: int) -> time:
    """Convert total seconds since midnight to a time object."""
    seconds = seconds % 86400  # Clamp to one day
    hours, remainder = divmod(seconds, 3600)
    minutes, secs = divmod(remainder, 60)
    return time(hours, minutes, secs)
