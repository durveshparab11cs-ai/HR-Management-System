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
    Detect obviously spoofed or physically impossible coordinates.

    Only returns True when there is clear, unambiguous evidence of
    fabrication or data corruption. Normal browser GPS — including
    desktop GPS, low-accuracy GPS (50–100 m), and JavaScript floating
    point representations — must NEVER be flagged.

    Rejects ONLY:
        - Exact (0.0, 0.0) — "null island", the default spoofing tool value.
        - NaN or infinite values — corrupted data, not real GPS.
        - Out-of-range values — caught earlier in parse_and_validate, but
          double-checked here for defence-in-depth.

    Does NOT reject:
        - Coordinates with many decimal places — JavaScript's String()
          serialization of IEEE 754 floats routinely produces 15+ decimal
          place strings (e.g. 19.014699600000002) from perfectly valid GPS
          readings. Rejecting on decimal count causes false positives for
          every user on Chrome/Android.
        - Coordinates inside the allowed geofence — being physically present
          is the opposite of suspicious.
        - Any accuracy value — GPS accuracy of 50–200 m is normal for
          desktop/urban environments and is not evidence of spoofing.

    Args:
        lat: Parsed latitude float.
        lon: Parsed longitude float.

    Returns:
        True only when actual evidence of fabrication exists.
    """
    import math  # noqa: PLC0415

    # Corrupted / non-physical values
    if math.isnan(lat) or math.isnan(lon):
        return True
    if math.isinf(lat) or math.isinf(lon):
        return True

    # Null island — exact zero used by mock GPS tools as default
    if lat == 0.0 and lon == 0.0:
        return True

    # Out-of-range (belt-and-suspenders; parse_and_validate catches this first)
    if not (-90.0 <= lat <= 90.0) or not (-180.0 <= lon <= 180.0):
        return True

    # All other coordinates are treated as genuine unless proven otherwise
    # through additional session-level movement analysis (not done here).
    return False
