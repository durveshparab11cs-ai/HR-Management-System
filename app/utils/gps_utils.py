"""
app/utils/gps_utils.py
=======================
GPS coordinate utilities for geofence-based attendance validation.

Used to verify that employees are within an allowed radius of the
office when marking attendance from a mobile browser or kiosk.

All calculations use the Haversine formula which provides accurate
great-circle distances on the Earth's surface.
"""

import math
from typing import Optional


# Earth's mean radius in metres
_EARTH_RADIUS_METRES = 6_371_000


def haversine_distance(
    lat1: float,
    lon1: float,
    lat2: float,
    lon2: float,
) -> float:
    """
    Calculate the great-circle distance between two GPS coordinates.

    Uses the Haversine formula — accurate to within ~0.5% for typical
    HR attendance use cases (distances under 10 km).

    Args:
        lat1: Latitude of point 1 in decimal degrees.
        lon1: Longitude of point 1 in decimal degrees.
        lat2: Latitude of point 2 in decimal degrees.
        lon2: Longitude of point 2 in decimal degrees.

    Returns:
        Distance in metres (float).
    """
    # Convert degrees to radians
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    delta_phi = math.radians(lat2 - lat1)
    delta_lambda = math.radians(lon2 - lon1)

    a = (
        math.sin(delta_phi / 2) ** 2
        + math.cos(phi1) * math.cos(phi2) * math.sin(delta_lambda / 2) ** 2
    )
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

    return _EARTH_RADIUS_METRES * c


def is_within_geofence(
    employee_lat: float,
    employee_lon: float,
    office_lat: float,
    office_lon: float,
    radius_metres: float = 200.0,
) -> bool:
    """
    Determine whether an employee is within the allowed geofence radius.

    Args:
        employee_lat: Employee's current latitude.
        employee_lon: Employee's current longitude.
        office_lat: Office/anchor point latitude.
        office_lon: Office/anchor point longitude.
        radius_metres: Allowed radius in metres (default 200 m).

    Returns:
        True if the employee is within the geofence.
    """
    distance = haversine_distance(
        employee_lat, employee_lon,
        office_lat, office_lon,
    )
    return distance <= radius_metres


def parse_coordinates(lat_str: str, lon_str: str) -> Optional[tuple[float, float]]:
    """
    Parse latitude/longitude from string form field values.

    Args:
        lat_str: Latitude as a string from a form.
        lon_str: Longitude as a string from a form.

    Returns:
        Tuple of (latitude, longitude) floats, or None if parsing fails.
    """
    try:
        lat = float(lat_str)
        lon = float(lon_str)
        if not (-90 <= lat <= 90) or not (-180 <= lon <= 180):
            return None
        return lat, lon
    except (ValueError, TypeError):
        return None


def format_coordinates(lat: float, lon: float, decimals: int = 6) -> str:
    """
    Format coordinates to a human-readable string.

    Args:
        lat: Latitude in decimal degrees.
        lon: Longitude in decimal degrees.
        decimals: Number of decimal places.

    Returns:
        String like '51.507351, -0.127758'.
    """
    return f"{lat:.{decimals}f}, {lon:.{decimals}f}"


def bearing_between(
    lat1: float, lon1: float,
    lat2: float, lon2: float,
) -> float:
    """
    Calculate the compass bearing from point 1 to point 2.

    Args:
        lat1, lon1: Source coordinates in decimal degrees.
        lat2, lon2: Target coordinates in decimal degrees.

    Returns:
        Bearing in degrees (0–360, clockwise from north).
    """
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    delta_lambda = math.radians(lon2 - lon1)

    x = math.sin(delta_lambda) * math.cos(phi2)
    y = (
        math.cos(phi1) * math.sin(phi2)
        - math.sin(phi1) * math.cos(phi2) * math.cos(delta_lambda)
    )

    bearing = math.degrees(math.atan2(x, y))
    return (bearing + 360) % 360
