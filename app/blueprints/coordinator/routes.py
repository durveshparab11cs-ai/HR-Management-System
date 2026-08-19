"""
Coordinator attendance kiosk routes.
Coordinator-only portal for marking employee attendance.

Only authenticated user with employee_code = "E-2606026" can access these routes.
All attendance is marked AGAINST SELECTED EMPLOYEES, not the coordinator.
GPS/geofence verification uses COORDINATOR DEVICE location, not employee location.
"""

from datetime import datetime, date, timedelta
from flask import render_template, request, jsonify, redirect, url_for, abort
from flask_login import login_required, current_user
import logging

from app.blueprints.coordinator import coordinator_bp
from app.models.employee import Employee
from app.models.user import User
from app.models.attendance import Attendance
from app.models.office_settings import OfficeSettings
from app.models.attendance_photo import AttendancePhoto
from app.blueprints.attendance.photo_service import PhotoService
from app.blueprints.attendance.gps_service import GPSService
from app.blueprints.attendance.distance_calculator import haversine_metres
from app.blueprints.employees.repository import EmployeeRepository
from app.extensions.database import db

logger = logging.getLogger("coordinator")

_emp_repo = EmployeeRepository()
_photo_svc = PhotoService()
_gps_svc = GPSService()


# ── Authorization Check ──────────────────────────────────────────────
def _check_coordinator_authorization():
    """
    Verify that current user has coordinator access.
    Coordinator can be:
    1. The dedicated coordinator_kiosk user
    2. Any Super Admin user
    
    Returns:
        current_user if authorized, aborts 403 if not
    """
    if not current_user.is_authenticated:
        abort(401)
    
    # Allow access if user is Super Admin (can mark attendance)
    if current_user.role == "super_admin":
        return current_user
    
    # Also allow the old E-2606026 coordinator for backward compatibility
    employee = _emp_repo.get_by_user_id(current_user.id)
    if employee and employee.employee_code == "E-2606026":
        return current_user
    
    logger.warning(
        "Coordinator authorization denied | user=%s | role=%s",
        current_user.username,
        current_user.role
    )
    abort(403)


# ── MAIN DASHBOARD ──────────────────────────────────────────────────

@coordinator_bp.route("/", methods=["GET"])
@login_required
def dashboard():
    """
    Render the coordinator attendance kiosk dashboard.
    Only E-2606026 can access.
    """
    _check_coordinator_authorization()
    return render_template("coordinator/dashboard.html")


# ── EMPLOYEE SEARCH ──────────────────────────────────────────────────

@coordinator_bp.route("/search", methods=["POST"])
@login_required
def search_employee():
    """
    Search for an employee by code or name.
    Only coordinator can access.
    
    Request JSON:
        {
            "search_term": "E-2606001" or "John Doe"
        }
    
    Response:
        {
            "success": true,
            "employee": {
                "id": 123,
                "employee_code": "E-2606001",
                "full_name": "John Doe",
                "department": "Engineering",
                "designation": "Software Engineer",
                "profile_photo": "data:image/...",
                "today_status": "not_checked_in",  # not_checked_in | checked_in | checked_out
                "today_check_in": "10:15",
                "today_check_out": "18:30",
                "shift_start": "09:00",
                "shift_end": "18:00"
            }
        }
    """
    try:
        _check_coordinator_authorization()
        
        data = request.get_json()
        search_term = data.get("search_term", "").strip()
        
        if not search_term:
            return jsonify({"success": False, "error": "Search term is required"}), 400
        
        # Search by employee code (exact match) or name (case-insensitive)
        # Prefer exact code match
        employee = Employee.query.filter_by(employee_code=search_term).first()
        
        if not employee:
            # Try by name
            employee = Employee.query.filter(
                (Employee.first_name.ilike(f"%{search_term}%")) |
                (Employee.last_name.ilike(f"%{search_term}%"))
            ).first()
        
        if not employee:
            return jsonify({"success": False, "error": f"Employee '{search_term}' not found"}), 404
        
        # Get today's attendance
        today = date.today()
        attendance = Attendance.query.filter_by(
            employee_id=employee.id,
            date=today
        ).first()
        
        # Determine today's status
        if attendance:
            if attendance.check_out_time:
                today_status = "checked_out"
                check_in_time = attendance.check_in_time.strftime("%H:%M") if attendance.check_in_time else None
                check_out_time = attendance.check_out_time.strftime("%H:%M") if attendance.check_out_time else None
            elif attendance.check_in_time:
                today_status = "checked_in"
                check_in_time = attendance.check_in_time.strftime("%H:%M")
                check_out_time = None
            else:
                today_status = "pending"
                check_in_time = None
                check_out_time = None
        else:
            today_status = "not_checked_in"
            check_in_time = None
            check_out_time = None
        
        # Get office settings for shift times
        office = OfficeSettings.query.first()
        shift_start = office.office_start_time.strftime("%H:%M") if office else "09:00"
        shift_end = office.office_end_time.strftime("%H:%M") if office else "18:00"
        
        return jsonify({
            "success": True,
            "employee": {
                "id": employee.id,
                "employee_code": employee.employee_code,
                "full_name": f"{employee.first_name} {employee.last_name}",
                "department": employee.department or "N/A",
                "designation": employee.designation or "N/A",
                "profile_photo": employee.profile_photo or None,
                "today_status": today_status,
                "today_check_in": check_in_time,
                "today_check_out": check_out_time,
                "shift_start": shift_start,
                "shift_end": shift_end
            }
        }), 200
    
    except Exception as e:
        logger.error("Search employee error: %s", str(e))
        return jsonify({"success": False, "error": "Server error during search"}), 500


