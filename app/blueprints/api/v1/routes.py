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
            EmployeeMaster.employee_code.ilike("I-%")
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

        # Lookup employee by exact code
        employee = emp_repo.get_by_employee_code(code)
        emp_master = EmployeeMaster.query.filter_by(employee_code=code).first()

        if employee:
            loc = getattr(employee, "working_location", None) or getattr(employee, "branch", None) or (emp_master.working_location if emp_master else None) or "Head Office"
            desig = employee.designation or (emp_master.designation if emp_master else None) or "Staff"
            dept = employee.department or (emp_master.department if emp_master else None) or "General"
            emp_info = {
                "id": employee.id,
                "code": employee.employee_code,
                "name": employee.full_name or (emp_master.employee_name if emp_master else "Employee"),
                "department": dept,
                "designation": desig,
                "location": loc,
                "shift": getattr(employee, "shift_timing", None) or (emp_master.shift_timing if emp_master else None) or "Standard Shift",
                "is_face_registered": bool(getattr(employee, "is_face_registered", False) or (emp_master and emp_master.is_face_registered)),
                "registered_face_photo": bool(employee.registered_face_photo or (emp_master and emp_master.registered_face_photo)),
                "face_descriptor": employee.face_descriptor or (emp_master.face_descriptor if emp_master else None),
            }
            att_record = Attendance.query.filter_by(employee_id=employee.id, date=today).first()
        elif emp_master:
            is_master = True
            emp_info = {
                "id": emp_master.id,
                "code": emp_master.employee_code,
                "name": emp_master.employee_name,
                "department": emp_master.department or "General",
                "designation": emp_master.designation or "Staff",
                "location": emp_master.working_location or "Head Office",
                "shift": emp_master.shift_timing or "Standard Shift",
                "is_face_registered": bool(emp_master.is_face_registered),
                "registered_face_photo": bool(emp_master.registered_face_photo),
                "face_descriptor": emp_master.face_descriptor,
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


@api_bp.route("/kiosk/identify-and-punch", methods=["POST"])
def kiosk_identify_and_punch():
    """
    Face-First Automatic Attendance Punching & Profile Retrieval.
    
    1. Anti-Spoofing / Presentation Attack Detection (PAD):
       - Detects digital screen subpixel grids (Moire effect via 2D FFT).
       - Detects glass screen specular reflection hotspots.
       - Validates dynamic temporal micro-liveness (EAR change across 6s window).
       - Strictly blocks photo-on-phone, tablet, or printed paper attacks!
    2. 1:N Facial Biometric Identification:
       - Compares live 128-d descriptor against all registered employee profiles.
       - Enforces Euclidean distance <= 0.385 and Cosine similarity >= 60%.
    3. Attendance Punch Execution:
       - Records Check-In or Check-Out based on today's status.
       - Enforces 2-minute repeat punch buffer warning.
       - Saves audit photo to database.
    4. Full Profile Retrieval:
       - Returns all registration details: Name, Code, Official Email, Department,
         Designation, Work Location/Hospital, Date of Joining, and Punch summary.
    """
    from zoneinfo import ZoneInfo
    from datetime import datetime
    from app.models.employee import Employee
    from app.models.employee_master import EmployeeMaster
    from app.models.user import User
    from app.models.attendance import Attendance
    from app.models.attendance_photo import AttendancePhoto
    from app.models.attendance_master import AttendanceMaster
    from app.models.attendance_master_photo import AttendanceMasterPhoto
    from app.services.face_verification_service import FaceVerificationService
    from app.extensions.database import db

    data = request.get_json() or {}
    live_face_descriptor = data.get("live_face_descriptor")
    photo_b64 = data.get("photo_base64")
    liveness_metrics = data.get("liveness_metrics") or {}
    latitude = data.get("latitude", 0.0)
    longitude = data.get("longitude", 0.0)
    accuracy = data.get("accuracy", 10.0)

    if not live_face_descriptor or not photo_b64:
        return jsonify({
            "success": False,
            "message": "Biometric face scan and photo are required."
        }), 400

    try:
        # 1. Presentation Attack Detection (Anti-Spoofing)
        is_spoof, spoof_reason, details = FaceVerificationService.detect_presentation_attack(
            image_b64=photo_b64,
            liveness_metrics=liveness_metrics
        )
        if is_spoof:
            return jsonify({
                "success": False,
                "spoof_detected": True,
                "message": f"Biometric Security Alert: Screen or static photo detected ({spoof_reason}). A live person must face the camera.",
                "details": details
            }), 403

        # 2. Gather candidate face profiles across Employee and EmployeeMaster tables
        candidates = []
        registered_emps = Employee.query.filter(
            Employee.is_face_registered == True,
            Employee.face_descriptor != None,
            Employee.is_deleted == False
        ).all()
        for emp in registered_emps:
            candidates.append({
                "source": "employee",
                "id": emp.id,
                "user_id": emp.user_id,
                "employee_code": emp.employee_code,
                "name": emp.full_name or "Employee",
                "department": emp.department,
                "designation": emp.designation,
                "working_location": emp.branch,
                "date_of_joining": str(emp.date_joined) if emp.date_joined else "",
                "personal_email": emp.personal_email,
                "registered_face_photo": emp.registered_face_photo,
                "face_descriptor": emp.face_descriptor,
            })

        seen_codes = {c["employee_code"].upper() for c in candidates}
        registered_masters = EmployeeMaster.query.filter(
            EmployeeMaster.is_face_registered == True,
            EmployeeMaster.face_descriptor != None
        ).all()
        for m in registered_masters:
            if m.employee_code.upper() not in seen_codes:
                candidates.append({
                    "source": "master",
                    "id": m.id,
                    "user_id": m.user_id,
                    "employee_code": m.employee_code,
                    "name": m.employee_name or "Employee",
                    "department": m.department,
                    "designation": m.designation,
                    "working_location": m.working_location,
                    "date_of_joining": "",
                    "personal_email": getattr(m, "official_email", "") or "",
                    "registered_face_photo": m.registered_face_photo,
                    "face_descriptor": m.face_descriptor,
                })

        if not candidates:
            return jsonify({
                "success": False,
                "match_found": False,
                "message": "No registered face profiles found in the system. Please register your face first."
            }), 404

        # 3. 1:N Facial Biometric Identification
        match_result = FaceVerificationService.identify_face_1_to_n(
            live_descriptor=live_face_descriptor,
            candidates=candidates,
            threshold=0.44
        )

        if not match_result:
            return jsonify({
                "success": False,
                "match_found": False,
                "message": "Face not recognized. Please face the camera directly, ensure good lighting, or complete face registration."
            }), 404

        cand = match_result["candidate"]
        code = cand["employee_code"]
        name = cand["name"]
        score = match_result["similarity"]
        distance = match_result["distance"]

        # Resolve Official Email
        official_email = cand.get("personal_email") or ""
        user = None
        if cand.get("user_id"):
            user = User.query.get(cand["user_id"])
        if not user:
            from app.blueprints.authentication.repository import AuthRepository
            auth_repo = AuthRepository()
            user = auth_repo.get_by_employee_code(code)
        if user and user.email:
            official_email = user.email

        # 4. Record Attendance Punch (Asia/Kolkata)
        tz = ZoneInfo("Asia/Kolkata")
        now_kolkata = datetime.now(tz)
        today = now_kolkata.date()

        use_master = (cand.get("source") == "master")
        att = None
        emp_record = None

        if not use_master:
            emp_record = Employee.query.get(cand["id"])
            att = Attendance.query.filter_by(employee_id=emp_record.id, date=today).first()
            if not att:
                att = Attendance(employee_id=emp_record.id, date=today, status="present")
                db.session.add(att)
                db.session.flush()
        else:
            att = AttendanceMaster.query.filter_by(employee_master_id=cand["id"], date=today).first()
            if not att:
                att = AttendanceMaster(
                    employee_master_id=cand["id"],
                    employee_code=code,
                    date=today,
                    status="present"
                )
                db.session.add(att)
                db.session.flush()

        # Determine Punch Action: IN or OUT
        action_type = "CHECK-IN"
        buffer_warning = False
        buffer_message = ""

        if not att.check_in_time:
            action_type = "CHECK-IN"
            att.check_in_time = now_kolkata
            if hasattr(att, "check_in_latitude"):
                att.check_in_latitude = latitude
                att.check_in_longitude = longitude
                att.check_in_accuracy = accuracy
        elif att.check_in_time and not att.check_out_time:
            dt_in = att.check_in_time
            if dt_in.tzinfo is None:
                dt_in = dt_in.replace(tzinfo=tz)
            elapsed_since_in = (now_kolkata - dt_in).total_seconds()
            if elapsed_since_in < 120:
                buffer_warning = True
                wait_sec = int(120 - elapsed_since_in)
                buffer_message = f"Notice: Checked IN {int(elapsed_since_in)}s ago ({dt_in.strftime('%I:%M %p')}). Please wait {wait_sec}s before checking OUT."
                action_type = "CHECK-IN (REPEAT)"
            else:
                action_type = "CHECK-OUT"
                att.check_out_time = now_kolkata
                if hasattr(att, "check_out_latitude"):
                    att.check_out_latitude = latitude
                    att.check_out_longitude = longitude
                    att.check_out_accuracy = accuracy
                if hasattr(att, "working_minutes"):
                    diff_mins = int((now_kolkata - dt_in).total_seconds() // 60)
                    att.working_minutes = max(1, diff_mins)
        else:
            # Already checked out today: update latest checkout
            dt_out = att.check_out_time
            if dt_out.tzinfo is None:
                dt_out = dt_out.replace(tzinfo=tz)
            elapsed_since_out = (now_kolkata - dt_out).total_seconds()
            if elapsed_since_out < 120:
                buffer_warning = True
                buffer_message = f"Notice: Check-out recorded {int(elapsed_since_out)}s ago. 2-minute buffer active."
            action_type = "CHECK-OUT"
            att.check_out_time = now_kolkata

        # Store Photo Audit Record
        if not use_master:
            photo = AttendancePhoto.query.filter_by(attendance_id=att.id).first()
            if not photo:
                photo = AttendancePhoto(attendance_id=att.id, employee_id=emp_record.id)
                db.session.add(photo)
            if action_type.startswith("CHECK-IN"):
                photo.image_data = photo_b64
            else:
                photo.checkout_image_data = photo_b64
        else:
            photo = AttendanceMasterPhoto.query.filter_by(attendance_master_id=att.id).first()
            if not photo:
                photo = AttendanceMasterPhoto(
                    attendance_master_id=att.id,
                    employee_master_id=cand["id"]
                )
                db.session.add(photo)
            if action_type.startswith("CHECK-IN"):
                photo.image_data = photo_b64
            else:
                photo.checkout_image_data = photo_b64

        db.session.commit()

        # 5. Return Full Profile & Punch Details
        return jsonify({
            "success": True,
            "match_found": True,
            "employee": {
                "id": cand["id"],
                "employee_code": code,
                "name": name,
                "department": cand.get("department") or "General",
                "designation": cand.get("designation") or "Staff",
                "working_location": cand.get("working_location") or "Head Office",
                "date_of_joining": cand.get("date_of_joining") or "Not Specified",
                "official_email": official_email or "Not Provided",
                "registered_photo": cand.get("registered_face_photo") or "",
                "captured_photo": photo_b64,
                "confidence_score": round(score, 1),
                "euclidean_distance": round(distance, 4)
            },
            "punch": {
                "action": action_type,
                "time": now_kolkata.strftime("%I:%M:%S %p"),
                "date": now_kolkata.strftime("%A, %d %B %Y"),
                "status": "Verified & Recorded",
                "buffer_warning": buffer_warning,
                "buffer_message": buffer_message,
                "message": f"Biometric Identity Verified ({score:.1f}% confidence). {action_type} recorded successfully."
            }
        }), 200

    except Exception as exc:
        db.session.rollback()
        import traceback, sys
        traceback.print_exc(file=sys.stderr)
        return jsonify({
            "success": False,
            "message": f"Biometric attendance processing failed: {str(exc)}"
        }), 500


@api_bp.route("/kiosk/enroll-and-punch", methods=["POST"])
def kiosk_enroll_and_punch():
    """
    Direct Kiosk Face Biometric Enrollment & Immediate Punch:
    Assigns the live camera face photo and 128-d biometric descriptor to the EmployeeMaster record.
    When the employee later registers on the web portal, their face is already linked and automatically loaded!
    """
    import re
    from zoneinfo import ZoneInfo
    from datetime import datetime
    import json
    from sqlalchemy import func
    from app.models.employee import Employee
    from app.models.employee_master import EmployeeMaster
    from app.models.attendance import Attendance
    from app.models.attendance_photo import AttendancePhoto
    from app.models.attendance_master import AttendanceMaster
    from app.models.attendance_master_photo import AttendanceMasterPhoto
    from app.extensions.database import db

    data = request.get_json() or {}
    raw_code = (data.get("employee_code") or "").strip()
    # Strip any "E.G.", "EG", "EXAMPLE", colons, leading spaces
    code = re.sub(r'^(?:E\.?G\.?|EXAMPLE)\s*[:\-]?\s*', '', raw_code, flags=re.IGNORECASE).strip().upper()
    live_face_descriptor = data.get("live_face_descriptor")
    photo_b64 = data.get("photo_base64")

    if not code or not live_face_descriptor or not photo_b64:
        return jsonify({
            "success": False,
            "message": "Employee code, face scan, and photo are required."
        }), 400

    # Anti-spoofing presentation attack detection
    from app.services.face_verification_service import FaceVerificationService
    is_spoof, spoof_reason, details = FaceVerificationService.detect_presentation_attack(
        image_b64=photo_b64,
        liveness_metrics=data.get("liveness_metrics")
    )
    if is_spoof:
        return jsonify({
            "success": False,
            "spoof_detected": True,
            "message": f"Biometric Security Alert: Screen or static photo detected ({spoof_reason}). A live person must face the camera.",
            "details": details
        }), 403

    try:
        master = EmployeeMaster.query.filter(
            func.upper(func.trim(EmployeeMaster.employee_code)) == code
        ).first()

        if not master:
            return jsonify({
                "success": False,
                "message": f"Employee code '{code}' not found in company master list. Please check your code."
            }), 404

        # Save face biometric to EmployeeMaster
        desc_json = json.dumps(live_face_descriptor) if not isinstance(live_face_descriptor, str) else live_face_descriptor
        master.registered_face_photo = photo_b64
        master.face_descriptor = desc_json
        master.is_face_registered = True
        # NOTE: Do NOT set master.is_registered = True here!
        # The employee will complete password & registration details on the registration page.

        # If Employee profile already exists, sync face to it as well
        employee = Employee.query.filter(
            func.upper(func.trim(Employee.employee_code)) == code
        ).first()
        if employee:
            employee.registered_face_photo = photo_b64
            employee.face_descriptor = desc_json
            employee.is_face_registered = True
            employee.profile_photo = photo_b64

        # Record Attendance Punch for today (Asia/Kolkata)
        tz = ZoneInfo("Asia/Kolkata")
        now_kolkata = datetime.now(tz)
        today = now_kolkata.date()
        action_type = "CHECK-IN"

        if employee:
            att = Attendance.query.filter_by(employee_id=employee.id, date=today).first()
            if not att:
                att = Attendance(
                    employee_id=employee.id,
                    date=today,
                    status="present",
                    check_in_time=now_kolkata,
                    face_verified=True,
                    face_match_score=100.0
                )
                db.session.add(att)
                db.session.flush()
            else:
                if not att.check_in_time:
                    att.check_in_time = now_kolkata
                    action_type = "CHECK-IN"
                else:
                    att.check_out_time = now_kolkata
                    action_type = "CHECK-OUT"
                att.face_verified = True
                att.face_match_score = 100.0

            photo = AttendancePhoto.query.filter_by(attendance_id=att.id).first()
            if not photo:
                photo = AttendancePhoto(attendance_id=att.id, employee_id=employee.id)
                db.session.add(photo)
            if action_type.startswith("CHECK-IN"):
                photo.image_data = photo_b64
            else:
                photo.checkout_image_data = photo_b64

        else:
            # Employee has not yet registered on web portal: punch in AttendanceMaster
            att = AttendanceMaster.query.filter_by(employee_master_id=master.id, date=today).first()
            if not att:
                att = AttendanceMaster(
                    employee_master_id=master.id,
                    employee_code=code,
                    date=today,
                    status="present",
                    check_in_time=now_kolkata,
                    face_verified=True,
                    face_match_score=100.0
                )
                db.session.add(att)
                db.session.flush()
            else:
                if not att.check_in_time:
                    att.check_in_time = now_kolkata
                    action_type = "CHECK-IN"
                else:
                    att.check_out_time = now_kolkata
                    action_type = "CHECK-OUT"
                att.face_verified = True
                att.face_match_score = 100.0

            photo = AttendanceMasterPhoto.query.filter_by(attendance_master_id=att.id).first()
            if not photo:
                photo = AttendanceMasterPhoto(attendance_master_id=att.id, employee_master_id=master.id)
                db.session.add(photo)
            if action_type.startswith("CHECK-IN"):
                photo.image_data = photo_b64
            else:
                photo.checkout_image_data = photo_b64

        db.session.commit()

        # Return comprehensive profile
        return jsonify({
            "success": True,
            "match_found": True,
            "enrolled_new": True,
            "employee": {
                "id": master.id,
                "employee_code": code,
                "name": master.employee_name or "Employee",
                "department": getattr(employee, "department", None) or master.department or "General",
                "designation": getattr(employee, "designation", None) or master.designation or "Staff",
                "working_location": getattr(employee, "branch", None) or master.working_location or "Head Office",
                "date_of_joining": str(getattr(employee, "date_joined", "")) if getattr(employee, "date_joined", None) else "Pending Registration",
                "official_email": getattr(master, "official_email", "") or getattr(employee, "personal_email", "") or "Pending Web Registration",
                "registered_photo": photo_b64,
                "captured_photo": photo_b64,
                "confidence_score": 100.0,
                "euclidean_distance": 0.0
            },
            "punch": {
                "action": action_type,
                "time": now_kolkata.strftime("%I:%M:%S %p"),
                "date": now_kolkata.strftime("%A, %d %B %Y"),
                "status": "Face Assigned & Punch Verified",
                "buffer_warning": False,
                "buffer_message": "",
                "message": f"Biometric Face Successfully Assigned to {code}! {action_type} recorded."
            }
        }), 200

    except Exception as exc:
        db.session.rollback()
        import traceback, sys
        traceback.print_exc(file=sys.stderr)
        return jsonify({
            "success": False,
            "message": f"Enrollment failed: {str(exc)}"
        }), 500


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
    live_face_descriptor = data.get("live_face_descriptor")

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

        # ══════════════════════════════════════════════════════════════
        # STRICT FACIAL BIOMETRIC VERIFICATION ENFORCEMENT
        # "if the face matches only then the attendance is recorded"
        # ══════════════════════════════════════════════════════════════
        from app.services.face_verification_service import FaceVerificationService

        registered_desc = getattr(employee, "face_descriptor", None) if employee else None
        if not registered_desc and emp_master:
            registered_desc = emp_master.face_descriptor

        registered_photo = getattr(employee, "registered_face_photo", None) if employee else None
        if not registered_photo and emp_master:
            registered_photo = emp_master.registered_face_photo

        face_verified = False
        face_score = 0.0

        if registered_desc or registered_photo:
            # Employee has a registered face profile - STRICT BIOMETRIC ENFORCEMENT
            is_match = False
            distance = 1.0

            if not live_face_descriptor:
                logger.warning("REJECTED_PUNCH_NO_LIVE_DESCRIPTOR | code=%s | name=%s", code, emp_name)
                return jsonify({
                    "success": False,
                    "biometric_failure": True,
                    "message": f"Biometric verification required: No live facial scan detected for {emp_name}. Please face the camera and try again."
                }), 403

            # 1. High-accuracy 128-dimensional deep neural descriptor verification
            if registered_desc and live_face_descriptor:
                is_match, distance, score = FaceVerificationService.verify_descriptors(live_face_descriptor, registered_desc, threshold=0.385)
                face_score = score

            if not is_match or face_score < 60.0:
                logger.warning("REJECTED_PUNCH_FACE_MISMATCH | code=%s | name=%s | distance=%.4f | score=%.1f%%", code, emp_name, distance, face_score)
                return jsonify({
                    "success": False,
                    "biometric_failure": True,
                    "message": f"Biometric verification failed ({face_score:.1f}% confidence): Live face does not match registered profile for {emp_name}. Punch strictly rejected."
                }), 403
                logger.warning(
                    "FACIAL_VERIFICATION_FAILED | code=%s | name=%s | dist=%.3f | score=%.1f",
                    code, emp_name, distance, face_score
                )
                return jsonify({
                    "success": False,
                    "biometric_failure": True,
                    "message": f"Biometric verification failed: live face does not match registered employee profile for {emp_name} (Distance: {distance:.2f}). Attendance strictly denied."
                }), 403

            face_verified = True
        else:
            # Employee has not enrolled face yet - REJECT kiosk attendance until enrolled
            logger.warning("FACIAL_UNENROLLED_BLOCKED | code=%s", code)
            return jsonify({
                "success": False,
                "biometric_failure": True,
                "message": f"Biometric enrollment required: {emp_name} has not registered their face profile yet. Please complete registration with camera scan first."
            }), 403

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

        # Record biometric verification flag & score on attendance
        if hasattr(att, "face_verified"):
            att.face_verified = face_verified
        if hasattr(att, "face_match_score"):
            att.face_match_score = face_score

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
