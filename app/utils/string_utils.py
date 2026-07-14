"""
app/utils/string_utils.py
==========================
String manipulation utilities — slugify, truncate, sanitize, and format helpers.
"""

import re
import unicodedata
from typing import Optional


def slugify(value: str, separator: str = "-") -> str:
    """
    Convert a string to a URL-safe slug.

    Example: 'Hello World!' → 'hello-world'

    Args:
        value: Input string.
        separator: Word separator character (default '-').

    Returns:
        Lowercase slug string.
    """
    # Normalize unicode characters to ASCII equivalents
    value = unicodedata.normalize("NFKD", value)
    value = value.encode("ascii", "ignore").decode("ascii")
    value = value.lower()
    # Replace non-alphanumeric sequences with the separator
    value = re.sub(r"[^\w\s-]", "", value)
    value = re.sub(r"[-_\s]+", separator, value)
    return value.strip(separator)


def truncate(text: Optional[str], max_length: int = 100, suffix: str = "...") -> str:
    """
    Truncate a string to a maximum length, appending a suffix if truncated.

    Args:
        text: Input string or None.
        max_length: Maximum allowed length (including suffix).
        suffix: Appended when text is truncated.

    Returns:
        Truncated string.
    """
    if not text:
        return ""
    if len(text) <= max_length:
        return text
    return text[: max_length - len(suffix)].rstrip() + suffix


def snake_to_title(value: str) -> str:
    """
    Convert a snake_case string to Title Case.

    Example: 'first_name' → 'First Name'

    Args:
        value: snake_case string.

    Returns:
        Title-cased string.
    """
    return value.replace("_", " ").title()


def camel_to_snake(name: str) -> str:
    """
    Convert camelCase or PascalCase to snake_case.

    Example: 'employeeId' → 'employee_id'

    Args:
        name: camelCase identifier.

    Returns:
        snake_case string.
    """
    s1 = re.sub(r"(.)([A-Z][a-z]+)", r"\1_\2", name)
    return re.sub(r"([a-z0-9])([A-Z])", r"\1_\2", s1).lower()


def format_currency(amount: float, currency_symbol: str = "₹", decimals: int = 2) -> str:
    """
    Format a float as a currency string with thousands separator.

    Example: 125000.5 → '₹1,25,000.50' (Indian format) or '₹125,000.50'

    Args:
        amount: Monetary amount.
        currency_symbol: Currency prefix symbol.
        decimals: Number of decimal places.

    Returns:
        Formatted currency string.
    """
    formatted = f"{amount:,.{decimals}f}"
    return f"{currency_symbol}{formatted}"


def initials(full_name: str, max_chars: int = 2) -> str:
    """
    Extract initials from a full name.

    Example: 'John Michael Doe' → 'JD'

    Args:
        full_name: Full name string.
        max_chars: Maximum number of initial characters (default 2).

    Returns:
        Uppercase initials string.
    """
    parts = [p for p in full_name.strip().split() if p]
    if not parts:
        return "?"
    if len(parts) == 1:
        return parts[0][0].upper()
    return (parts[0][0] + parts[-1][0]).upper()[:max_chars]


def pluralize(count: int, singular: str, plural: Optional[str] = None) -> str:
    """
    Return the singular or plural form of a word based on count.

    Example: pluralize(1, 'day') → '1 day'
             pluralize(5, 'day') → '5 days'

    Args:
        count: The quantity.
        singular: Singular form of the word.
        plural: Plural form. If None, appends 's' to singular.

    Returns:
        String with count and appropriate word form.
    """
    word = singular if count == 1 else (plural or f"{singular}s")
    return f"{count} {word}"


def mask_sensitive(value: str, visible_chars: int = 4) -> str:
    """
    Mask all but the last N characters of a sensitive string.

    Useful for displaying partial account/card numbers.

    Example: mask_sensitive('1234567890', 4) → '******7890'

    Args:
        value: Sensitive string.
        visible_chars: Number of characters to leave visible at the end.

    Returns:
        Masked string.
    """
    if not value or len(value) <= visible_chars:
        return "*" * len(value) if value else ""
    return "*" * (len(value) - visible_chars) + value[-visible_chars:]
