"""
app/utils/date_utils.py
========================
Date manipulation, formatting, and arithmetic utilities.

All internal date/time operations use UTC. Display formatting
converts to the configured APP_TIMEZONE only at the presentation layer.
"""

from datetime import date, datetime, timedelta, timezone
from typing import Optional

import pytz


def utc_now() -> datetime:
    """Return the current UTC datetime with timezone info."""
    return datetime.now(timezone.utc)


def today_utc() -> date:
    """Return today's date in UTC."""
    return datetime.now(timezone.utc).date()


def to_utc(dt: datetime, source_tz: str = "UTC") -> datetime:
    """
    Convert a naive or tz-aware datetime to UTC.

    Args:
        dt: The datetime to convert.
        source_tz: IANA timezone name of the source datetime if naive.

    Returns:
        UTC-aware datetime.
    """
    if dt.tzinfo is None:
        tz = pytz.timezone(source_tz)
        dt = tz.localize(dt)
    return dt.astimezone(timezone.utc)


def to_local(dt: datetime, target_tz: str) -> datetime:
    """
    Convert a UTC datetime to the target local timezone.

    Args:
        dt: UTC datetime (aware or naive assumed UTC).
        target_tz: IANA timezone name for conversion.

    Returns:
        Timezone-aware datetime in the target timezone.
    """
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    tz = pytz.timezone(target_tz)
    return dt.astimezone(tz)


def format_date(d: Optional[date], fmt: str = "%d %b %Y") -> str:
    """
    Format a date object to a human-readable string.

    Args:
        d: Date object or None.
        fmt: strftime format string.

    Returns:
        Formatted date string, or empty string if d is None.
    """
    if d is None:
        return ""
    return d.strftime(fmt)


def format_datetime(dt: Optional[datetime], fmt: str = "%d %b %Y, %I:%M %p") -> str:
    """
    Format a datetime to a human-readable string.

    Args:
        dt: Datetime object or None.
        fmt: strftime format string.

    Returns:
        Formatted datetime string or empty string.
    """
    if dt is None:
        return ""
    return dt.strftime(fmt)


def parse_date(date_str: str, fmt: str = "%Y-%m-%d") -> Optional[date]:
    """
    Parse a date string to a date object.

    Args:
        date_str: String representation of a date.
        fmt: Expected format string.

    Returns:
        date object or None if parsing fails.
    """
    try:
        return datetime.strptime(date_str.strip(), fmt).date()
    except (ValueError, AttributeError):
        return None


def parse_datetime(dt_str: str, fmt: str = "%Y-%m-%d %H:%M:%S") -> Optional[datetime]:
    """
    Parse a datetime string to a datetime object.

    Args:
        dt_str: String representation of a datetime.
        fmt: Expected format string.

    Returns:
        datetime object or None if parsing fails.
    """
    try:
        return datetime.strptime(dt_str.strip(), fmt)
    except (ValueError, AttributeError):
        return None


def working_days_between(start: date, end: date, include_weekends: bool = False) -> int:
    """
    Count working days between two dates (inclusive of both endpoints).

    Args:
        start: Start date.
        end: End date.
        include_weekends: If True, count all calendar days.

    Returns:
        Number of working days.
    """
    if start > end:
        return 0
    total = 0
    current = start
    while current <= end:
        if include_weekends or current.weekday() < 5:  # 0-4 = Mon-Fri
            total += 1
        current += timedelta(days=1)
    return total


def calendar_days_between(start: date, end: date) -> int:
    """
    Count calendar days between two dates (inclusive).

    Args:
        start: Start date.
        end: End date.

    Returns:
        Number of calendar days (0 if start > end).
    """
    if start > end:
        return 0
    return (end - start).days + 1


def is_weekend(d: date) -> bool:
    """Return True if the given date falls on Saturday or Sunday."""
    return d.weekday() >= 5


def is_future(d: date) -> bool:
    """Return True if the given date is in the future."""
    return d > today_utc()


def is_past(d: date) -> bool:
    """Return True if the given date is in the past."""
    return d < today_utc()


def start_of_month(d: date) -> date:
    """Return the first day of the month containing d."""
    return d.replace(day=1)


def end_of_month(d: date) -> date:
    """Return the last day of the month containing d."""
    if d.month == 12:
        return d.replace(day=31)
    return d.replace(month=d.month + 1, day=1) - timedelta(days=1)


def start_of_year(d: date) -> date:
    """Return January 1st of the year containing d."""
    return d.replace(month=1, day=1)


def end_of_year(d: date) -> date:
    """Return December 31st of the year containing d."""
    return d.replace(month=12, day=31)


def age_from_birthdate(birthdate: date) -> int:
    """
    Calculate age in full years from a birthdate.

    Args:
        birthdate: The date of birth.

    Returns:
        Age in complete years.
    """
    today = today_utc()
    age = today.year - birthdate.year
    # Subtract 1 if birthday hasn't occurred yet this year
    if (today.month, today.day) < (birthdate.month, birthdate.day):
        age -= 1
    return age


def human_readable_delta(dt: datetime) -> str:
    """
    Return a human-readable time delta string (e.g., '3 minutes ago').

    Args:
        dt: A datetime in the past.

    Returns:
        Human-readable relative time string.
    """
    now = utc_now()
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    delta = now - dt
    seconds = int(delta.total_seconds())

    if seconds < 60:
        return "just now"
    if seconds < 3600:
        minutes = seconds // 60
        return f"{minutes} minute{'s' if minutes != 1 else ''} ago"
    if seconds < 86400:
        hours = seconds // 3600
        return f"{hours} hour{'s' if hours != 1 else ''} ago"
    if seconds < 604800:
        days = seconds // 86400
        return f"{days} day{'s' if days != 1 else ''} ago"
    weeks = seconds // 604800
    return f"{weeks} week{'s' if weeks != 1 else ''} ago"
