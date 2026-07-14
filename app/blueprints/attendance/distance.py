"""
attendance/distance.py
========================
Haversine great-circle distance calculation.
Pure function — no Flask dependency.
"""

import math

EARTH_RADIUS_METRES = 6_371_000


def haversine(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """
    Return the distance in metres between two GPS coordinates.
    Uses the Haversine formula — accurate to within ~0.5% for short distances.
    """
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)

    a = math.sin(dphi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2) ** 2
    return EARTH_RADIUS_METRES * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))


def is_within_radius(
    emp_lat: float, emp_lon: float,
    office_lat: float, office_lon: float,
    radius_metres: float,
) -> tuple[bool, float]:
    """
    Check whether employee coordinates are within the office geofence.

    Returns:
        (within: bool, distance_metres: float)
    """
    dist = haversine(emp_lat, emp_lon, office_lat, office_lon)
    return dist <= radius_metres, round(dist, 2)
