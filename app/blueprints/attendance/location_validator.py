"""
attendance/location_validator.py
==================================
Validates incoming GPS coordinate strings from browser form submissions.

Single responsibility: parse, type-check, and range-validate raw
coordinate strings before they are used in any calculation.

All functions are pure — no Flask or database dependency.
"""

from typing import Optional, Tuple


class CoordinateParseError(ValueError):
    """Raised when GPS coordinate strings cannot be parsed or are out of range."""
    pass


def parse_and_validate(
    lat_str: str,
    lon_str: str,
    accuracy_str: str = "",
) -> Tuple[float, float, Optional[float]]:
    """
    Parse latitude, longitude, and optional accuracy from string inputs.

    Args:
        lat_str:      Raw latitude string from browser form.
        lon_str:      Raw longitude string from browser form.
        accuracy_str: Optional accuracy in metres reported by the browser.

    Returns:
        Tuple of (latitude, longitude, accuracy_or_None).

    Raises:
        CoordinateParseError: With a user-readable message on any failure.
    """
    if not lat_str or not lon_str:
        raise CoordinateParseError(
            "Location data is missing. Please allow location access and try again."
        )

    try:
        lat = float(lat_str.strip())
    except ValueError:
        raise CoordinateParseError(
            "Invalid latitude value. Please refresh and try again."
        )

    try:
        lon = float(lon_str.strip())
    except ValueError:
        raise CoordinateParseError(
            "Invalid longitude value. Please refresh and try again."
        )

    if not (-90.0 <= lat <= 90.0):
        raise CoordinateParseError(
            f"Latitude {lat} is out of the valid range (-90 to 90)."
        )

    if not (-180.0 <= lon <= 180.0):
        raise CoordinateParseError(
            f"Longitude {lon} is out of the valid range (-180 to 180)."
        )

    accuracy: Optional[float] = None
    if accuracy_str:
        try:
            accuracy = float(accuracy_str.strip())
            if accuracy < 0:
                accuracy = None
        except ValueError:
            accuracy = None

    return lat, lon, accuracy


def is_suspicious_coordinate(lat: float, lon: float) -> bool:
    """
    Detect obviously spoofed or test coordinates.

    Rejects:
        - Exact (0.0, 0.0) — the "null island" coordinate used by spoofing tools.
        - Coordinates with more than 8 decimal places (non-physical precision).

    Args:
        lat: Parsed latitude float.
        lon: Parsed longitude float.

    Returns:
        True if the coordinate looks suspicious.
    """
    if lat == 0.0 and lon == 0.0:
        return True

    # More than 8 decimal places suggests a fabricated value
    lat_str = f"{lat}"
    lon_str = f"{lon}"
    lat_decimals = len(lat_str.split(".")[-1]) if "." in lat_str else 0
    lon_decimals = len(lon_str.split(".")[-1]) if "." in lon_str else 0

    if lat_decimals > 8 or lon_decimals > 8:
        return True

    return False
