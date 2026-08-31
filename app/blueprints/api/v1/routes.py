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
    """Attendance Kiosk - 4-step flow"""
    from flask import Response
    kiosk_html = """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Attendance Kiosk — Smart HRMS</title>
  <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/bootstrap-icons@1.11.3/font/bootstrap-icons.min.css">
  <style>
    * { margin: 0; padding: 0; box-sizing: border-box; }
    body {
      font-family: 'Inter', system-ui, sans-serif;
      background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
      min-height: 100vh;
      display: flex;
      align-items: center;
      justify-content: center;
      padding: 20px;
    }
    .kiosk-container {
      background: white;
      border-radius: 12px;
      box-shadow: 0 20px 60px rgba(0,0,0,0.3);
      max-width: 500px;
      width: 100%;
      overflow: hidden;
    }
    .kiosk-header {
      background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
      color: white;
      padding: 24px;
      text-align: center;
    }
    .kiosk-header h1 {
      font-size: 1.8rem;
      margin-bottom: 8px;
    }
    .kiosk-header p {
      font-size: 0.9rem;
      opacity: 0.9;
    }
    .step-indicator {
      display: flex;
      justify-content: space-between;
      padding: 20px 24px;
      background: #f8f9fa;
      border-bottom: 1px solid #e0e0e0;
    }
    .step { text-align: center; flex: 1; }
    .step-number {
      display: inline-flex;
      align-items: center;
      justify-content: center;
      width: 40px;
      height: 40px;
      border-radius: 50%;
      background: #e0e0e0;
      color: #666;
      font-weight: 600;
      margin-bottom: 8px;
    }
    .step.active .step-number {
      background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
      color: white;
    }
    .step-label {
      font-size: 0.75rem;
      color: #999;
      font-weight: 500;
    }
    .step.active .step-label {
      color: #667eea;
      font-weight: 600;
    }
    .kiosk-content { padding: 32px 24px; }
    .step-panel { display: none; }
    .step-panel.active { display: block; }
    .input-group { margin-bottom: 16px; }
    .input-label {
      display: block;
      font-size: 0.85rem;
      font-weight: 600;
      color: #333;
      margin-bottom: 8px;
    }
    .input-field {
      width: 100%;
      padding: 12px;
      border: 2px solid #e0e0e0;
      border-radius: 6px;
      font-size: 1rem;
      font-family: inherit;
    }
    .input-field:focus { outline: none; border-color: #667eea; }
    .employee-card {
      background: #f0f4ff;
      border: 2px solid #667eea;
      border-radius: 8px;
      padding: 16px;
      margin-bottom: 16px;
      text-align: center;
    }
    .employee-avatar {
      width: 60px;
      height: 60px;
      border-radius: 50%;
      background: #667eea;
      color: white;
      display: inline-flex;
      align-items: center;
      justify-content: center;
      font-size: 1.8rem;
      margin-bottom: 12px;
    }
    .employee-name {
      font-size: 1.1rem;
      font-weight: 700;
      color: #333;
      margin-bottom: 4px;
    }
    .employee-info {
      font-size: 0.85rem;
      color: #666;
    }
    video { width: 100%; border-radius: 8px; margin-bottom: 16px; }
    .btn-group {
      display: flex;
      gap: 10px;
      margin-bottom: 12px;
    }
    .btn {
      flex: 1;
      padding: 12px 16px;
      border: none;
      border-radius: 6px;
      font-size: 0.9rem;
      font-weight: 600;
      cursor: pointer;
      font-family: inherit;
    }
    .btn-primary {
      background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
      color: white;
    }
    .btn-secondary {
      background: #e0e0e0;
      color: #333;
    }
    .btn-full { width: 100%; }
    .error-message {
      background: #fee;
      border: 1px solid #fcc;
      border-left: 4px solid #f00;
      color: #c00;
      padding: 12px;
      border-radius: 4px;
      margin-bottom: 16px;
      font-size: 0.9rem;
      display: none;
    }
    .check-buttons {
      display: flex;
      gap: 12px;
    }
    .check-buttons button {
      flex: 1;
      padding: 14px;
      font-size: 1rem;
      font-weight: 600;
      border: none;
      border-radius: 6px;
      cursor: pointer;
    }
    .check-in {
      background: linear-gradient(135deg, #10b981 0%, #059669 100%);
      color: white;
    }
    .check-out {
      background: linear-gradient(135deg, #f59e0b 0%, #d97706 100%);
      color: white;
    }
  </style>
</head>
<body>
<div class="kiosk-container">
  <div class="kiosk-header">
    <h1><i class="bi bi-clock-history"></i> Attendance Kiosk</h1>
    <p>Mark your attendance in 4 simple steps</p>
  </div>

  <div class="step-indicator">
    <div class="step active" id="step-indicator-1">
      <div class="step-number">1</div>
      <div class="step-label">Code</div>
    </div>
    <div class="step" id="step-indicator-2">
      <div class="step-number">2</div>
      <div class="step-label">Details</div>
    </div>
    <div class="step" id="step-indicator-3">
      <div class="step-number">3</div>
      <div class="step-label">Photo</div>
    </div>
    <div class="step" id="step-indicator-4">
      <div class="step-number">4</div>
      <div class="step-label">Submit</div>
    </div>
  </div>

  <div class="kiosk-content">
    <!-- STEP 1 -->
    <div class="step-panel active" id="panel-1">
      <h2 style="font-size:1.2rem;margin-bottom:16px">Step 1: Enter Employee Code</h2>
      <div class="input-group">
        <label class="input-label">Your Employee Code</label>
        <input type="text" id="employee-code" class="input-field" placeholder="e.g., E-2603025" autocomplete="off">
      </div>
      <div id="error-1" class="error-message"></div>
      <button class="btn btn-primary btn-full" onclick="nextStep(1)">Continue</button>
    </div>

    <!-- STEP 2 -->
    <div class="step-panel" id="panel-2">
      <h2 style="font-size:1.2rem;margin-bottom:16px">Step 2: Verify Your Details</h2>
      <div id="loading-2" style="display:none;text-align:center;padding:20px">
        <p style="color:#666">Loading employee details...</p>
      </div>
      <div id="employee-display" style="display:none">
        <div class="employee-card">
          <div class="employee-avatar"><i class="bi bi-person-fill"></i></div>
          <div class="employee-name" id="emp-name"></div>
          <div class="employee-info" id="emp-dept"></div>
          <div class="employee-info" id="emp-desg"></div>
        </div>
      </div>
      <div id="error-2" class="error-message"></div>
      <div class="btn-group">
        <button class="btn btn-secondary" onclick="prevStep(2)">Back</button>
        <button class="btn btn-primary" onclick="nextStep(2)">Take Photo</button>
      </div>
    </div>

    <!-- STEP 3 -->
    <div class="step-panel" id="panel-3">
      <h2 style="font-size:1.2rem;margin-bottom:16px">Step 3: Take Your Photo</h2>
      <video id="camera-preview" autoplay playsinline></video>
      <canvas id="photo-canvas" style="display:none"></canvas>
      <div id="captured-photo" style="display:none">
        <img id="photo-preview" style="width:100%;border-radius:8px;margin-bottom:16px">
      </div>
      <div id="error-3" class="error-message"></div>
      <div class="btn-group" id="camera-buttons">
        <button class="btn btn-secondary" onclick="prevStep(3)">Back</button>
        <button class="btn btn-primary" onclick="capturePhoto()">Capture</button>
      </div>
      <div class="btn-group" id="retake-buttons" style="display:none">
        <button class="btn btn-secondary" onclick="retakePhoto()">Retake</button>
        <button class="btn btn-primary" onclick="nextStep(3)">Use Photo</button>
      </div>
    </div>

    <!-- STEP 4 -->
    <div class="step-panel" id="panel-4">
      <h2 style="font-size:1.2rem;margin-bottom:16px">Step 4: Mark Attendance</h2>
      <div class="employee-card" style="margin-bottom:24px">
        <div style="font-size:0.9rem;color:#666;margin-bottom:8px">Submitting for:</div>
        <div class="employee-name" id="emp-name-4" style="font-size:1rem"></div>
      </div>
      <div id="error-4" class="error-message"></div>
      <div class="check-buttons" id="check-buttons">
        <button class="check-in" onclick="submitAttendance('checkin')">Check In</button>
        <button class="check-out" onclick="submitAttendance('checkout')">Check Out</button>
      </div>
    </div>
  </div>
</div>

<script>
let currentStep = 1, employeeData = null, photoBase64 = null;

function updateStepIndicator() {
  for (let i = 1; i <= 4; i++) {
    document.getElementById(`step-indicator-${i}`).classList.toggle('active', i === currentStep);
  }
}

function nextStep(step) {
  if (step === 1) {
    const code = document.getElementById('employee-code').value.trim().toUpperCase();
    if (!code) { showError(1, 'Enter employee code'); return; }
    loadEmployee(code);
  } else if (step === 2) {
    startCamera();
    currentStep = 3;
    showPanel(3);
  } else if (step === 3) {
    currentStep = 4;
    showPanel(4);
    if (employeeData) document.getElementById('emp-name-4').textContent = employeeData.name;
  }
  updateStepIndicator();
}

function prevStep(step) {
  if (step === 2) currentStep = 1;
  else if (step === 3) { stopCamera(); currentStep = 2; }
  showPanel(currentStep);
  updateStepIndicator();
}

function showPanel(n) {
  for (let i = 1; i <= 4; i++) document.getElementById(`panel-${i}`).classList.toggle('active', i === n);
}

function showError(step, msg) {
  const err = document.getElementById(`error-${step}`);
  err.textContent = msg;
  err.style.display = 'block';
}

async function loadEmployee(code) {
  const loading = document.getElementById('loading-2');
  const display = document.getElementById('employee-display');
  loading.style.display = 'block';
  display.style.display = 'none';
  
  try {
    const res = await fetch(`/api/v1/kiosk/employee?code=${code}`);
    const data = await res.json();
    if (data.success) {
      employeeData = data.employee;
      document.getElementById('emp-name').textContent = data.employee.name;
      document.getElementById('emp-dept').textContent = `Dept: ${data.employee.department}`;
      document.getElementById('emp-desg').textContent = `Role: ${data.employee.designation}`;
      loading.style.display = 'none';
      display.style.display = 'block';
      currentStep = 2;
      showPanel(2);
      updateStepIndicator();
    } else {
      showError(1, data.message || 'Not found');
      loading.style.display = 'none';
    }
  } catch (e) {
    showError(1, `Error: ${e.message}`);
    loading.style.display = 'none';
  }
}

async function startCamera() {
  try {
    const stream = await navigator.mediaDevices.getUserMedia({ video: { facingMode: 'user' }, audio: false });
    document.getElementById('camera-preview').srcObject = stream;
  } catch (e) {
    showError(3, `Camera error: ${e.message}`);
  }
}

function stopCamera() {
  const video = document.getElementById('camera-preview');
  if (video.srcObject) video.srcObject.getTracks().forEach(t => t.stop());
}

function capturePhoto() {
  const video = document.getElementById('camera-preview');
  const canvas = document.getElementById('photo-canvas');
  const ctx = canvas.getContext('2d');
  canvas.width = video.videoWidth;
  canvas.height = video.videoHeight;
  ctx.drawImage(video, 0, 0);
  photoBase64 = canvas.toDataURL('image/jpeg');
  document.getElementById('photo-preview').src = photoBase64;
  document.getElementById('camera-preview').style.display = 'none';
  document.getElementById('captured-photo').style.display = 'block';
  document.getElementById('camera-buttons').style.display = 'none';
  document.getElementById('retake-buttons').style.display = 'flex';
}

function retakePhoto() {
  document.getElementById('captured-photo').style.display = 'none';
  document.getElementById('camera-preview').style.display = 'block';
  document.getElementById('camera-buttons').style.display = 'flex';
  document.getElementById('retake-buttons').style.display = 'none';
  photoBase64 = null;
}

async function submitAttendance(type) {
  if (!employeeData || !photoBase64) { showError(4, 'Missing data'); return; }
  try {
    const res = await fetch('/api/v1/kiosk/attendance', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        employee_code: employeeData.code,
        check_type: type,
        latitude: 0, longitude: 0, accuracy: 100,
        photo_base64: photoBase64
      })
    });
    const data = await res.json();
    if (data.success) {
      alert('✓ ' + data.message);
      // Reset form for next employee
      setTimeout(() => {
        resetKiosk();
      }, 1000);
    } else {
      showError(4, data.message || 'Failed');
    }
  } catch (e) {
    showError(4, `Error: ${e.message}`);
  }
}

function resetKiosk() {
  // Clear all data
  employeeData = null;
  photoBase64 = null;
  currentStep = 1;
  
  // Clear input fields
  document.getElementById('employee-code').value = '';
  document.getElementById('photo-preview').src = '';
  document.getElementById('captured-photo').style.display = 'none';
  document.getElementById('camera-preview').style.display = 'block';
  document.getElementById('camera-buttons').style.display = 'flex';
  document.getElementById('retake-buttons').style.display = 'none';
  
  // Clear errors
  for (let i = 1; i <= 4; i++) {
    const err = document.getElementById(`error-${i}`);
    if (err) err.style.display = 'none';
  }
  
  // Reset to Step 1
  showPanel(1);
  updateStepIndicator();
  document.getElementById('employee-code').focus();
}

window.addEventListener('load', () => document.getElementById('employee-code').focus());
</script>
</body>
</html>"""
    return Response(kiosk_html, mimetype="text/html")


