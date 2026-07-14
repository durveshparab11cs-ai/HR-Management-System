"""
app/constants/limits.py
========================
Application-wide numerical limits, thresholds, and size constraints.

Centralizing limits prevents magic numbers from being scattered across
the codebase and makes them trivial to adjust in one place.

Usage:
    from app.constants import Limits
    if len(password) < Limits.Password.MIN_LENGTH:
        raise ValidationError(...)
"""


class Limits:
    """Namespace container for all application limits."""

    class Password:
        """Password policy constraints."""
        MIN_LENGTH: int = 8
        MAX_LENGTH: int = 128
        MAX_FAILED_ATTEMPTS: int = 5
        LOCKOUT_DURATION_MINUTES: int = 30
        RESET_TOKEN_EXPIRY_HOURS: int = 2
        HISTORY_COUNT: int = 5  # Prevent reuse of last N passwords

    class File:
        """File upload size limits (in bytes)."""
        MAX_PROFILE_PHOTO_BYTES: int = 5 * 1024 * 1024       # 5 MB
        MAX_DOCUMENT_BYTES: int = 20 * 1024 * 1024           # 20 MB
        MAX_IMPORT_FILE_BYTES: int = 10 * 1024 * 1024        # 10 MB
        THUMBNAIL_WIDTH: int = 200
        THUMBNAIL_HEIGHT: int = 200

    class Pagination:
        """Pagination defaults and limits."""
        DEFAULT_PAGE_SIZE: int = 25
        MAX_PAGE_SIZE: int = 100
        MIN_PAGE_SIZE: int = 5
        PAGE_SIZE_OPTIONS: tuple = (10, 25, 50, 100)

    class RateLimit:
        """Per-endpoint rate limit strings (Flask-Limiter format)."""
        LOGIN: str = "5 per minute;20 per hour"
        PASSWORD_RESET: str = "3 per hour"
        API_DEFAULT: str = "60 per minute"
        REGISTRATION: str = "3 per hour"
        EXPORT: str = "10 per hour"
        EMAIL_SEND: str = "20 per hour"

    class String:
        """String field length constraints for model columns."""
        SHORT: int = 50
        MEDIUM: int = 100
        LONG: int = 255
        EXTRA_LONG: int = 500
        TEXT: int = 2000
        NOTES: int = 5000
        UUID: int = 36
        EMAIL: int = 254      # RFC 5321 maximum
        PHONE: int = 20
        EMPLOYEE_CODE: int = 20
        IP_ADDRESS: int = 45  # IPv6 max

    class Session:
        """Session and token expiry durations (in seconds)."""
        DEFAULT_LIFETIME: int = 86400       # 24 hours
        REMEMBER_ME: int = 2592000          # 30 days
        API_TOKEN: int = 3600               # 1 hour
        REFRESH_TOKEN: int = 604800         # 7 days
        EMAIL_VERIFY_TOKEN: int = 86400     # 24 hours

    class Payroll:
        """Payroll calculation limits."""
        MAX_OVERTIME_HOURS_PER_WEEK: int = 20
        MAX_DEDUCTION_PERCENTAGE: float = 0.50   # 50% max deduction
        MIN_WAGE_MULTIPLIER: float = 1.0

    class Leave:
        """Leave policy limits."""
        MAX_CONSECUTIVE_DAYS: int = 30
        MIN_ADVANCE_NOTICE_DAYS: int = 1
        MAX_CARRY_FORWARD_DAYS: int = 15
