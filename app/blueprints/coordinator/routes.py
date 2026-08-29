"""
Coordinator Attendance Portal - Simple Routes

CRITICAL: These routes bypass Flask-Login entirely by using the `@app.route` decorator
directly instead of using the blueprint. This prevents Flask-Login from intercepting
and redirecting unauthenticated requests to the login page.
"""

from datetime import datetime, date, time as datetime_time, timedelta
from flask import render_template, request, jsonify, redirect, url_for
import logging
import pytz

from app.extensions.database import db
from app.models.employee import Employee
from app.models.employee_master import EmployeeMaster
from app.models.attendance import Attendance
from app.models.attendance_photo import AttendancePhoto
from app.models.user import User
from app.models.employee_shift_assignment import EmployeeShiftAssignment
from app.models.company import Shift
from app.models.leave import EarlyLeaveRequest

logger = logging.getLogger("coordinator")

# We'll register these routes directly with the app instead of using a blueprint
# This way Flask-Login won't intercept them

def get_employee_shift_for_date(employee_id, attendance_date):
    """Get the active shift for an employee on a given date."""
    try:
        assignment = EmployeeShiftAssignment.query.filter(
            EmployeeShiftAssignment.employee_id == employee_id,
            EmployeeShiftAssignment.effective_from <= attendance_date,
            (EmployeeShiftAssignment.effective_until.is_(None) | 
             (EmployeeShiftAssignment.effective_until >= attendance_date))
        ).first()
        
        if assignment and assignment.shift:
            return assignment.shift
        return None
    except Exception as e:
        logger.error(f"Error getting shift for employee {employee_id}: {e}")
        return None

def check_early_leave_approved(employee_id, attendance_date):
    """Check if employee has approved early leave for the date."""
    try:
        early_leave = EarlyLeaveRequest.query.filter_by(
            employee_id=employee_id,
            date=attendance_date,
            status="approved"
        ).first()
        return early_leave is not None
    except Exception as e:
        logger.error(f"Error checking early leave: {e}")
        return False

