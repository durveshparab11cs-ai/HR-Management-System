"""
attendance/gps_service.py
===========================
GPS orchestration service - SIMPLIFIED VERSION.

Just verify coordinates are within geofence. No complex logic.
"""

import logging
from typing import Optional

from flask import request

from app.extensions.database import db
from app.models.employee import Employee
from app.models.gps_log import GPSLog

from .distance_calculator import DistanceResult, calculate as calc_distance
from .location_validator import CoordinateParseError, is_suspicious_coordinate, parse_and_validate

logger = logging.getLogger("attendance")


class GPSVerificationResult:
    """Encapsulates GPS verification result."""

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
    """Validates GPS coordinates against office geofence."""

    def verify(
        self,
        employee: Employee,
        office,
        lat_str: str,
        lon_str: str,
        accuracy_str: str,
        action: str,
    ) -> GPSVerificationResult:
        """GPS verification - simplified version."""
        try:
            logger.info("GPS_VERIFY_START | emp=%s | lat=%s | lon=%s", employee.id, lat_str, lon_str)
            
            # Step 1: Get reference office (simplified - just use provided office)
            if not office:
                logger.error("GPS_NO_OFFICE | emp=%s", employee.id)
                return GPSVerificationResult(success=False, error="No office configured. Contact HR.")
            
            # Extract coordinates - simple getattr
            ref_lat = getattr(office, 'latitude', None)
            ref_lon = getattr(office, 'longitude', None)
            # Try both allowed_radius_metres (Hospital model) and radius_metres (fallback)
            ref_radius = getattr(office, 'allowed_radius_metres', None) or getattr(office, 'radius_metres', None)
            
            if not (ref_lat and ref_lon and ref_radius):
                logger.error("GPS_INCOMPLETE_OFFICE | lat=%s | lon=%s | radius=%s", ref_lat, ref_lon, ref_radius)
                return GPSVerificationResult(success=False, error="Office coordinates incomplete. Contact HR.")
            
            logger.info("GPS_OFFICE_OK | ref_lat=%.7f | ref_lon=%.7f | radius=%d", ref_lat, ref_lon, ref_radius)
            
            # Step 2: Parse employee coordinates
            try:
                lat, lon, accuracy = parse_and_validate(lat_str, lon_str, accuracy_str)
                logger.info("GPS_PARSE_OK | emp_lat=%.7f | emp_lon=%.7f | accuracy=%.1f", lat, lon, accuracy or 0)
            except CoordinateParseError as e:
                logger.error("GPS_PARSE_FAILED | %s", str(e))
                return GPSVerificationResult(success=False, error=str(e))
            
            # Step 3: Check for spoofing
            suspicious = is_suspicious_coordinate(lat, lon)
            if suspicious:
                logger.warning("GPS_SUSPICIOUS | lat=%.7f | lon=%.7f", lat, lon)
                return GPSVerificationResult(
                    success=False,
                    error="Suspicious coordinates detected. Attendance rejected for security.",
                    lat=lat, lon=lon, accuracy=accuracy, suspicious=True
                )
            
            # Step 4: Calculate distance
            try:
                result = calc_distance(lat, lon, ref_lat, ref_lon, ref_radius)
                logger.info("GPS_DISTANCE | distance=%.1fm | allowed=%dm | within=%s", 
                           result.distance_metres, ref_radius, result.within_radius)
            except Exception as e:
                logger.error("GPS_DISTANCE_CALC_FAILED | %s", str(e))
                return GPSVerificationResult(success=False, error=f"Distance calculation failed: {str(e)}")
            
            # Step 5: Check if within radius
            if not result.within_radius:
                # Try both hospital_name (Hospital model) and name (fallback)
                office_name = getattr(office, 'hospital_name', None) or getattr(office, 'name', 'Office')
                reason = f"You are {result.distance_metres:.0f}m from {office_name}. Allowed radius: {ref_radius}m."
                logger.warning("GPS_REJECTED | %s", reason)
                return GPSVerificationResult(
                    success=False, error=reason,
                    lat=lat, lon=lon, accuracy=accuracy, distance=result
                )
            
            # SUCCESS
            logger.info("GPS_OK | distance=%.1fm", result.distance_metres)
            return GPSVerificationResult(
                success=True, lat=lat, lon=lon,
                accuracy=accuracy, distance=result
            )
            
        except Exception as e:
            logger.error("GPS_VERIFY_EXCEPTION | %s | %s", type(e).__name__, str(e))
            import traceback
            logger.error("Traceback:\n%s", traceback.format_exc())
            return GPSVerificationResult(success=False, error=f"GPS error: {str(e)}")

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
        """Log GPS attempt."""
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
            logger.info("GPS_LOG_OK | emp=%s | action=%s", employee.id, action)
        except Exception as exc:
            logger.error("GPS_LOG_FAILED | %s", str(exc))

    def _get_ip(self) -> str:
        xff = request.headers.get("X-Forwarded-For", "")
        return xff.split(",")[0].strip() if xff else (request.remote_addr or "unknown")