# ── GET EMPLOYEE INFO ───────────────────────────────────────────────

@coordinator_bp.route("/employee-info/<int:employee_id>", methods=["GET"])
@login_required
def get_employee_info(employee_id):
    """
    Get detailed employee information for display.
    
    Response:
        {
            "success": true,
            "employee": { ... },
            "today_attendance": { ... }
        }
    """
    try:
        _check_coordinator_authorization()
        
        employee = Employee.query.get(employee_id)
        if not employee:
            return jsonify({"success": False, "error": "Employee not found"}), 404
        
        # Get today's attendance
        today = date.today()
        attendance = Attendance.query.filter_by(
            employee_id=employee_id,
            date=today
        ).first()
        
        office = OfficeSettings.query.first()
        
        return jsonify({
            "success": True,
            "employee": {
                "id": employee.id,
                "employee_code": employee.employee_code,
                "full_name": f"{employee.first_name} {employee.last_name}",
                "department": employee.department,
                "designation": employee.designation,
                "profile_photo": employee.profile_photo
            },
            "today_attendance": {
                "status": attendance.status if attendance else "absent",
                "check_in": attendance.check_in_time.isoformat() if attendance and attendance.check_in_time else None,
                "check_out": attendance.check_out_time.isoformat() if attendance and attendance.check_out_time else None,
                "check_in_lat": attendance.check_in_latitude if attendance else None,
                "check_in_lon": attendance.check_in_longitude if attendance else None,
                "check_in_distance": attendance.check_in_distance_metres if attendance else None
            },
            "office": {
                "lat": office.latitude if office else 18.520430,
                "lon": office.longitude if office else 73.856743,
                "radius": office.radius_metres if office else 200
            }
        }), 200
    
    except Exception as e:
        logger.error("Get employee info error: %s", str(e))
        return jsonify({"success": False, "error": "Server error"}), 500


# ── CHECK-IN ────────────────────────────────────────────────────────

