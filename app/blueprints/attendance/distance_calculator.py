"""
attendance/distance_calculator.py
===================================
Haversine great-circle distance calculation.

Single responsibility: compute distance between two GPS coordinates.
Pure function module — zero Flask dependency, fully testable in isolation.

The Haversine formula calculates the shortest distance between two
points on a sphere (Earth) given their latitudes and longitudes.
Accuracy: within 0.3% for distances under 10 km — sufficient for
geofence attendance validation.
"""

import math
from typing import NamedTuple

EARTH_RADIUS_METRES: float = 6_371_000.0  # Mean radius of Earth in metres


class DistanceResult(NamedTuple):
    """Result of a distance calculation between two GPS points."""
    distance_metres: float      # Precise Haversine distance
    bearing_degrees: float      # Compass direction from point1 to point2
    within_radius: bool         # Whether distance <= allowed_radius
    allowed_radius_metres: float


def haversine_metres(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """
    Compute great-circle distance in metres using the Haversine formula.

    Accurate to within 0.3% for distances under 10 km.
    Never use Euclidean distance for GPS — it ignores Earth's curvature.

    Args:
        lat1: Latitude of point 1 in decimal degrees.
        lon1: Longitude of point 1 in decimal degrees.
        lat2: Latitude of point 2 in decimal degrees.
        lon2: Longitude of point 2 in decimal degrees.

    Returns:
        Distance in metres as a float.
    """
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    d_phi    = math.radians(lat2 - lat1)
    d_lambda = math.radians(lon2 - lon1)

    a = (math.sin(d_phi / 2.0) ** 2
         + math.cos(phi1) * math.cos(phi2) * math.sin(d_lambda / 2.0) ** 2)

    c = 2.0 * math.atan2(math.sqrt(a), math.sqrt(1.0 - a))
    return round(EARTH_RADIUS_METRES * c, 2)


def bearing_degrees(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """
    Compute the initial compass bearing from point 1 to point 2.

    Args:
        lat1, lon1: Source coordinates in decimal degrees.
        lat2, lon2: Target coordinates in decimal degrees.

    Returns:
        Bearing in degrees 0–360 (clockwise from true north).
    """
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    d_lambda = math.radians(lon2 - lon1)

    x = math.sin(d_lambda) * math.cos(phi2)
    y = (math.cos(phi1) * math.sin(phi2)
         - math.sin(phi1) * math.cos(phi2) * math.cos(d_lambda))

    bearing = math.degrees(math.atan2(x, y))
    return (bearing + 360.0) % 360.0


def calculate(
    employee_lat: float,
    employee_lon: float,
    office_lat: float,
    office_lon: float,
    allowed_radius_metres: float,
) -> DistanceResult:
    """
    Calculate distance and determine whether within geofence.

    Args:
        employee_lat: Employee's current GPS latitude.
        employee_lon: Employee's current GPS longitude.
        office_lat:   Office anchor point latitude.
        office_lon:   Office anchor point longitude.
        allowed_radius_metres: Maximum allowed distance in metres.

    Returns:
        DistanceResult with distance, bearing, within_radius flag.
    """
    dist   = haversine_metres(employee_lat, employee_lon, office_lat, office_lon)
    bering = bearing_degrees(office_lat, office_lon, employee_lat, employee_lon)
    within = dist <= allowed_radius_metres

    return DistanceResult(
        distance_metres=dist,
        bearing_degrees=round(bering, 1),
        within_radius=within,
        allowed_radius_metres=allowed_radius_metres,
    )
