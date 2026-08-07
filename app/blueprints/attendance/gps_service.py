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
            3. Calculate Haversine distance from office OR allocated hospital.
            4. Log every attempt to gps_logs table.
            5. Return structured verification result.

        Args:
            employee:     Employee model instance.
            office:       OfficeSettings model instance (fallback if no hospital assigned).
            lat_str:      Raw latitude from form.
            lon_str:      Raw longitude from form.
            accuracy_str: Raw accuracy from browser.
            action:       Log action label (check_in / check_out).

        Returns:
            GPSVerificationResult with full details.
        """
        try:
            # Determine GPS reference point: Employee's hospital OR office
            reference_office = None
            location_name = "Office"
            location_type = "office"
            
            # Priority 1: Use employee's assigned HOSPITAL if exists
            from app.models.employee_hospital_assignment import EmployeeHospitalAssignment  # noqa: PLC0415
            from app.models.hospital import Hospital  # noqa: PLC0415
            
            try:
                current_hospital_assign = EmployeeHospitalAssignment.query.filter(
                    EmployeeHospitalAssignment.employee_id == employee.id,
                    EmployeeHospitalAssignment.effective_until.is_(None),
                    EmployeeHospitalAssignment.is_deleted == False
                ).first()
                
                if current_hospital_assign and current_hospital_assign.hospital_id:
                    hospital = Hospital.query.filter_by(id=current_hospital_assign.hospital_id).first()
                    if hospital and hospital.latitude and hospital.longitude:
                        reference_office = hospital
                        location_name = hospital.hospital_name
                        location_type = "hospital"
                        logger.info(
                            "GPS_REFERENCE | emp=%s | using_assigned_hospital=%s | lat=%.7f | lon=%.7f",
                            employee.id, hospital.hospital_name, hospital.latitude, hospital.longitude
                        )
                    elif hospital:
                        logger.info(
                            "GPS_REFERENCE | emp=%s | hospital_assigned_but_no_coords | hospital_id=%d",
                            employee.id, hospital.id
                        )
            except Exception as hosp_err:
                logger.warning("GPS_REFERENCE | emp=%s | hospital_lookup_failed: %s", employee.id, str(hosp_err))
            
            # Priority 2: Fall back to employee's assigned office if exists
            if not reference_office and employee.office_settings_id:
                try:
                    emp_office = employee.office
                    if emp_office:
                        reference_office = emp_office
                        location_name = emp_office.name if hasattr(emp_office, 'name') else "Employee Office"
                        location_type = "office"
                        logger.info(
                            "GPS_REFERENCE | emp=%s | using_employee_office=%s | office_id=%d",
                            employee.id, location_name, employee.office_settings_id
                        )
                except Exception as office_err:  # noqa: BLE001
                    logger.warning("GPS_REFERENCE | emp=%s | office_relationship_failed: %s", employee.id, str(office_err))
            
            # Priority 3: Use provided office parameter (fallback)
            if not reference_office and office:
                reference_office = office
                location_name = office.name if hasattr(office, 'name') else "Office"
                location_type = "office"
                logger.info(
                    "GPS_REFERENCE | emp=%s | using_provided_office=%s",
                    employee.id, location_name
                )
            
            # Safety check - if no office found, return error
            if not reference_office:
                reason = "No office location configured. Contact HR."
                logger.error("GPS_NO_OFFICE | emp=%s | cannot_proceed", employee.id)
                self._log(employee, None, None, None, None, action, reason)
                return GPSVerificationResult(success=False, error=reason)
            
            # Extract coordinates with safety checks
            reference_lat = getattr(reference_office, 'latitude', None)
            reference_lon = getattr(reference_office, 'longitude', None)
            allowed_radius = getattr(reference_office, 'radius_metres', None)
            
            # Validate required coordinates exist
            if reference_lat is None or reference_lon is None or allowed_radius is None:
                reason = f"Office location incomplete: lat={reference_lat}, lon={reference_lon}, radius={allowed_radius}. Contact HR."
                logger.error(
                    "GPS_INVALID_COORDS | emp=%s | location=%s | lat=%s | lon=%s | radius=%s",
                    employee.id, location_name, reference_lat, reference_lon, allowed_radius
                )
                self._log(employee, None, None, None, None, action, reason)
                return GPSVerificationResult(success=False, error=reason)
            
            logger.info(
                "GPS_REFERENCE_FINAL | emp=%s | location=%s | lat=%.7f | lon=%.7f | radius=%dm",
                employee.id, location_name, reference_lat, reference_lon, allowed_radius
            )
            
            # Step 1: Parse
            try:
                lat, lon, accuracy = parse_and_validate(lat_str, lon_str, accuracy_str)
            except CoordinateParseError as e:
                self._log(employee, None, None, None, None, action, str(e))
                return GPSVerificationResult(success=False, error=str(e))

            # Step 2: Spoofing check — only flags physically impossible values
            suspicious = is_suspicious_coordinate(lat, lon)

            if suspicious:
                # Compute distance for context logging even on spoof rejection
                try:
                    dist_ctx = calc_distance(lat, lon, reference_lat, reference_lon, allowed_radius)
                    dist_for_log = dist_ctx.distance_metres
                except Exception:  # noqa: BLE001
                    dist_for_log = None

                reason = "Suspicious coordinates detected. Attendance rejected for security."
                logger.warning(
                    "SUSPICIOUS_GPS_REJECTED | emp=%s | lat=%.7f | lon=%.7f"
                    " | accuracy=%s | ref_lat=%.7f | ref_lon=%.7f | location=%s"
                    " | distance=%s | allowed_radius=%s | inside_geofence=%s"
                    " | spoof_detection=True | reason=%r | action=%s",
                    employee.id, lat, lon,
                    f"{accuracy:.1f}m" if accuracy is not None else "n/a",
                    reference_lat, reference_lon, location_name,
                    f"{dist_for_log:.1f}m" if dist_for_log is not None else "n/a",
                    f"{allowed_radius}m",
                    (dist_for_log is not None and dist_for_log <= allowed_radius),
                    reason, action,
                )
                self._log(employee, lat, lon, accuracy, dist_for_log, action, reason)
                return GPSVerificationResult(
                    success=False, error=reason,
                    lat=lat, lon=lon, accuracy=accuracy, suspicious=True,
                )

            # Step 2b: Log accuracy for audit — no hard rejection on accuracy alone.
            min_accuracy = getattr(reference_office, 'min_gps_accuracy_metres', 50)
            if accuracy is not None and accuracy > min_accuracy:
                logger.info(
                    "GPS_LOW_ACCURACY_ACCEPTED | emp=%s | accuracy=%.0fm | threshold=%dm | action=%s",
                    employee.id, accuracy, min_accuracy, action,
                )

            # Step 3: Distance - calculate from reference point (hospital or office)
            result = calc_distance(lat, lon, reference_lat, reference_lon, allowed_radius)

            # Step 4: Log
            self._log(employee, lat, lon, accuracy, result.distance_metres, action)

            # Step 5: Evaluate
            if not result.within_radius:
                reason = (
                    f"You are {result.distance_metres:.0f}m from {location_name}. "
                    f"Allowed radius: {allowed_radius}m."
                )
                logger.info(
                    "GPS_REJECTED | emp=%s | location=%s | dist=%.0fm | limit=%dm | action=%s",
                    employee.id, location_name, result.distance_metres, allowed_radius, action,
                )
                return GPSVerificationResult(
                    success=False, error=reason,
                    lat=lat, lon=lon, accuracy=accuracy, distance=result,
                )

            logger.info(
                "GPS_OK | emp=%s | location=%s | dist=%.0fm | action=%s",
                employee.id, location_name, result.distance_metres, action,
            )
            return GPSVerificationResult(
                success=True, lat=lat, lon=lon,
                accuracy=accuracy, distance=result,
            )
        except Exception as gps_verify_err:
            logger.error("GPS_VERIFY_EXCEPTION | emp=%s | Error: %s", employee.id, str(gps_verify_err))
            import traceback
            logger.error("GPS verify full traceback:\n%s", traceback.format_exc())
            # Return error instead of crashing
            reason = f"GPS verification system error: {str(gps_verify_err)}"
            try:
                self._log(employee, None, None, None, None, action, reason)
            except Exception as log_err:
                logger.error("GPS_LOG_FAILED | Could not write GPS log: %s", str(log_err))
            return GPSVerificationResult(success=False, error=reason)

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