@api_bp.route("/kiosk/employee", methods=["GET"])
def kiosk_employee():
    """
    Lookup employee by code from the kiosk.
    Searches in both Employee and EmployeeMaster tables.
    """
    code = request.args.get("code", "").strip().upper()
    
    if not code:
        return jsonify({"success": False, "message": "Employee code required"}), 400
    
    try:
        from app.blueprints.employees.repository import EmployeeRepository
        from app.models.employee_master import EmployeeMaster
        
        emp_repo = EmployeeRepository()
        
        # Try Employee table first
        employee = emp_repo.get_by_employee_code(code)
        
        # If not found, try EmployeeMaster table
        if not employee:
            employee_master = EmployeeMaster.query.filter_by(employee_code=code, is_active=True).first()
            if employee_master:
                # Convert EmployeeMaster to Employee-like object for response
                return jsonify({
                    "success": True,
                    "employee": {
                        "id": employee_master.id,
                        "code": employee_master.employee_code,
                        "name": employee_master.employee_name,
                        "department": employee_master.department or "N/A",
                        "designation": employee_master.designation or "N/A",
                    },
                    "message": f"Found: {employee_master.employee_name}"
                })
            else:
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
            },
            "message": f"Found: {employee.full_name}"
        })
    
    except Exception as e:
        import traceback
        import sys
        traceback.print_exc(file=sys.stderr)
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
    from datetime import date, datetime
    
    data = request.get_json() or {}
    
    code = data.get("employee_code", "").upper()
    check_type = data.get("check_type", "checkin").lower()
    latitude = data.get("latitude")
    longitude = data.get("longitude")
    accuracy = data.get("accuracy")
    photo_b64 = data.get("photo_base64")
    
    # Validation - check for None/empty, NOT falsy (0 is valid for coords)
    if not code or not check_type or latitude is None or longitude is None or accuracy is None or not photo_b64:
        return jsonify({
            "success": False,
            "message": "Missing required fields"
        }), 400
    
    try:
        from app.blueprints.employees.repository import EmployeeRepository
        from app.blueprints.attendance.repository import AttendanceRepository
        from app.models.attendance_photo import AttendancePhoto
        from app.models.attendance_master_photo import AttendanceMasterPhoto
        from app.models.employee_master import EmployeeMaster
        from app.extensions.database import db
        
        emp_repo = EmployeeRepository()
        att_repo = AttendanceRepository()
        
        # Find employee - try Employee table first
        employee = emp_repo.get_by_employee_code(code)
        employee_name = None
        
        # If not found in Employee, try EmployeeMaster
        if not employee:
            employee_master = EmployeeMaster.query.filter_by(employee_code=code, is_active=True).first()
            if not employee_master:
                return jsonify({
                    "success": False,
                    "message": f"Employee {code} not found"
                }), 404
            # Store employee master name for response
            employee_name = employee_master.employee_name
            # For EmployeeMaster, we'll use master id as employee_id placeholder
            employee_id = None  # Will handle specially
            use_master = True
        else:
            employee_id = employee.id
            employee_name = employee.full_name
            use_master = False
        
        today = date.today()
        
        if use_master:
            # For EmployeeMaster employees, store in AttendanceMaster table
            from app.models.attendance_master import AttendanceMaster
            
            # Get or create attendance record for this employee_master and date
            attendance_master = AttendanceMaster.query.filter_by(
                employee_master_id=employee_master.id,
                date=today
            ).first()
            
            if not attendance_master:
                attendance_master = AttendanceMaster(
                    employee_master_id=employee_master.id,
                    employee_code=code,
                    date=today,
                    status="present"
                )
                db.session.add(attendance_master)
                db.session.flush()
            
            # Check if already checked in/out
            if check_type == "checkin":
                if attendance_master.check_in_time:
                    return jsonify({
                        "success": False,
                        "message": "You have already checked in today. Cannot check in twice."
                    }), 400
            else:  # checkout
                if attendance_master.check_out_time:
                    return jsonify({
                        "success": False,
                        "message": "You have already checked out today. Cannot check out twice."
                    }), 400
                if not attendance_master.check_in_time:
                    return jsonify({
                        "success": False,
                        "message": "You must check in before you can check out."
                    }), 400
            
            # Store check-in/out time
            now = datetime.now()
            
            if check_type == "checkin":
                attendance_master.check_in_time = now
                attendance_master.check_in_latitude = latitude
                attendance_master.check_in_longitude = longitude
                attendance_master.check_in_accuracy = accuracy
            else:
                attendance_master.check_out_time = now
                attendance_master.check_out_latitude = latitude
                attendance_master.check_out_longitude = longitude
                attendance_master.check_out_accuracy = accuracy
            
            # Store photo in AttendanceMasterPhoto (I-prefix photo table)
            photo = AttendanceMasterPhoto.query.filter_by(attendance_master_id=attendance_master.id).first()
            if not photo:
                photo = AttendanceMasterPhoto(
                    attendance_master_id=attendance_master.id,
                    employee_master_id=employee_master.id
                )
                db.session.add(photo)
            
            if check_type == "checkin":
                photo.image_data = photo_b64
            else:
                photo.checkout_image_data = photo_b64
            
            db.session.commit()
            
            return jsonify({
                "success": True,
                "message": f"{check_type.title()} recorded for {employee_name}",
                "attendance_id": attendance_master.id,
                "employee": {
                    "code": code,
                    "name": employee_name
                }
            })
        else:
            # Regular employee with full record
            attendance = att_repo.get_today(employee_id, today)
            if not attendance:
                from app.models.attendance import Attendance
                attendance = Attendance(
                    employee_id=employee_id,
                    date=today,
                    status="present"
                )
                db.session.add(attendance)
                db.session.flush()
            
            # Check if already checked in/out
            if check_type == "checkin":
                if attendance.check_in_time:
                    return jsonify({
                        "success": False,
                        "message": "You have already checked in today. Cannot check in twice."
                    }), 400
            else:  # checkout
                if attendance.check_out_time:
                    return jsonify({
                        "success": False,
                        "message": "You have already checked out today. Cannot check out twice."
                    }), 400
                if not attendance.check_in_time:
                    return jsonify({
                        "success": False,
                        "message": "You must check in before you can check out."
                    }), 400
            
            # Store check-in/out time
            now = datetime.now()
            
            if check_type == "checkin":
                attendance.check_in_time = now
            else:
                attendance.check_out_time = now
            
            # Store photo in AttendancePhoto (E-prefix photo table)
            photo = AttendancePhoto.query.filter_by(attendance_id=attendance.id).first()
            if not photo:
                photo = AttendancePhoto(
                    attendance_id=attendance.id,
                    employee_id=employee_id
                )
                db.session.add(photo)
            
            if check_type == "checkin":
                photo.image_data = photo_b64
            else:
                photo.checkout_image_data = photo_b64
            
            db.session.commit()
            
            return jsonify({
                "success": True,
                "message": f"{check_type.title()} recorded for {employee_name}",
                "attendance_id": attendance.id,
                "employee": {
                    "code": employee.employee_code,
                    "name": employee_name
                }
            })
    
    except Exception as e:
        try:
            db.session.rollback()
        except:
            pass
        import traceback
        import sys
        traceback.print_exc(file=sys.stderr)
        return jsonify({
            "success": False,
            "message": f"Attendance submission failed: {str(e)}"
        }), 500

