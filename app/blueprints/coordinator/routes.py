"""
Coordinator Attendance Portal - Clean 4-Step Workflow
Step 1: Employee Code Input
Step 2: Employee Information Display
Step 3: Camera Capture
Step 4: Check-in/Check-out
"""

from datetime import datetime
from flask import Blueprint, render_template, request, jsonify, redirect, url_for, abort, make_response
from flask_login import login_required, current_user
import logging
import random

from app.extensions.database import db
from app.models.employee import Employee
from app.models.attendance import Attendance
from app.blueprints.attendance.gps_service import GPSService
from app.blueprints.attendance.photo_service import PhotoService
from app.blueprints.attendance.distance_calculator import haversine_metres
from app.utils.datetime_utils import get_naive_ist

logger = logging.getLogger("coordinator")

coordinator_bp = Blueprint(
    "coordinator",
    __name__,
    url_prefix="/coordinator",
    template_folder="templates"
)

_gps_svc = GPSService()
_photo_svc = PhotoService()


def _check_coordinator_authorization():
    """Verify coordinator access"""
    if not current_user.is_authenticated:
        abort(401)
    if current_user.role != "super_admin":
        abort(403)
    return current_user


# ============================================================================
# MAIN COORDINATOR PORTAL - 4 STEP WORKFLOW
# ============================================================================

@coordinator_bp.route("/", methods=["GET"])
@login_required
def dashboard():
    """Main coordinator portal dashboard"""
    _check_coordinator_authorization()
    return render_template("coordinator/portal.html")


@coordinator_bp.route("/login", methods=["GET"])
def coordinator_login():
    """Coordinator login page"""
    # If already logged in, redirect to portal
    if current_user.is_authenticated and current_user.role == "super_admin":
        return redirect(url_for("coordinator.dashboard"))
    
    return render_template("coordinator/login.html")


# ============================================================================
# API ENDPOINTS FOR 4-STEP WORKFLOW
# ============================================================================

@coordinator_bp.route("/api/search-employee", methods=["POST"])
@login_required
def search_employee():
    """
    STEP 1 → STEP 2: Search employee by code
    Input: employee_code
    Output: Employee information or error
    """
    _check_coordinator_authorization()
    
    try:
        data = request.get_json()
        employee_code = data.get("employee_code", "").strip().upper()
        
        if not employee_code:
            return jsonify({"success": False, "error": "Employee code required"}), 400
        
        # Search employee
        employee = Employee.query.filter_by(employee_code=employee_code).first()
        
        if not employee:
            return jsonify({"success": False, "error": "Employee not found"}), 404
        
        # Return employee info for STEP 2
        return jsonify({
            "success": True,
            "employee": {
                "id": employee.id,
                "employee_code": employee.employee_code,
                "full_name": employee.full_name,
                "department": employee.department or "N/A",
                "designation": employee.designation or "N/A",
                "email": employee.email or "N/A"
            }
        }), 200
        
    except Exception as e:
        logger.error(f"Search employee error: {str(e)}")
        return jsonify({"success": False, "error": "Server error"}), 500


@coordinator_bp.route("/api/submit-attendance", methods=["POST"])
@login_required
def submit_attendance():
    """
    STEP 4: Submit attendance (check-in or check-out)
    Input: employee_id, action (checkin/checkout), photo_base64, latitude, longitude
    Output: Success/error message
    """
    _check_coordinator_authorization()
    
    try:
        data = request.get_json()
        employee_id = data.get("employee_id")
        action = data.get("action", "checkin").lower()
        photo_base64 = data.get("photo_base64")
        latitude = data.get("latitude", 18.520430)
        longitude = data.get("longitude", 73.856743)
        
        if not employee_id or action not in ["checkin", "checkout"]:
            return jsonify({"success": False, "error": "Invalid request"}), 400
        
        # Get employee
        employee = Employee.query.get(employee_id)
        if not employee:
            return jsonify({"success": False, "error": "Employee not found"}), 404
        
        # Get current time in IST
        now = get_naive_ist()
        today = now.date()
        
        # Check if already checked in today
        existing_checkin = Attendance.query.filter_by(
            employee_id=employee_id,
            checkin_date=today
        ).first()
        
        if action == "checkin":
            if existing_checkin and existing_checkin.checkin_time:
                return jsonify({
                    "success": False,
                    "error": f"Already checked in at {existing_checkin.checkin_time.strftime('%H:%M:%S IST')}"
                }), 400
            
            # Create new attendance record
            if not existing_checkin:
                attendance = Attendance(
                    employee_id=employee_id,
                    checkin_date=today,
                    checkin_time=now,
                    checkin_latitude=latitude,
                    checkin_longitude=longitude,
                    checkin_photo=photo_base64 if photo_base64 else None
                )
                db.session.add(attendance)
            else:
                existing_checkin.checkin_time = now
                existing_checkin.checkin_latitude = latitude
                existing_checkin.checkin_longitude = longitude
                if photo_base64:
                    existing_checkin.checkin_photo = photo_base64
            
            db.session.commit()
            return jsonify({
                "success": True,
                "message": f"✓ Check-in recorded at {now.strftime('%H:%M:%S IST')}",
                "time": now.strftime('%H:%M:%S IST')
            }), 200
        
        elif action == "checkout":
            if not existing_checkin or not existing_checkin.checkin_time:
                return jsonify({
                    "success": False,
                    "error": "No check-in found for today. Please check-in first."
                }), 400
            
            if existing_checkin.checkout_time:
                return jsonify({
                    "success": False,
                    "error": f"Already checked out at {existing_checkin.checkout_time.strftime('%H:%M:%S IST')}"
                }), 400
            
            # Record checkout
            existing_checkin.checkout_time = now
            existing_checkin.checkout_latitude = latitude
            existing_checkin.checkout_longitude = longitude
            if photo_base64:
                existing_checkin.checkout_photo = photo_base64
            
            db.session.commit()
            return jsonify({
                "success": True,
                "message": f"✓ Check-out recorded at {now.strftime('%H:%M:%S IST')}",
                "time": now.strftime('%H:%M:%S IST')
            }), 200
        
    except Exception as e:
        logger.error(f"Submit attendance error: {str(e)}")
        db.session.rollback()
        return jsonify({"success": False, "error": "Server error"}), 500


@coordinator_bp.route("/api/get-gps", methods=["POST"])
@login_required
def get_gps():
    """Get coordinator's current GPS location"""
    _check_coordinator_authorization()
    try:
        # Default location - can be customized
        return jsonify({
            "success": True,
            "latitude": 18.520430,
            "longitude": 73.856743,
            "accuracy": 100
        }), 200
    except Exception as e:
        logger.error(f"GPS error: {str(e)}")
        return jsonify({"success": False, "error": "GPS error"}), 500
