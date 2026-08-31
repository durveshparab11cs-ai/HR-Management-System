"""
Coordinator Attendance Portal - Routes
Simple implementation with I-code and E-code support
"""

from datetime import datetime, date
from flask import render_template, request, jsonify
import logging

from app.extensions.database import db
from app.models.employee import Employee
from app.models.employee_master import EmployeeMaster
from app.models.attendance import Attendance
from app.models.attendance_photo import AttendancePhoto

logger = logging.getLogger("coordinator")


def register_coordinator_routes(app):
    """Register coordinator routes directly with Flask app (bypass Flask-Login)"""
    
    from app.extensions.csrf import csrf
    
    print("\n" + "="*70)
    print("Registering Coordinator Routes (Portal & API)")
    print("="*70 + "\n")
    
    # Route 1: GET /coordinator/portal - Serve the portal HTML
    @app.route("/coordinator/portal", methods=["GET"])
    def coordinator_portal():
        """Serve the coordinator attendance portal page"""
        app.logger.info("[COORDINATOR-PORTAL] Loading portal template...")
        return render_template("coordinator/portal.html")
    
    app.logger.info("✓ Registered /coordinator/portal")
    
    # Route 2: GET /coordinator/login - Redirect to portal
    @app.route("/coordinator/login", methods=["GET"])
    def coordinator_login_redirect():
        """Redirect to coordinator portal"""
        from flask import redirect, url_for
        return redirect(url_for("coordinator_portal"))
    
    app.logger.info("✓ Registered /coordinator/login")
    
    # Route 3: POST /coordinator/api/search-employee - Search by code
    @app.route("/coordinator/api/search-employee", methods=["POST"])
    @csrf.exempt
    def coordinator_api_search_employee():
        """Search employee by code (E- or I- format, or auto-prefix)"""
        try:
            app.logger.info("[SEARCH-EMPLOYEE] API hit")
            
            data = request.get_json(force=True, silent=True) or {}
            employee_code = data.get("employee_code", "").strip().upper()
            
            app.logger.info(f"[SEARCH] Looking for: {employee_code}")
            
            # Auto-prefix if no prefix
            if employee_code and not employee_code.startswith(("E-", "I-")):
                employee_code = f"E-{employee_code}"
            
            if not employee_code or employee_code in ("E-", "I-"):
                return jsonify({"success": False, "error": "Employee code required"}), 400
            
            # Try Employee table first
            employee = Employee.query.filter_by(employee_code=employee_code).first()
            
            # Fall back to EmployeeMaster
            if not employee:
                emp_master = EmployeeMaster.query.filter_by(employee_code=employee_code).first()
                if emp_master:
                    return jsonify({
                        "success": True,
                        "employee": {
                            "id": emp_master.id,
                            "employee_code": emp_master.employee_code,
                            "full_name": emp_master.employee_name or "N/A",
                            "department": emp_master.department or "N/A",
                            "designation": emp_master.designation or "N/A",
                            "email": "N/A"
                        }
                    }), 200
                else:
                    return jsonify({"success": False, "error": "Employee not found"}), 404
            
            # Found in Employee table
            return jsonify({
                "success": True,
                "employee": {
                    "id": employee.id,
                    "employee_code": employee.employee_code,
                    "full_name": employee.full_name or "N/A",
                    "department": employee.department or "N/A",
                    "designation": employee.designation or "N/A",
                    "email": employee.email or "N/A"
                }
            }), 200
            
        except Exception as e:
            app.logger.error(f"[SEARCH-EMPLOYEE] Error: {e}")
            return jsonify({"success": False, "error": "Server error"}), 500
    
    app.logger.info("✓ Registered /coordinator/api/search-employee")
    
    # Route 4: POST /coordinator/api/submit-attendance - Check-in/checkout
    @app.route("/coordinator/api/submit-attendance", methods=["POST"])
    @csrf.exempt
    def coordinator_api_submit_attendance():
        """Submit attendance check-in or check-out"""
        try:
            data = request.get_json(force=True, silent=True) or {}
            
            employee_id = data.get("employee_id")
            action = data.get("action", "checkin").lower()
            photo_base64 = data.get("photo_base64")
            
            if not employee_id or action not in ["checkin", "checkout"]:
                return jsonify({"success": False, "error": "Invalid request"}), 400
            
            employee = Employee.query.get(employee_id)
            if not employee:
                return jsonify({"success": False, "error": "Employee not found"}), 404
            
            now = datetime.utcnow()
            today = now.date()
            
            attendance = Attendance.query.filter_by(employee_id=employee_id, date=today).first()
            
            if action == "checkin":
                if attendance and attendance.check_in_time:
                    return jsonify({"success": False, "error": "Already checked in today"}), 400
                
                if not attendance:
                    attendance = Attendance(employee_id=employee_id, date=today)
                    db.session.add(attendance)
                    db.session.flush()
                
                attendance.check_in_time = now
                db.session.commit()
                
                app.logger.info(f"[CHECK-IN] Employee {employee_id}")
                return jsonify({"success": True, "message": "Check-in recorded", "time": now.strftime("%H:%M:%S")}), 200
            
            elif action == "checkout":
                if not attendance or not attendance.check_in_time:
                    return jsonify({"success": False, "error": "No check-in found today"}), 400
                
                if attendance.check_out_time:
                    return jsonify({"success": False, "error": "Already checked out"}), 400
                
                attendance.check_out_time = now
                db.session.commit()
                
                app.logger.info(f"[CHECK-OUT] Employee {employee_id}")
                return jsonify({"success": True, "message": "Check-out recorded", "time": now.strftime("%H:%M:%S")}), 200
        
        except Exception as e:
            app.logger.error(f"[ATTENDANCE] Error: {e}")
            db.session.rollback()
            return jsonify({"success": False, "error": "Server error"}), 500
    
    app.logger.info("✓ Registered /coordinator/api/submit-attendance")
    
    # Route 5: POST /coordinator/api/get-gps
    @app.route("/coordinator/api/get-gps", methods=["POST"])
    @csrf.exempt
    def coordinator_api_get_gps():
        """Get mock GPS location"""
        return jsonify({"success": True, "latitude": 18.520430, "longitude": 73.856743, "accuracy": 100}), 200
    
    app.logger.info("✓ Registered /coordinator/api/get-gps")
    
    # Route 6: POST /coordinator/api/get-attendance-status
    @app.route("/coordinator/api/get-attendance-status", methods=["POST"])
    @csrf.exempt
    def coordinator_api_get_attendance_status():
        """Get attendance status for today"""
        try:
            data = request.get_json(force=True, silent=True) or {}
            employee_id = data.get("employee_id")
            
            if not employee_id:
                return jsonify({"success": False, "error": "Employee ID required"}), 400
            
            today = date.today()
            attendance = Attendance.query.filter_by(employee_id=employee_id, date=today).first()
            
            if not attendance:
                return jsonify({"success": False, "error": "No attendance record found"}), 404
            
            return jsonify({
                "success": True,
                "attendance": {
                    "status": attendance.status or "pending",
                    "is_late": attendance.is_late or False,
                    "working_minutes": attendance.working_minutes or 0
                }
            }), 200
        
        except Exception as e:
            app.logger.error(f"[ATTENDANCE-STATUS] Error: {e}")
            return jsonify({"success": False, "error": "Server error"}), 500
    
    app.logger.info("✓ Registered /coordinator/api/get-attendance-status")
    
    app.logger.info("="*70)
    app.logger.info("All coordinator routes registered successfully!")
    app.logger.info("="*70)