@coordinator_bp.route("/check-in", methods=["POST"])
@login_required
def check_in():
    """
    Mark employee check-in with coordinator device GPS and photo.
    
    Request JSON:
        {
            "employee_id": 123,
            "latitude": 18.520430,
            "longitude": 73.856743,
            "accuracy": 25.5,
            "photo_base64": "data:image/jpeg;base64,..."
        }
    
    Response:
        {
            "success": true,
            "attendance": {
                "id": 456,
                "employee_id": 123,
                "check_in_time": "2026-08-18T10:15:30",
                "check_in_distance_metres": 45.2
            }
        }
    """
    try:
        _check_coordinator_authorization()
        
        data = request.get_json()
        employee_id = data.get("employee_id")
        latitude = data.get("latitude")
        longitude = data.get("longitude")
        accuracy = data.get("accuracy")
        photo_base64 = data.get("photo_base64")
        
        # Validate inputs
        if not employee_id:
            return jsonify({"success": False, "error": "Employee ID required"}), 400
        if latitude is None or longitude is None:
            return jsonify({"success": False, "error": "GPS coordinates required"}), 400
        if not photo_base64:
            return jsonify({"success": False, "error": "Proof photo required"}), 400
        
        # Verify employee exists
        employee = Employee.query.get(employee_id)
        if not employee:
            return jsonify({"success": False, "error": "Employee not found"}), 404
        
        # Check if already checked in today
        today = date.today()
        existing = Attendance.query.filter_by(
            employee_id=employee_id,
            date=today
        ).first()
        
        if existing and existing.check_in_time:
            return jsonify({
                "success": False,
                "error": f"{employee.first_name} is already checked in",
                "status": "already_checked_in"
            }), 409
        
        # Get office settings for GPS validation
        office = OfficeSettings.query.first()
        if not office:
            return jsonify({"success": False, "error": "Office settings not configured"}), 500
        
        # Verify GPS is within office radius
        distance_m = haversine_metres(
            office.latitude, office.longitude,
            float(latitude), float(longitude)
        )
        
        min_accuracy = office.min_gps_accuracy_metres or 50
        if accuracy > min_accuracy:
            return jsonify({
                "success": False,
                "error": f"GPS accuracy {accuracy:.1f}m exceeds minimum {min_accuracy}m",
                "status": "gps_accuracy_poor",
                "gps_accuracy": accuracy
            }), 400
        
        allowed_radius = office.radius_metres or 200
        if distance_m > allowed_radius:
            return jsonify({
                "success": False,
                "error": f"You are {distance_m:.1f}m from office (allowed: {allowed_radius}m)",
                "status": "outside_geofence",
                "distance_metres": distance_m,
                "allowed_radius": allowed_radius
            }), 400
        
        # Create or update attendance record
        now = datetime.now()
        if existing:
            # Update existing pending record
            attendance = existing
            attendance.check_in_time = now
            attendance.check_in_latitude = float(latitude)
            attendance.check_in_longitude = float(longitude)
            attendance.check_in_accuracy = float(accuracy)
            attendance.check_in_distance_metres = distance_m
            attendance.status = "present"
        else:
            # Create new attendance record
            attendance = Attendance(
                employee_id=employee_id,
                date=today,
                check_in_time=now,
                check_in_latitude=float(latitude),
                check_in_longitude=float(longitude),
                check_in_accuracy=float(accuracy),
                check_in_distance_metres=distance_m,
                status="present"
            )
            db.session.add(attendance)
        
        db.session.flush()  # Flush to get attendance.id
        
        # Store check-in photo
        try:
            # Create AttendancePhoto record
            photo = AttendancePhoto(
                attendance_id=attendance.id,
                employee_id=employee_id,
                image_data=photo_base64,
                ip_address=request.remote_addr
            )
            db.session.add(photo)
        except Exception as photo_err:
            logger.warning("Failed to save check-in photo: %s", photo_err)
            # Continue anyway - attendance is recorded
        
        db.session.commit()
        
        logger.info(
            "Coordinator check-in | coordinator=%s | employee=%s | distance=%.1fm",
            current_user.username,
            employee.employee_code,
            distance_m
        )
        
        return jsonify({
            "success": True,
            "message": f"✓ {employee.first_name} checked in successfully",
            "attendance": {
                "id": attendance.id,
                "employee_id": employee_id,
                "check_in_time": attendance.check_in_time.isoformat(),
                "check_in_distance_metres": round(distance_m, 1)
            }
        }), 200
    
    except Exception as e:
        db.session.rollback()
        logger.error("Check-in error: %s", str(e))
        return jsonify({"success": False, "error": "Server error during check-in"}), 500


# ── CHECK-OUT ───────────────────────────────────────────────────────

