"""
attendance/gps_service.py
===========================
GPS orchestration service.

Single responsibility: combine coordinate validation, distance calculation,
and GPS audit logging into a single cohesive operation that the attendance
service delegates to.

This is the only class that depends on both the pure calculation modules
AND the Flask/database layer (for logging).
"""

import logging
from typing import Optional, Tuple

from flask import request

from app.extensions.database import db
from app.models.employee import Employee
from app.models.gps_log import GPSLog

from .distance_calculator import DistanceResult, calculate as calc_distance
from .location_validator import CoordinateParseError, is_suspicious_coordinate, parse_and_validate

logger = logging.getLogger("attendance")


class GPSVerificationResult:
    """
    Encapsulates the full result of a GPS verification attempt.

    Attributes:
        success:      True if coordinates are valid and within geofence.
        error:        Human-readable rejection reason (empty on success).
        lat:          Parsed latitude float (None on parse failure).
        lon:          Parsed longitude float (None on parse failure).
        accuracy:     Browser-reported accuracy in metres.
        distance:     DistanceResult with Haversine distance (None on parse failure).
        suspicious:   True if coordinates appear to be spoofed.
    """

    __slots__ = ("success", "error", "lat", "lon", "accuracy", "distance", "suspicious")

    def __init__(
        self,
        success: bool,
        error: str = "",
        lat: Optional[float] = None,
        lon: Optional[float] = None,
        accuracy: Optional[float] = None,
        distance: Optional[DistanceResult] = None,
        suspicious: bool = False,
    ) -> None:
        self.success    = success
        self.error      = error
        self.lat        = lat
        self.lon        = lon
        self.accuracy   = accuracy
        self.distance   = distance
        self.suspicious = suspicious

    @property
    def distance_metres(self) -> Optional[float]:
        return self.distance.distance_metres if self.distance else None

    @property
    def within_radius(self) -> bool:
        return bool(self.distance and self.distance.within_radius)


class GPSService:
    """
    Validates GPS coordinates against an office geofence and logs every attempt.

    Usage:
        svc = GPSService()
        result = svc.verify(employee, office, lat_str, lon_str, acc_str, action)
        if not result.success:
            return False, result.error, None
    """

    def verify(
        self,
        employee: Employee,
        office,
        lat_str: str,
        lon_str: str,
        accuracy_str: str,
        action: str,
    ) -> GPSVerificationResult:
        """
        Full GPS verification pipeline:
            1. Parse and validate raw coordinate strings.
            2. Check for suspicious/spoofed coordinates.
            3. Calculate Haversine distance from office.
            4. Log every attempt to gps_logs table.
            5. Return structured verification result.

        Args:
            employee:     Employee model instance.
            office:       OfficeSettings model instance.
            lat_str:      Raw latitude from form.
            lon_str:      Raw longitude from form.
            accuracy_str: Raw accuracy from browser.
            action:       Log action label (check_in / check_out).

        Returns:
            GPSVerificationResult with full details.
        """
        # Step 1: Parse
        try:
            lat, lon, accuracy = parse_and_validate(lat_str, lon_str, accuracy_str)
        except CoordinateParseError as e:
            self._log(employee, None, None, None, None, action, str(e))
            return GPSVerificationResult(success=False, error=str(e))

        # Step 2: Spoofing check
        suspicious = is_suspicious_coordinate(lat, lon)
        if suspicious:
            reason = "Suspicious coordinates detected. Attendance rejected for security."
            self._log(employee, lat, lon, accuracy, None, action, reason)
            logger.warning(
                "SUSPICIOUS_GPS | emp=%s | lat=%s | lon=%s | action=%s",
                employee.id, lat, lon, action,
            )
            return GPSVerificationResult(
                success=False, error=reason,
                lat=lat, lon=lon, accuracy=accuracy, suspicious=True,
            )

        # Step 2b: Accuracy threshold — reject if GPS accuracy is too poor
        min_accuracy = getattr(office, 'min_gps_accuracy_metres', 50)
        if accuracy is not None and accuracy > min_accuracy:
            reason = (
                f"GPS accuracy is too poor (±{accuracy:.0f}m). "
                f"Required: ±{min_accuracy}m or better. "
                f"Move to an open area and try again."
            )
            self._log(employee, lat, lon, accuracy, None, action, reason)
            logger.warning(
                "GPS_POOR_ACCURACY | emp=%s | accuracy=%.0fm | required=%dm | action=%s",
                employee.id, accuracy, min_accuracy, action,
            )
            return GPSVerificationResult(
                success=False, error=reason,
                lat=lat, lon=lon, accuracy=accuracy,
            )

        # Step 3: Distance
        result = calc_distance(lat, lon, office.latitude, office.longitude, office.radius_metres)

        # Step 4: Log
        self._log(employee, lat, lon, accuracy, result.distance_metres, action)

        # Step 5: Evaluate
        if not result.within_radius:
            reason = (
                f"You are {result.distance_metres:.0f}m from the office. "
                f"Allowed radius: {office.radius_metres}m."
            )
            logger.info(
                "GPS_REJECTED | emp=%s | dist=%.0fm | limit=%dm | action=%s",
                employee.id, result.distance_metres, office.radius_metres, action,
            )
            return GPSVerificationResult(
                success=False, error=reason,
                lat=lat, lon=lon, accuracy=accuracy, distance=result,
            )

        logger.info(
            "GPS_OK | emp=%s | dist=%.0fm | action=%s",
            employee.id, result.distance_metres, action,
        )
        return GPSVerificationResult(
            success=True, lat=lat, lon=lon,
            accuracy=accuracy, distance=result,
        )

    def _log(
        self,
        employee: Employee,
        lat: Optional[float],
        lon: Optional[float],
        accuracy: Optional[float],
        distance: Optional[float],
        action: str,
        rejection_reason: str = "",
    ) -> None:
        """Persist GPS attempt to gps_logs — always called, even on rejection."""
        try:
            ip = self._get_ip()
            entry = GPSLog(
                user_id=employee.user_id,
                employee_id=employee.id,
                latitude=lat,
                longitude=lon,
                accuracy_metres=accuracy,
                distance_from_office=distance,
                action=action,
                ip_address=ip,
            )
            db.session.add(entry)
            db.session.commit()
        except Exception as exc:  # noqa: BLE001
            logger.error("GPS log write failed: %s", exc)

    def _get_ip(self) -> str:
        xff = request.headers.get("X-Forwarded-For", "")
        return xff.split(",")[0].strip() if xff else (request.remote_addr or "unknown")
