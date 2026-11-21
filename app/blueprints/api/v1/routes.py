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
# ---------------------------------------------------------------------------
# Attendance Kiosk & Server Time
# ---------------------------------------------------------------------------

@api_bp.route("/server-time", methods=["GET"])
def server_time():
    """Server-synchronized digital time in Asia/Kolkata timezone."""
    from zoneinfo import ZoneInfo
    from datetime import datetime
    tz = ZoneInfo("Asia/Kolkata")
    now = datetime.now(tz)
    return jsonify({
        "success": True,
        "iso": now.isoformat(),
        "epoch_ms": int(now.timestamp() * 1000),
        "date_str": now.strftime("%A, %d %B %Y"),
        "time_str": now.strftime("%I:%M:%S %p"),
        "timezone": "Asia/Kolkata"
    })


@api_bp.route("/kiosk", methods=["GET"])
def kiosk():
    """Attendance Kiosk Terminal UI."""
    return render_template("attendance/kiosk.html")


@api_bp.route("/kiosk/debug-employees", methods=["GET"])
def debug_employees():
    """DEBUG ONLY: List all I-prefix employees in the system."""
    try:
        from app.models.employee_master import EmployeeMaster
        
        # Get all I-prefix employees
        i_employees = EmployeeMaster.query.filter(
            EmployeeMaster.employee_code.like("I-%")
        ).order_by(EmployeeMaster.employee_code).limit(20).all()
        
        results = []
        for emp in i_employees:
            results.append({
                "code": emp.employee_code,
                "name": emp.employee_name,
                "is_active": emp.is_active,
                "is_registered": emp.is_registered
            })
        
        return jsonify({
            "success": True,
            "count": len(results),
            "i_prefix_employees": results,
            "message": f"Found {len(results)} I-prefix employees"
        })
    except Exception as e:
        import traceback
        import sys
        traceback.print_exc(file=sys.stderr)
        return jsonify({
            "success": False,
            "message": f"Debug query failed: {str(e)}"
        }), 500

