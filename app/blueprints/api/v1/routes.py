"""
blueprints/api/v1/routes.py
==============================
API v1 route definitions.

All routes return JSON using response_utils helpers.
CSRF is exempt — authentication is via Bearer token.
Rate limiting is applied per endpoint.

Current endpoints (skeleton):
    GET  /api/v1/health          — liveness probe
    GET  /api/v1/me              — current authenticated user info
    GET  /api/v1/kiosk           — attendance kiosk page
    GET  /api/v1/kiosk/employee  — lookup employee by code
    POST /api/v1/kiosk/attendance — submit attendance
"""

from flask import g, render_template, request, jsonify
from flask_login import login_required

from app.utils.response_utils import success_response
from app.constants.limits import Limits
from app.extensions.limiter import limiter
from app.extensions.csrf import csrf
from .. import api_bp


# Exempt the entire API blueprint from CSRF — uses token auth instead.
csrf.exempt(api_bp)


# ---------------------------------------------------------------------------
# Health
# ---------------------------------------------------------------------------

@api_bp.route("/health", methods=["GET"])
def health():
    """
    Liveness probe endpoint for load balancers and Docker health checks.

    Returns HTTP 200 with status 'ok' when the application is running.
    Does not require authentication.
    """
    return success_response(data={"status": "ok", "version": "1.0.0"})


# ---------------------------------------------------------------------------
# Auth
# ---------------------------------------------------------------------------

@api_bp.route("/me", methods=["GET"])
@login_required
@limiter.limit(Limits.RateLimit.API_DEFAULT)
def me():
    """Return the current authenticated user's profile."""
    from flask_login import current_user  # noqa: PLC0415
    return success_response(data={
        "id": current_user.id,
        "email": current_user.email,
        "full_name": current_user.full_name,
        "role": current_user.role,
    })


# ---------------------------------------------------------------------------
# Attendance Kiosk
# ---------------------------------------------------------------------------

@api_bp.route("/kiosk", methods=["GET"])
def kiosk():
    """
    Attendance Kiosk - 4-step flow:
    1. Employee Code Entry
    2. Employee Details Display
    3. Camera Photo Capture
    4. Check In/Out Submission
    """
    return render_template("api/v1/kiosk.html", title="Attendance Kiosk")


@api_bp.route("/kiosk/employee", methods=["GET"])
def kiosk_employee():
    """
    Lookup employee by code from the kiosk.
    
    Query params:
        code: Employee code (e.g., E-2603025)
    
    Returns:
        {success: bool, employee: {...}, message: string}
    """
    code = request.args.get("code", "").strip().upper()
    
    if not code:
        return jsonify({"success": False, "message": "Employee code required"}), 400
    
    try:
        from app.blueprints.employees.repository import EmployeeRepository
        emp_repo = EmployeeRepository()
        employee = emp_repo.get_by_code(code)
        
        if not employee:
            return jsonify({
                "success": False,
                "message": f"Employee {code} not found"
            }), 404
        
        return jsonify({
            "success": True,
            "employee": {
                "id": employee.id,
                "code": employee.employee_code,
                "name": employee.full_name,
                "department": employee.department or "N/A",
                "designation": employee.designation or "N/A",
                "photo_url": f"/api/v1/employee/{employee.id}/photo" if employee.profile_photo else None,
            },
            "message": f"Found: {employee.full_name}"
        })
    
    except Exception as e:
        return jsonify({
            "success": False,
            "message": f"Lookup failed: {str(e)}"
        }), 500


@api_bp.route("/kiosk/attendance", methods=["POST"])
def kiosk_attendance():
    """
    Submit attendance from the kiosk.
    
    JSON body:
        {
            "employee_code": "E-2603025",
            "check_type": "checkin" | "checkout",
            "latitude": 18.5204,
            "longitude": 73.8567,
            "accuracy": 25.0,
            "photo_base64": "data:image/jpeg;base64,..."
        }
    
    Returns:
        {success: bool, message: string, attendance_id: int}
    """
    from datetime import date
    
    data = request.get_json() or {}
    
    code = data.get("employee_code", "").upper()
    check_type = data.get("check_type", "checkin").lower()
    latitude = data.get("latitude")
    longitude = data.get("longitude")
    accuracy = data.get("accuracy")
    photo_b64 = data.get("photo_base64")
    
    # Validation
    if not all([code, check_type, latitude, longitude, accuracy, photo_b64]):
        return jsonify({
            "success": False,
            "message": "Missing required fields"
        }), 400
    
    try:
        from app.blueprints.employees.repository import EmployeeRepository
        from app.blueprints.attendance.repository import AttendanceRepository
        from app.models.attendance_photo import AttendancePhoto
        from app.extensions.database import db
        
        emp_repo = EmployeeRepository()
        att_repo = AttendanceRepository()
        
        # Find employee
        employee = emp_repo.get_by_code(code)
        if not employee:
            return jsonify({
                "success": False,
                "message": f"Employee {code} not found"
            }), 404
        
        today = date.today()
        
        # Get or create attendance record
        attendance = att_repo.get_today(employee.id, today)
        if not attendance:
            from app.models.attendance import Attendance
            attendance = Attendance(
                employee_id=employee.id,
                date=today,
                status="present"
            )
            db.session.add(attendance)
            db.session.flush()
        
        # Store check-in/out time
        from datetime import datetime
        now = datetime.now()
        
        if check_type == "checkin":
            attendance.check_in_time = now
        else:
            attendance.check_out_time = now
        
        # Store photo
        photo = AttendancePhoto.query.filter_by(attendance_id=attendance.id).first()
        if not photo:
            photo = AttendancePhoto(attendance_id=attendance.id)
            db.session.add(photo)
        
        if check_type == "checkin":
            photo.image_data = photo_b64
        else:
            photo.checkout_image_data = photo_b64
        
        db.session.commit()
        
        return jsonify({
            "success": True,
            "message": f"{check_type.title()} recorded for {employee.full_name}",
            "attendance_id": attendance.id,
            "employee": {
                "code": employee.employee_code,
                "name": employee.full_name
            }
        })
    
    except Exception as e:
        db.session.rollback()
        return jsonify({
            "success": False,
            "message": f"Attendance submission failed: {str(e)}"
        }), 500

