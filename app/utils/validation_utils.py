"""
app/utils/validation_utils.py
==============================
Reusable input validation functions beyond what WTForms provides.

These are pure functions — no Flask context required — making them
usable in services, CLI scripts, and API handlers alike.
"""

import re
from datetime import date
from typing import Optional


# RFC 5322 compliant email regex (simplified but robust)
_EMAIL_REGEX = re.compile(
    r"^[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}$"
)

# E.164 phone format: +<country><number> (7-15 digits)
_PHONE_E164_REGEX = re.compile(r"^\+[1-9]\d{6,14}$")

# Alphanumeric with underscores and hyphens — for codes/slugs
_SLUG_REGEX = re.compile(r"^[a-z0-9]+(?:[-_][a-z0-9]+)*$")


def is_valid_email(email: str) -> bool:
    """
    Validate an email address format.

    Args:
        email: Email string to validate.

    Returns:
        True if the format is valid.
    """
    if not email or len(email) > 254:
        return False
    return bool(_EMAIL_REGEX.match(email.strip()))


def is_valid_phone(phone: str) -> bool:
    """
    Validate a phone number in E.164 format (+1234567890).

    Args:
        phone: Phone string to validate.

    Returns:
        True if the format matches E.164.
    """
    if not phone:
        return False
    return bool(_PHONE_E164_REGEX.match(phone.strip()))


def is_valid_slug(value: str) -> bool:
    """
    Validate a URL-safe slug (lowercase, alphanumeric, hyphens/underscores).

    Args:
        value: String to validate.

    Returns:
        True if the value is a valid slug.
    """
    if not value:
        return False
    return bool(_SLUG_REGEX.match(value.strip()))


def is_valid_date_range(start: date, end: date) -> bool:
    """
    Validate that start date is not after end date.

    Args:
        start: Range start date.
        end: Range end date.

    Returns:
        True if start <= end.
    """
    return start <= end


def is_valid_percentage(value: float) -> bool:
    """
    Validate that a value is a valid percentage (0.0 to 100.0).

    Args:
        value: Float to validate.

    Returns:
        True if 0.0 <= value <= 100.0.
    """
    return 0.0 <= value <= 100.0


def is_positive_number(value) -> bool:
    """
    Validate that a value is a positive number (> 0).

    Args:
        value: Numeric value to check.

    Returns:
        True if value > 0.
    """
    try:
        return float(value) > 0
    except (TypeError, ValueError):
        return False


def is_non_negative_number(value) -> bool:
    """
    Validate that a value is zero or positive (>= 0).

    Args:
        value: Numeric value to check.

    Returns:
        True if value >= 0.
    """
    try:
        return float(value) >= 0
    except (TypeError, ValueError):
        return False


def sanitize_string(value: Optional[str], max_length: Optional[int] = None) -> str:
    """
    Strip whitespace and optionally truncate a string.

    Args:
        value: Input string or None.
        max_length: Maximum allowed length. Truncates if exceeded.

    Returns:
        Cleaned string, or empty string if input is None.
    """
    if value is None:
        return ""
    cleaned = value.strip()
    if max_length and len(cleaned) > max_length:
        cleaned = cleaned[:max_length]
    return cleaned


def normalize_email(email: str) -> str:
    """
    Normalize an email to lowercase and strip whitespace.

    Args:
        email: Raw email string from form input.

    Returns:
        Normalized email string.
    """
    return email.strip().lower() if email else ""


def contains_only_letters(value: str) -> bool:
    """
    Check that a string contains only letters (including unicode).

    Useful for name validation.

    Args:
        value: String to check.

    Returns:
        True if every character is alphabetic or a space/hyphen.
    """
    if not value:
        return False
    return all(c.isalpha() or c in (" ", "-", "'") for c in value)


def is_valid_employee_code(code: str) -> bool:
    """
    Validate an employee code format: alphanumeric, 3-20 characters.

    Args:
        code: Employee code to validate.

    Returns:
        True if valid.
    """
    if not code:
        return False
    return bool(re.match(r"^[A-Za-z0-9\-]{3,20}$", code.strip()))
