"""
Datetime utilities for IST (Indian Standard Time) timezone handling.
IST = UTC + 5:30
"""
from datetime import datetime, timezone, timedelta

# IST is UTC + 5 hours 30 minutes
IST = timezone(timedelta(hours=5, minutes=30))


def get_naive_ist():
    """
    Get current IST time as a naive datetime (no timezone info).
    This is compatible with SQLite datetime fields.
    
    Returns:
        datetime: Current time in IST timezone (naive)
    """
    utc_now = datetime.now(timezone.utc)
    ist_now = utc_now.astimezone(IST)
    return ist_now.replace(tzinfo=None)


def now_ist():
    """
    Get current IST time as timezone-aware datetime.
    
    Returns:
        datetime: Current time in IST timezone (aware)
    """
    utc_now = datetime.now(timezone.utc)
    return utc_now.astimezone(IST)


def utc_to_ist(utc_dt):
    """
    Convert UTC datetime to IST.
    
    Args:
        utc_dt: datetime object (naive or aware)
    
    Returns:
        datetime: IST datetime (naive)
    """
    if utc_dt is None:
        return None
    
    # If naive, assume it's UTC
    if utc_dt.tzinfo is None:
        utc_dt = utc_dt.replace(tzinfo=timezone.utc)
    
    ist_dt = utc_dt.astimezone(IST)
    return ist_dt.replace(tzinfo=None)


def ist_to_utc(ist_dt):
    """
    Convert IST datetime to UTC.
    
    Args:
        ist_dt: datetime object in IST (naive or aware)
    
    Returns:
        datetime: UTC datetime (naive)
    """
    if ist_dt is None:
        return None
    
    # If naive, assume it's IST
    if ist_dt.tzinfo is None:
        ist_dt = ist_dt.replace(tzinfo=IST)
    
    utc_dt = ist_dt.astimezone(timezone.utc)
    return utc_dt.replace(tzinfo=None)