@api_bp.route("/kiosk/employee", methods=["GET"])
def kiosk_employee():
    """
    Lookup employee by code from the kiosk.
    Searches in both Employee and EmployeeMaster tables.
    Returns today's punch status and enforces 2-minute repeat punch buffer warning.
    """
    code = request.args.get("code", "").strip().upper()
    if not code:
        return jsonify({"success": False, "message": "Employee code required"}), 400

    try:
        from zoneinfo import ZoneInfo
        from datetime import datetime
        from app.blueprints.employees.repository import EmployeeRepository
        from app.models.employee_master import EmployeeMaster
        from app.models.attendance import Attendance
        from app.models.attendance_master import AttendanceMaster

        emp_repo = EmployeeRepository()
        tz = ZoneInfo("Asia/Kolkata")
        now_kolkata = datetime.now(tz)
        today = now_kolkata.date()

        emp_info = None
        is_master = False
        att_record = None

        # Try Employee table first
        employee = emp_repo.get_by_employee_code(code)
        if employee:
            emp_info = {
                "id": employee.id,
                "code": employee.employee_code,
                "name": employee.full_name,
                "department": employee.department or "General",
                "designation": employee.designation or "Staff",
                "location": getattr(employee, "location", None) or "Hospital Site",
                "shift": getattr(employee, "shift_timing", None) or "Standard Shift",
            }
            att_record = Attendance.query.filter_by(employee_id=employee.id, date=today).first()
        else:
            # Try EmployeeMaster table
            emp_master = EmployeeMaster.query.filter_by(employee_code=code).first()
            if not emp_master and code.startswith("I-"):
                e_code = code.replace("I-", "E-", 1)
                emp_master = EmployeeMaster.query.filter_by(employee_code=e_code).first()
            elif not emp_master and code.startswith("E-"):
                i_code = code.replace("E-", "I-", 1)
                emp_master = EmployeeMaster.query.filter_by(employee_code=i_code).first()

            if emp_master:
                is_master = True
                emp_info = {
                    "id": emp_master.id,
                    "code": emp_master.employee_code,
                    "name": emp_master.employee_name,
                    "department": emp_master.department or "General",
                    "designation": emp_master.designation or "Staff",
                    "location": emp_master.working_location or "Hospital Site",
                    "shift": emp_master.shift_timing or "Standard Shift",
                }
                att_record = AttendanceMaster.query.filter_by(employee_master_id=emp_master.id, date=today).first()

        if not emp_info:
            return jsonify({
                "success": False,
                "message": f"Employee code '{code}' not found in employee registry."
            }), 404

        # Calculate today's status and 2-minute buffer
        has_in = bool(att_record and att_record.check_in_time)
        has_out = bool(att_record and att_record.check_out_time)

        in_time_str = None
        if has_in and att_record.check_in_time:
            dt_in = att_record.check_in_time
            if dt_in.tzinfo is None:
                dt_in = dt_in.replace(tzinfo=tz)
            in_time_str = dt_in.strftime("%I:%M %p")

        out_time_str = None
        if has_out and att_record.check_out_time:
            dt_out = att_record.check_out_time
            if dt_out.tzinfo is None:
                dt_out = dt_out.replace(tzinfo=tz)
            out_time_str = dt_out.strftime("%I:%M %p")

        suggested_action = "checkin"
        can_punch = True
        buffer_warning = None

        if has_in and not has_out:
            suggested_action = "checkout"
            dt_in = att_record.check_in_time
            if dt_in.tzinfo is None:
                dt_in = dt_in.replace(tzinfo=tz)
            elapsed_sec = (now_kolkata - dt_in).total_seconds()
            if elapsed_sec < 120:
                can_punch = False
                wait_sec = int(120 - elapsed_sec)
                buffer_warning = f"Already punched IN at {in_time_str}. Please wait {wait_sec}s before checking OUT."
        elif has_in and has_out:
            suggested_action = "completed"
            dt_out = att_record.check_out_time
            if dt_out.tzinfo is None:
                dt_out = dt_out.replace(tzinfo=tz)
            elapsed_sec = (now_kolkata - dt_out).total_seconds()
            if elapsed_sec < 120:
                can_punch = False
                wait_sec = int(120 - elapsed_sec)
                buffer_warning = f"Already punched OUT at {out_time_str}. Please wait {wait_sec}s."
            else:
                can_punch = False
                buffer_warning = f"Attendance already completed for today (Punched OUT at {out_time_str})."

        return jsonify({
            "success": True,
            "employee": emp_info,
            "today_status": {
                "has_checked_in": has_in,
                "has_checked_out": has_out,
                "check_in_time": in_time_str,
                "check_out_time": out_time_str,
                "suggested_action": suggested_action,
                "can_punch": can_punch,
                "buffer_warning": buffer_warning
            },
            "message": f"Found: {emp_info['name']}"
        })

    except Exception as e:
        import traceback, sys
        traceback.print_exc(file=sys.stderr)
        return jsonify({"success": False, "message": f"Lookup failed: {str(e)}"}), 500