@coordinator_bp.route("/check-out", methods=["POST"])
@login_required
def check_out():
    """
    Mark employee check-out with coordinator device GPS and photo.
    
    Request JSON:
        {
            "employee_id": 123,
            "latitude": 18.520430,
            "longitude": 73.856743,
            "accuracy": 25.5,
            "photo_base64": "data:image/jpeg;base64,..."
        }
    
    Response:
        {
            "success": true,
            "attendance": {
                "id": 456,
                "employee_id": 123,
                "check_out_time": "2026-08-18T18:30:00",
                "working_hours": "8h 15m"
            }
        }
    """
    try:
        _check_coordinator_authorization()
        
        data = request.get_json()
        employee_id = data.get("employee_id")
        latitude = data.get("latitude")
        longitude = data.get("longitude")
        accuracy = data.get("accuracy")
        photo_base64 = data.get("photo_base64")
        
        # Validate inputs
        if not employee_id:
            return jsonify({"success": False, "error": "Employee ID required"}), 400
        if latitude is None or longitude is None:
            return jsonify({"success": False, "error": "GPS coordinates required"}), 400
        if not photo_base64:
            return jsonify({"success": False, "error": "Checkout photo required"}), 400
        
        # Verify employee exists
        employee = Employee.query.get(employee_id)
        if not employee:
            return jsonify({"success": False, "error": "Employee not found"}), 404
        
        # Get today's attendance
        today = date.today()
        attendance = Attendance.query.filter_by(
            employee_id=employee_id,
            date=today
        ).first()
        
        if not attendance:
            return jsonify({
                "success": False,
                "error": f"{employee.first_name} has no check-in for today",
                "status": "no_check_in"
            }), 404
        
        if not attendance.check_in_time:
            return jsonify({
                "success": False,
                "error": f"{employee.first_name} has not checked in yet",
                "status": "not_checked_in"
            }), 409
        
        if attendance.check_out_time:
            return jsonify({
                "success": False,
                "error": f"{employee.first_name} has already checked out",
                "status": "already_checked_out"
            }), 409
        
        # Get office settings for GPS validation
        office = OfficeSettings.query.first()
        if not office:
            return jsonify({"success": False, "error": "Office settings not configured"}), 500
        
        # Verify GPS is within office radius
        distance_m = haversine_metres(
            office.latitude, office.longitude,
            float(latitude), float(longitude)
        )
        
        min_accuracy = office.min_gps_accuracy_metres or 50
        if accuracy > min_accuracy:
            return jsonify({
                "success": False,
                "error": f"GPS accuracy {accuracy:.1f}m exceeds minimum {min_accuracy}m",
                "status": "gps_accuracy_poor",
                "gps_accuracy": accuracy
            }), 400
        
        allowed_radius = office.radius_metres or 200
        if distance_m > allowed_radius:
            return jsonify({
                "success": False,
                "error": f"You are {distance_m:.1f}m from office (allowed: {allowed_radius}m)",
                "status": "outside_geofence",
                "distance_metres": distance_m,
                "allowed_radius": allowed_radius
            }), 400
        
        # Record check-out
        now = datetime.now()
        attendance.check_out_time = now
        attendance.check_out_latitude = float(latitude)
        attendance.check_out_longitude = float(longitude)
        attendance.check_out_accuracy = float(accuracy)
        attendance.check_out_distance_metres = distance_m
        
        # Calculate working hours
        if attendance.check_in_time:
            duration = now - datetime.combine(
                attendance.check_in_time.date(),
                attendance.check_in_time.time()
            )
            working_seconds = duration.total_seconds()
            working_minutes = int(working_seconds // 60)
            attendance.working_minutes = working_minutes
        
        db.session.flush()
        
        # Store check-out photo
        try:
            photo = AttendancePhoto.query.filter_by(
                attendance_id=attendance.id
            ).first()
            
            if photo:
                photo.checkout_image_data = photo_base64
            else:
                photo = AttendancePhoto(
                    attendance_id=attendance.id,
                    employee_id=employee_id,
                    checkout_image_data=photo_base64,
                    ip_address=request.remote_addr
                )
                db.session.add(photo)
        except Exception as photo_err:
            logger.warning("Failed to save checkout photo: %s", photo_err)
        
        db.session.commit()
        
        working_hours = attendance.working_hours_display if hasattr(attendance, 'working_hours_display') else "N/A"
        
        logger.info(
            "Coordinator check-out | coordinator=%s | employee=%s | distance=%.1fm | worked=%s",
            current_user.username,
            employee.employee_code,
            distance_m,
            working_hours
        )
        
        return jsonify({
            "success": True,
            "message": f"✓ {employee.first_name} checked out successfully",
            "attendance": {
                "id": attendance.id,
                "employee_id": employee_id,
                "check_out_time": attendance.check_out_time.isoformat(),
                "check_out_distance_metres": round(distance_m, 1),
                "working_hours": working_hours
            }
        }), 200
    
    except Exception as e:
        db.session.rollback()
        logger.error("Check-out error: %s", str(e))
        return jsonify({"success": False, "error": "Server error during check-out"}), 500
