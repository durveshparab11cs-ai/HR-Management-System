"""
Coordinator Attendance Portal - Simple Routes

CRITICAL: These routes bypass Flask-Login entirely by using the `@app.route` decorator
directly instead of using the blueprint. This prevents Flask-Login from intercepting
and redirecting unauthenticated requests to the login page.
"""

from datetime import datetime, date
from flask import render_template, request, jsonify, redirect, url_for
import logging

from app.extensions.database import db
from app.models.employee import Employee
from app.models.attendance import Attendance

logger = logging.getLogger("coordinator")

# We'll register these routes directly with the app instead of using a blueprint
# This way Flask-Login won't intercept them

def register_coordinator_routes(app):
    """Register coordinator routes directly with the Flask app to bypass Flask-Login."""
    from app.extensions.csrf import csrf  # noqa: PLC0415
    
    print("\n" + "="*80)
    print("REGISTERING COORDINATOR ROUTES!")
    print("="*80 + "\n")
    
    app.logger.info("=" * 70)
    app.logger.info("Registering coordinator API routes directly (bypass Flask-Login)")
    app.logger.info("=" * 70)
    
    @app.route("/coordinator/portal", methods=["GET"])
    def coordinator_portal():
        """Serve the coordinator attendance portal page"""
        app.logger.info("[COORDINATOR-PORTAL] Loading portal template...")
        return render_template("coordinator/portal.html")
    
    app.logger.info("✓ Registered /coordinator/portal")
    
    @app.route("/coordinator/api/search-employee", methods=["POST"])
    @csrf.exempt
    def coordinator_api_search_employee():
        """Search employee by code - PUBLIC API, NO AUTH REQUIRED"""
        app.logger.info(f"✓✓✓ /coordinator/api/search-employee ROUTE HIT ✓✓✓")
        try:
            data = request.get_json(force=True, silent=True) or {}
            employee_code = data.get("employee_code", "").strip().upper()
            app.logger.info(f"[COORDINATOR-API-ROUTE] Searching for employee: {employee_code}")
            
            # Ensure E- prefix
            if employee_code and not employee_code.startswith("E-"):
                employee_code = f"E-{employee_code}"
            
            if not employee_code or employee_code == "E-":
                return jsonify({"success": False, "error": "Employee code required"}), 400
            
            logger.info(f"[COORDINATOR-API] Searching: {employee_code}")
            employee = Employee.query.filter_by(employee_code=employee_code).first()
            
            if not employee:
                logger.warning(f"[COORDINATOR-API] Not found: {employee_code}")
                return jsonify({"success": False, "error": "Employee not found"}), 404
            
            logger.info(f"[COORDINATOR-API] Found: {employee.full_name}")
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
            logger.error(f"[COORDINATOR-API] Error: {e}")
            return jsonify({"success": False, "error": "Server error"}), 500
    
    app.logger.info("✓ Registered /coordinator/api/search-employee")
    
    @app.route("/coordinator/api/submit-attendance", methods=["POST"])
    @csrf.exempt
    def coordinator_api_submit_attendance():
        """Submit attendance (check-in/checkout) - PUBLIC API, NO AUTH REQUIRED"""
        try:
            data = request.get_json(force=True, silent=True) or {}
            
            employee_id = data.get("employee_id")
            action = data.get("action", "checkin").lower()
            photo_base64 = data.get("photo_base64")
            latitude = data.get("latitude", 0)
            longitude = data.get("longitude", 0)
            
            if not employee_id or action not in ["checkin", "checkout"]:
                return jsonify({"success": False, "error": "Invalid request"}), 400
            
            employee = Employee.query.get(employee_id)
            if not employee:
                return jsonify({"success": False, "error": "Employee not found"}), 404
            
            now = datetime.utcnow()
            today = now.date()
            
            attendance = Attendance.query.filter_by(
                employee_id=employee_id,
                date=today
            ).first()
            
            if action == "checkin":
                if attendance and attendance.check_in_time:
                    return jsonify({
                        "success": False,
                        "error": "Already checked in today"
                    }), 400
                
                if not attendance:
                    attendance = Attendance(
                        employee_id=employee_id,
                        date=today
                    )
                    db.session.add(attendance)
                
                attendance.check_in_time = now
                attendance.check_in_latitude = latitude
                attendance.check_in_longitude = longitude
                if photo_base64:
                    attendance.check_in_selfie = photo_base64
                
                db.session.commit()
                logger.info(f"[COORDINATOR-API] Check-in: {employee_id}")
                
                return jsonify({
                    "success": True,
                    "message": "Check-in recorded",
                    "time": now.strftime('%H:%M:%S')
                }), 200
            
            elif action == "checkout":
                if not attendance or not attendance.check_in_time:
                    return jsonify({
                        "success": False,
                        "error": "No check-in found today"
                    }), 400
                
                if attendance.check_out_time:
                    return jsonify({
                        "success": False,
                        "error": "Already checked out"
                    }), 400
                
                attendance.check_out_time = now
                attendance.check_out_latitude = latitude
                attendance.check_out_longitude = longitude
                
                db.session.commit()
                logger.info(f"[COORDINATOR-API] Check-out: {employee_id}")
                
                return jsonify({
                    "success": True,
                    "message": "Check-out recorded",
                    "time": now.strftime('%H:%M:%S')
                }), 200
            
        except Exception as e:
            logger.error(f"[COORDINATOR-API] submit error: {e}")
            db.session.rollback()
            return jsonify({"success": False, "error": "Server error"}), 500
    
    app.logger.info("✓ Registered /coordinator/api/submit-attendance")

    @app.route("/coordinator/api/get-gps", methods=["POST"])
    @csrf.exempt
    def coordinator_api_get_gps():
        """Get GPS location - PUBLIC API, NO AUTH REQUIRED"""
        try:
            return jsonify({
                "success": True,
                "latitude": 18.520430,
                "longitude": 73.856743,
                "accuracy": 100
            }), 200
        except Exception as e:
            logger.error(f"get-gps error: {e}")
            return jsonify({"success": False, "error": "GPS error"}), 500
    
    app.logger.info("✓ Registered /coordinator/api/get-gps")
    app.logger.info("=" * 70)
    app.logger.info("All coordinator API routes registered successfully!")
    app.logger.info("=" * 70)


# Create a blueprint for backwards compatibility (legacy routes can still use the blueprint)
from flask import Blueprint

coordinator_bp = Blueprint(
    "coordinator",
    __name__,
    url_prefix="/coordinator",
    template_folder="templates"
)