@api_bp.route("/kiosk/attendance", methods=["POST"])
def kiosk_attendance():
    """
    Submit attendance from the kiosk.
    Server time only (Asia/Kolkata).
    Enforces 2-minute repeat punch buffer window.
    """
    from zoneinfo import ZoneInfo
    from datetime import datetime
    from app.blueprints.employees.repository import EmployeeRepository
    from app.blueprints.attendance.repository import AttendanceRepository
    from app.models.attendance import Attendance
    from app.models.attendance_photo import AttendancePhoto
    from app.models.attendance_master import AttendanceMaster
    from app.models.attendance_master_photo import AttendanceMasterPhoto
    from app.models.employee_master import EmployeeMaster
    from app.extensions.database import db

    data = request.get_json() or {}
    code = data.get("employee_code", "").strip().upper()
    check_type = data.get("check_type", "auto").lower()
    latitude = data.get("latitude", 0.0)
    longitude = data.get("longitude", 0.0)
    accuracy = data.get("accuracy", 10.0)
    photo_b64 = data.get("photo_base64")

    if not code or not photo_b64:
        return jsonify({"success": False, "message": "Employee code and photo are required."}), 400

    try:
        tz = ZoneInfo("Asia/Kolkata")
        now_kolkata = datetime.now(tz)
        today = now_kolkata.date()

        emp_repo = EmployeeRepository()
        employee = emp_repo.get_by_employee_code(code)
        emp_master = None
        use_master = False

        if employee:
            emp_name = employee.full_name
            emp_id = employee.id
            att = Attendance.query.filter_by(employee_id=emp_id, date=today).first()
            if not att:
                att = Attendance(employee_id=emp_id, date=today, status="present")
                db.session.add(att)
                db.session.flush()
        else:
            emp_master = EmployeeMaster.query.filter_by(employee_code=code).first()
            if not emp_master and code.startswith("I-"):
                e_code = code.replace("I-", "E-", 1)
                emp_master = EmployeeMaster.query.filter_by(employee_code=e_code).first()
            elif not emp_master and code.startswith("E-"):
                i_code = code.replace("E-", "I-", 1)
                emp_master = EmployeeMaster.query.filter_by(employee_code=i_code).first()

            if not emp_master:
                return jsonify({"success": False, "message": f"Employee {code} not found."}), 404

            use_master = True
            emp_name = emp_master.employee_name
            att = AttendanceMaster.query.filter_by(employee_master_id=emp_master.id, date=today).first()
            if not att:
                att = AttendanceMaster(
                    employee_master_id=emp_master.id,
                    employee_code=code,
                    date=today,
                    status="present"
                )
                db.session.add(att)
                db.session.flush()

        # Determine check_type if 'auto'
        if check_type not in ("checkin", "checkout"):
            check_type = "checkout" if att.check_in_time and not att.check_out_time else "checkin"

        # Enforce 2-minute buffer logic
        if check_type == "checkin":
            if att.check_in_time:
                dt_in = att.check_in_time
                if dt_in.tzinfo is None:
                    dt_in = dt_in.replace(tzinfo=tz)
                elapsed = (now_kolkata - dt_in).total_seconds()
                in_str = dt_in.strftime("%I:%M %p")
                if elapsed < 120:
                    wait_sec = int(120 - elapsed)
                    return jsonify({
                        "success": False,
                        "message": f"Already punched IN at {in_str}. Please wait {wait_sec}s between punches."
                    }), 400
                return jsonify({
                    "success": False,
                    "message": f"You have already checked in today at {in_str}."
                }), 400

            att.check_in_time = now_kolkata
            if hasattr(att, "check_in_latitude"):
                att.check_in_latitude = latitude
                att.check_in_longitude = longitude
                att.check_in_accuracy = accuracy

            # ── 20-min buffer & 3-Late-Marks Policy for Kiosk ──
            try:
                from app.models.office_settings import OfficeSettings
                from app.blueprints.attendance.attendance_engine import compute_check_in_meta
                office = OfficeSettings.query.filter_by(is_deleted=False).first()
                is_late, late_minutes = compute_check_in_meta(now_kolkata.replace(tzinfo=None), office, emp.id, today)
                att.is_late = is_late
                att.late_minutes = late_minutes

                if is_late:
                    month_start = today.replace(day=1)
                    prev_lates = Attendance.query.filter(
                        Attendance.employee_id == emp.id,
                        Attendance.date >= month_start,
                        Attendance.date < today,
                        Attendance.is_late == True,
                        Attendance.is_deleted == False
                    ).count()
                    total_lates_this_month = prev_lates + 1

                    if total_lates_this_month % 3 == 0:
                        att.is_half_day = True
                        att.status = "half_day"

                    from app.services.email_notification_service import send_late_warning_notification
                    punch_time_display = now_kolkata.strftime("%I:%M %p")
                    shift_str = office.office_start_time.strftime("%I:%M %p") if office else "09:00 AM"
                    send_late_warning_notification(
                        employee=emp,
                        attendance=att,
                        late_count=total_lates_this_month,
                        late_minutes=late_minutes,
                        punch_time_str=punch_time_display,
                        shift_start_str=shift_str,
                    )
            except Exception as late_err:
                pass
        else: # checkout
            if not att.check_in_time:
                return jsonify({"success": False, "message": "You must check in before checking out."}), 400

            dt_in = att.check_in_time
            if dt_in.tzinfo is None:
                dt_in = dt_in.replace(tzinfo=tz)
            elapsed_since_in = (now_kolkata - dt_in).total_seconds()
            in_str = dt_in.strftime("%I:%M %p")

            if elapsed_since_in < 120:
                wait_sec = int(120 - elapsed_since_in)
                return jsonify({
                    "success": False,
                    "message": f"Punched IN at {in_str}. Please wait {wait_sec}s before checking OUT."
                }), 400

            if att.check_out_time:
                dt_out = att.check_out_time
                if dt_out.tzinfo is None:
                    dt_out = dt_out.replace(tzinfo=tz)
                out_str = dt_out.strftime("%I:%M %p")
                return jsonify({
                    "success": False,
                    "message": f"You have already checked out today at {out_str}."
                }), 400

            att.check_out_time = now_kolkata
            if hasattr(att, "check_out_latitude"):
                att.check_out_latitude = latitude
                att.check_out_longitude = longitude
                att.check_out_accuracy = accuracy
            if att.check_in_time and hasattr(att, "working_minutes"):
                try:
                    diff_mins = int((now_kolkata - dt_in).total_seconds() // 60)
                    att.working_minutes = max(1, diff_mins)
                except Exception:
                    pass

        # Store Photo
        if use_master:
            photo = AttendanceMasterPhoto.query.filter_by(attendance_master_id=att.id).first()
            if not photo:
                photo = AttendanceMasterPhoto(
                    attendance_master_id=att.id,
                    employee_master_id=emp_master.id
                )
                db.session.add(photo)
            if check_type == "checkin":
                photo.image_data = photo_b64
            else:
                photo.checkout_image_data = photo_b64
        else:
            photo = AttendancePhoto.query.filter_by(attendance_id=att.id).first()
            if not photo:
                photo = AttendancePhoto(attendance_id=att.id, employee_id=emp_id)
                db.session.add(photo)
            if check_type == "checkin":
                photo.image_data = photo_b64
            else:
                photo.checkout_image_data = photo_b64

        db.session.commit()

        # Calculate duration if checkout
        duration_str = "Recorded"
        if check_type == "checkout" and att.check_in_time and att.check_out_time:
            t1 = att.check_in_time if att.check_in_time.tzinfo else att.check_in_time.replace(tzinfo=tz)
            t2 = att.check_out_time if att.check_out_time.tzinfo else att.check_out_time.replace(tzinfo=tz)
            total_seconds = max(0, int((t2 - t1).total_seconds()))
            hrs = total_seconds // 3600
            mins = (total_seconds % 3600) // 60
            duration_str = f"{hrs}h {mins}m worked"

        time_str = now_kolkata.strftime("%I:%M %p")
        greeting = f"Welcome, {emp_name}!" if check_type == "checkin" else f"Goodbye, {emp_name}!"

        return jsonify({
            "success": True,
            "check_type": check_type,
            "message": f"{greeting} {check_type.upper()} recorded at {time_str}.",
            "time": time_str,
            "duration": duration_str,
            "attendance_id": att.id,
            "employee": {
                "code": code,
                "name": emp_name
            },
            "turnaround_ms": 4000
        })

    except Exception as e:
        db.session.rollback()
        import traceback, sys
        traceback.print_exc(file=sys.stderr)
        return jsonify({"success": False, "message": f"Attendance submission failed: {str(e)}"}), 500
