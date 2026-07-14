"""
attendance/gps.py
===================
GPS data parsing, validation, and logging helpers.
"""

import logging
from typing import Optional, Tuple

from flask import request
from app.extensions.database import db
from app.models.gps_log import GPSLog

logger = logging.getLogger("attendance")


def parse_coordinates(lat_str: str, lon_str: str) -> Tuple[Optional[float], Optional[float], str]:
    """
    Parse and validate latitude/longitude strings from form input.

    Returns:
        (latitude, longitude, error_message)
        error_message is empty string on success.
    """
    try:
        lat = float(lat_str)
        lon = float(lon_str)
    except (TypeError, ValueError):
        return None, None, "Invalid coordinates received. Please allow location access."

    if not (-90 <= lat <= 90):
        return None, None, "Latitude out of valid range (-90 to 90)."
    if not (-180 <= lon <= 180):
        return None, None, "Longitude out of valid range (-180 to 180)."

    return lat, lon, ""


def log_gps_attempt(
    user_id: int,
    employee_id: Optional[int],
    lat: Optional[float],
    lon: Optional[float],
    accuracy: Optional[float],
    distance_from_office: Optional[float],
    action: str,
) -> GPSLog:
    """
    Persist a GPS attempt to the gps_logs table.
    Always called regardless of success/failure.
    """
    ip = _get_ip()
    entry = GPSLog(
        user_id=user_id,
        employee_id=employee_id,
        latitude=lat,
        longitude=lon,
        accuracy_metres=accuracy,
        distance_from_office=distance_from_office,
        action=action,
        ip_address=ip,
    )
    db.session.add(entry)
    db.session.commit()
    logger.info(
        "GPS_LOG | user=%s | action=%s | lat=%s | lon=%s | dist=%s | ip=%s",
        user_id, action, lat, lon, distance_from_office, ip,
    )
    return entry


def _get_ip() -> str:
    xff = request.headers.get("X-Forwarded-For")
    if xff:
        return xff.split(",")[0].strip()
    return request.remote_addr or "unknown"