def calculate_attendance_status(attendance_record, employee_id):
    """
    Calculate and set attendance status based on working hours and shift timing.
    
    Rules:
    - Late Mark: Check-in time > Shift start time + grace period
    - Half Day: 5 hours <= working hours < 9 hours
    - Present: working hours >= 9 hours
    - Early Leave: If approved early leave exists, apply it
    """
    try:
        if not attendance_record.check_in_time or not attendance_record.check_out_time:
            # Can't calculate if check-in or check-out is missing
            return
        
        # Get IST timezone
        IST = pytz.timezone('Asia/Kolkata')
        
        # Convert times to IST
        check_in = attendance_record.check_in_time
        check_out = attendance_record.check_out_time
        
        # If UTC, convert to IST
        if check_in.tzinfo is None:
            check_in = pytz.utc.localize(check_in).astimezone(IST)
        else:
            check_in = check_in.astimezone(IST)
            
        if check_out.tzinfo is None:
            check_out = pytz.utc.localize(check_out).astimezone(IST)
        else:
            check_out = check_out.astimezone(IST)
        
        # Calculate working minutes (total duration)
        duration = check_out - check_in
        total_working_minutes = int(duration.total_seconds() / 60)
        
        # Get shift information
        shift = get_employee_shift_for_date(employee_id, attendance_record.date)
        
        # Calculate late mark
        is_late = False
        late_minutes = 0
        
        if shift:
            # Create shift start datetime in IST for the attendance date
            shift_start_time = shift.start_time  # This is a time object (e.g., 09:00:00)
            
            # Create a datetime for shift start on the attendance date, then localize to IST
            shift_start_naive = datetime.combine(attendance_record.date, shift_start_time)
            shift_start_ist = IST.localize(shift_start_naive)
            
            # Add grace period to shift start
            grace_minutes = shift.grace_minutes or 10
            grace_time_ist = shift_start_ist + timedelta(minutes=grace_minutes)
            
            # Compare check_in with grace_time (both now in IST)
            if check_in > grace_time_ist:
                is_late = True
                late_minutes = int((check_in - grace_time_ist).total_seconds() / 60)
            
            logger.info(f"[ATTENDANCE-CALC] Employee {employee_id}: "
                       f"ShiftStart={shift_start_ist.strftime('%Y-%m-%d %H:%M:%S %Z')}, "
                       f"GraceTime={grace_time_ist.strftime('%H:%M:%S %Z')}, "
                       f"CheckIn={check_in.strftime('%Y-%m-%d %H:%M:%S %Z')}, "
                       f"Late={is_late}, LateMinutes={late_minutes}")
        
        # Account for break time
        break_minutes = (shift.break_minutes or 60) if shift else 60
        working_minutes = total_working_minutes - break_minutes
        working_minutes = max(0, working_minutes)  # Ensure non-negative
        
        working_hours = working_minutes / 60
        
        # Check for early leave
        has_early_leave = check_early_leave_approved(employee_id, attendance_record.date)
        
        # Determine status
        status = "absent"  # Default
        is_half_day = False
        
        if has_early_leave:
            # If early leave approved, mark as early leave (treated as present/half-day based on hours)
            if working_hours >= 5:
                status = "present"  # Early leave with enough hours
                attendance_record.is_early_leave = True
            else:
                status = "half_day"
                is_half_day = True
                attendance_record.is_early_leave = True
        else:
            # Standard logic
            if working_hours >= 9:
                status = "present"
            elif working_hours >= 5:
                status = "half_day"
                is_half_day = True
            else:
                status = "absent"
        
        # Update attendance record
        attendance_record.working_minutes = working_minutes
        attendance_record.is_late = is_late
        attendance_record.late_minutes = late_minutes if is_late else 0
        attendance_record.is_half_day = is_half_day
        attendance_record.status = status
        
        logger.info(f"[ATTENDANCE-CALC] Employee {employee_id} ({attendance_record.date}): "
                   f"WorkingHours={working_hours:.2f}, Status={status}, IsHalfDay={is_half_day}, "
                   f"IsLate={is_late}, LateMinutes={late_minutes}, EarlyLeave={has_early_leave}")
        
    except Exception as e:
        logger.error(f"Error calculating attendance status: {e}", exc_info=True)

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

    @app.route("/coordinator/login", methods=["GET"])
    def coordinator_login_redirect():
        """Redirect /coordinator/login to login page with coordinator tab"""
        return redirect(url_for("authentication.login", tab="coordinator"))
    
    app.logger.info("✓ Registered /coordinator/login (redirect to portal)")
    
    @app.route("/coordinator/api/search-employee", methods=["POST"])
    @csrf.exempt
    def coordinator_api_search_employee():
        """Search employee by code - PUBLIC API, NO AUTH REQUIRED"""
        app.logger.info(f"✓✓✓ /coordinator/api/search-employee ROUTE HIT ✓✓✓")
        app.logger.info(f"[DATABASE-CONFIG] DATABASE_URL: {app.config.get('SQLALCHEMY_DATABASE_URI')}")
        
        try:
            data = request.get_json(force=True, silent=True) or {}
            employee_code = data.get("employee_code", "").strip().upper()
            app.logger.info(f"[COORDINATOR-API-ROUTE] Searching for employee: {employee_code}")
            
            # Ensure E- or I- prefix (accept both formats)
            if employee_code and not employee_code.startswith("E-") and not employee_code.startswith("I-"):
                employee_code = f"E-{employee_code}"
            
            if not employee_code or employee_code == "E-":
                resp = jsonify({"success": False, "error": "Employee code required"})
                resp.headers['Content-Type'] = 'application/json'
                return resp, 400
            
            logger.info(f"[COORDINATOR-API] Searching: {employee_code}")
            from sqlalchemy.orm import joinedload
            
            try:
                # First try Employee table
                employee = Employee.query.options(joinedload(Employee.user)).filter_by(employee_code=employee_code).first()
                
                # If not found in Employee, try EmployeeMaster
                if not employee:
                    app.logger.info(f"[COORDINATOR-API] Not in Employee table, checking EmployeeMaster...")
                    app.logger.info(f"[COORDINATOR-API] Querying EmployeeMaster for: {employee_code}")
                    emp_master = EmployeeMaster.query.filter_by(employee_code=employee_code).first()
                    app.logger.info(f"[COORDINATOR-API] EmployeeMaster query result: {emp_master}")
                    if emp_master:
                        # Found in EmployeeMaster, create a minimal employee object to return data
                        app.logger.info(f"[COORDINATOR-API] Found in EmployeeMaster: {emp_master.employee_name}")
                        response_data = {
                            "success": True,
                            "employee": {
                                "id": emp_master.id,  # Use master ID as fallback
                                "employee_code": emp_master.employee_code,
                                "full_name": emp_master.employee_name or "N/A",
                                "department": emp_master.department or "N/A",
                                "designation": emp_master.designation or "N/A",
                                "email": "N/A"  # EmployeeMaster doesn't have email; email is only in Employee/User models
                            }
                        }
                        resp = jsonify(response_data)
                        resp.headers['Content-Type'] = 'application/json'
                        return resp, 200
                    else:
                        # Not found in either table
                        logger.warning(f"[COORDINATOR-API] Not found in either table: {employee_code}")
                        resp = jsonify({"success": False, "error": "Employee not found"})
                        resp.headers['Content-Type'] = 'application/json'
                        return resp, 404
                
            except Exception as db_err:
                app.logger.error(f"[COORDINATOR-API] Database query failed: {db_err}")
                logger.error(f"[COORDINATOR-API] Database query failed: {db_err}")
                # If database fails, return error
                resp = jsonify({"success": False, "error": f"Database error: {str(db_err)[:100]}"})
                resp.headers['Content-Type'] = 'application/json'
                return resp, 500
            
            logger.info(f"[COORDINATOR-API] Found employee ID: {employee.id}")
            
            # Get the employee name from EmployeeMaster (which has the correct name)
            try:
                emp_master = EmployeeMaster.query.filter_by(employee_code=employee_code).first()
            except Exception as e:
                app.logger.warning(f"[COORDINATOR-API] EmployeeMaster query failed: {e}")
                emp_master = None
                
            full_name = employee.employee_code or "N/A"
            
            if emp_master and emp_master.employee_name:
                full_name = emp_master.employee_name.strip() or full_name
                logger.info(f"[COORDINATOR-API] Using EmployeeMaster name: '{full_name}'")
            else:
                # Fallback to User model if EmployeeMaster doesn't have the name
                try:
                    user = User.query.get(employee.user_id) if employee.user_id else None
                except Exception as e:
                    app.logger.warning(f"[COORDINATOR-API] User query failed: {e}")
                    user = None
                    
                if user:
                    first = (user.first_name or "").strip()
                    last = (user.last_name or "").strip()
                    fallback_name = f"{first} {last}".strip()
                    if fallback_name:
                        full_name = fallback_name
                        logger.info(f"[COORDINATOR-API] Using User model name: '{full_name}'")
            
            logger.info(f"[COORDINATOR-API] Final full_name for response: '{full_name}'")
            
            response_data = {
                "success": True,
                "employee": {
                    "id": employee.id,
                    "employee_code": employee.employee_code,
                    "full_name": full_name,
                    "department": employee.department or "N/A",
                    "designation": employee.designation or "N/A",
                    "email": employee.email or "N/A"
                }
            }
            resp = jsonify(response_data)
            resp.headers['Content-Type'] = 'application/json'
            return resp, 200
            
        except Exception as e:
            app.logger.error(f"[COORDINATOR-API] Error: {e}", exc_info=True)
            logger.error(f"[COORDINATOR-API] Error: {e}", exc_info=True)
            resp = jsonify({"success": False, "error": f"Server error: {str(e)[:100]}"})
            resp.headers['Content-Type'] = 'application/json'
            return resp, 500
    
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
                    db.session.flush()  # Flush to get attendance.id
                
                attendance.check_in_time = now
                attendance.check_in_latitude = latitude
                attendance.check_in_longitude = longitude
                
                db.session.commit()
                
                # Save photo to AttendancePhoto model if provided
                if photo_base64:
                    try:
                        # Check if photo record exists
                        photo_record = AttendancePhoto.query.filter_by(attendance_id=attendance.id).first()
                        if not photo_record:
                            photo_record = AttendancePhoto(
                                attendance_id=attendance.id,
                                employee_id=employee_id,
                                file_path="",
                                image_data=photo_base64,
                                original_filename="coordinator_checkin.jpg",
                                mime_type="image/jpeg",
                                ip_address=request.remote_addr or "unknown"
                            )
                            db.session.add(photo_record)
                        else:
                            photo_record.image_data = photo_base64
                        db.session.commit()
                        logger.info(f"[COORDINATOR-API] Photo saved for check-in: {employee_id}")
                    except Exception as e:
                        logger.error(f"[COORDINATOR-API] Photo save error: {e}")
                        db.session.rollback()
                
                logger.info(f"[COORDINATOR-API] Check-in: {employee_id}")
                
                # Convert to IST for display
                try:
                    import pytz
                    IST = pytz.timezone('Asia/Kolkata')
                    ist_time = now.replace(tzinfo=pytz.utc).astimezone(IST)
                    display_time = ist_time.strftime('%H:%M:%S')
                except Exception:
                    display_time = now.strftime('%H:%M:%S')
                
                return jsonify({
                    "success": True,
                    "message": "Check-in recorded",
                    "time": display_time
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
                
                # Calculate attendance status based on working hours and shift timing
                calculate_attendance_status(attendance, employee_id)
                
                db.session.commit()
                
                # Save checkout photo to AttendancePhoto model if provided
                if photo_base64:
                    try:
                        # Get or create photo record
                        photo_record = AttendancePhoto.query.filter_by(attendance_id=attendance.id).first()
                        if not photo_record:
                            photo_record = AttendancePhoto(
                                attendance_id=attendance.id,
                                employee_id=employee_id,
                                file_path="",
                                checkout_image_data=photo_base64,
                                original_filename="coordinator_checkout.jpg",
                                mime_type="image/jpeg",
                                ip_address=request.remote_addr or "unknown"
                            )
                            db.session.add(photo_record)
                        else:
                            photo_record.checkout_image_data = photo_base64
                        db.session.commit()
                        logger.info(f"[COORDINATOR-API] Photo saved for check-out: {employee_id}")
                    except Exception as e:
                        logger.error(f"[COORDINATOR-API] Checkout photo save error: {e}")
                        db.session.rollback()
                
                logger.info(f"[COORDINATOR-API] Check-out: {employee_id}")
                
                # Convert to IST for display
                try:
                    IST = pytz.timezone('Asia/Kolkata')
                    ist_time = now.replace(tzinfo=pytz.utc).astimezone(IST)
                    display_time = ist_time.strftime('%H:%M:%S')
                except Exception:
                    display_time = now.strftime('%H:%M:%S')
                
                return jsonify({
                    "success": True,
                    "message": "Check-out recorded",
                    "time": display_time
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

    @app.route("/coordinator/api/get-attendance-status", methods=["POST"])
    @csrf.exempt
    def coordinator_api_get_attendance_status():
        """Get attendance status for today - PUBLIC API, NO AUTH REQUIRED"""
        try:
            data = request.get_json(force=True, silent=True) or {}
            employee_id = data.get("employee_id")
            
            if not employee_id:
                return jsonify({"success": False, "error": "Employee ID required"}), 400
            
            today = date.today()
            attendance = Attendance.query.filter_by(
                employee_id=employee_id,
                date=today
            ).first()
            
            if not attendance:
                return jsonify({"success": False, "error": "No attendance record found"}), 404
            
            response_data = {
                "success": True,
                "attendance": {
                    "status": attendance.status,
                    "is_late": attendance.is_late,
                    "late_minutes": attendance.late_minutes or 0,
                    "is_half_day": attendance.is_half_day,
                    "is_early_leave": attendance.is_early_leave,
                    "working_minutes": attendance.working_minutes or 0
                }
            }
            
            return jsonify(response_data), 200
            
        except Exception as e:
            logger.error(f"[COORDINATOR-API] get-attendance-status error: {e}")
            return jsonify({"success": False, "error": "Server error"}), 500
    
    app.logger.info("✓ Registered /coordinator/api/get-attendance-status")
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
