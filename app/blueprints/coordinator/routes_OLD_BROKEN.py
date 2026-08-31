"""
Coordinator attendance kiosk routes.
Coordinator-only portal for marking employee attendance.

Only authenticated user with employee_code = "E-2606026" can access these routes.
All attendance is marked AGAINST SELECTED EMPLOYEES, not the coordinator.
GPS/geofence verification uses COORDINATOR DEVICE location, not employee location.
"""

from datetime import datetime, date, timedelta
from flask import render_template, request, jsonify, redirect, url_for, abort, make_response
from flask_login import login_required, current_user
import logging
import random

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
from app.utils.datetime_utils import get_naive_ist

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

@coordinator_bp.route("/kiosk-fresh-v3", methods=["GET"])
@login_required  
def kiosk_fresh_v3():
    """BRAND NEW UNCACHED ROUTE - Cloudflare has never seen this URL"""
    _check_coordinator_authorization()
    
    import os
    import time
    
    cache_buster = str(int(time.time() * 1000))
    
    template_path = os.path.join(os.path.dirname(__file__), 'templates', 'coordinator', 'dashboard.html')
    with open(template_path, 'r', encoding='utf-8') as f:
        html = f.read()
    
    # Add MASSIVE visible indicator at the very top
    timestamp_marker = f'''<div style="position:fixed;top:0;left:0;right:0;background:red;color:white;padding:15px;z-index:99999;font-size:20px;font-weight:bold;text-align:center;border:5px solid yellow;">
    🟢 FRESH VERSION {cache_buster} | TIME: {datetime.now().strftime('%H:%M:%S')} | THIS IS THE NEW WORKING VERSION
    </div>
    <div style="height:80px;"></div><!-- spacer -->'''
    html = html.replace('<body>', '<body>' + timestamp_marker)
    
    resp = make_response(html)
    resp.headers['Content-Type'] = 'text/html; charset=utf-8'
    resp.headers['Content-Security-Policy'] = "default-src *; script-src * 'unsafe-inline' 'unsafe-eval'; style-src * 'unsafe-inline';"
    resp.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, max-age=0, private'
    resp.headers['Pragma'] = 'no-cache'
    resp.headers['Expires'] = '0'
    return resp


@coordinator_bp.route("/", methods=["GET"])
@login_required  
def dashboard():
    """Dashboard - Simple embedded working HTML"""
    _check_coordinator_authorization()
    
    html = '''<!DOCTYPE html>
<html><head><title>TEST</title></head>
<body>
<h1 style="color:red;font-size:50px;">🟢 IF YOU SEE THIS THE SERVER WORKS!</h1>
<button onclick="alert('Button works!')">TEST BUTTON</button>
<script>console.log('JavaScript works!');</script>
</body></html>'''
    
    resp = make_response(html)
    resp.headers['Cache-Control'] = 'no-store'
    return resp
    
    # Embedded HTML - bypasses all template caching
    html = f'''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Attendance Kiosk - WORKING VERSION</title>
    <meta http-equiv="Cache-Control" content="no-cache, no-store, must-revalidate">
    <meta http-equiv="Pragma" content="no-cache">
    <meta http-equiv="Expires" content="0">
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            display: flex;
            justify-content: center;
            align-items: center;
            padding: 20px;
        }}
        .cache-indicator {{
            position: fixed;
            top: 0;
            left: 0;
            right: 0;
            background: #ff0000;
            color: white;
            padding: 10px;
            text-align: center;
            font-size: 14px;
            font-weight: bold;
            z-index: 99999;
            border-bottom: 3px solid yellow;
        }}
        .kiosk-container {{
            background: white;
            border-radius: 15px;
            box-shadow: 0 10px 40px rgba(0, 0, 0, 0.3);
            max-width: 900px;
            width: 100%;
            padding: 40px;
            margin-top: 60px;
        }}
        .kiosk-header {{
            text-align: center;
            margin-bottom: 30px;
        }}
        .kiosk-header h1 {{
            font-size: 32px;
            color: #333;
            margin-bottom: 10px;
        }}
        .kiosk-header p {{
            font-size: 14px;
            color: #666;
        }}
        .step-indicator {{
            display: flex;
            justify-content: space-between;
            margin-bottom: 30px;
            overflow-x: auto;
        }}
        .step {{
            display: flex;
            flex-direction: column;
            align-items: center;
            min-width: 80px;
        }}
        .step-number {{
            width: 40px;
            height: 40px;
            border-radius: 50%;
            background: #ddd;
            color: #666;
            display: flex;
            align-items: center;
            justify-content: center;
            font-weight: bold;
            margin-bottom: 8px;
            transition: all 0.3s ease;
        }}
        .step.active .step-number {{
            background: #667eea;
            color: white;
            transform: scale(1.2);
        }}
        .step.completed .step-number {{
            background: #4caf50;
            color: white;
        }}
        .step-label {{
            font-size: 11px;
            text-align: center;
            color: #666;
        }}
        .content-section {{
            display: none;
            animation: fadeIn 0.5s ease;
        }}
        .content-section.active {{
            display: block;
        }}
        @keyframes fadeIn {{
            from {{ opacity: 0; }}
            to {{ opacity: 1; }}
        }}
        .form-group {{
            margin-bottom: 20px;
        }}
        .form-group label {{
            display: block;
            margin-bottom: 8px;
            font-weight: 600;
            color: #333;
        }}
        .form-group input {{
            width: 100%;
            padding: 12px;
            border: 2px solid #ddd;
            border-radius: 8px;
            font-size: 16px;
            transition: border-color 0.3s ease;
        }}
        .form-group input:focus {{
            outline: none;
            border-color: #667eea;
        }}
        .employee-info {{
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 20px;
            margin: 20px 0;
        }}
        .info-item {{
            background: #f5f5f5;
            padding: 15px;
            border-radius: 8px;
        }}
        .info-item label {{
            display: block;
            font-size: 12px;
            color: #666;
            margin-bottom: 5px;
        }}
        .info-item .value {{
            font-size: 16px;
            font-weight: 600;
            color: #333;
        }}
        .camera-container {{
            background: #000;
            border-radius: 8px;
            overflow: hidden;
            margin: 20px 0;
        }}
        video {{
            width: 100%;
            height: auto;
            display: block;
        }}
        canvas {{
            display: none;
        }}
        .photo-preview {{
            width: 100%;
            height: auto;
            border-radius: 8px;
            margin-top: 10px;
        }}
        .button-group {{
            display: flex;
            gap: 10px;
            margin-top: 20px;
            flex-wrap: wrap;
        }}
        button {{
            flex: 1;
            min-width: 120px;
            padding: 12px 20px;
            border: none;
            border-radius: 8px;
            font-size: 14px;
            font-weight: 600;
            cursor: pointer;
            transition: all 0.3s ease;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }}
        .btn-primary {{
            background: #667eea;
            color: white;
        }}
        .btn-primary:hover {{
            background: #5568d3;
            transform: translateY(-2px);
            box-shadow: 0 5px 15px rgba(102, 126, 234, 0.4);
        }}
        .btn-secondary {{
            background: #f0f0f0;
            color: #333;
            border: 2px solid #ddd;
        }}
        .btn-secondary:hover {{
            background: #e8e8e8;
        }}
        .btn-success {{
            background: #4caf50;
            color: white;
        }}
        .btn-success:hover {{
            background: #45a049;
        }}
        .btn-danger {{
            background: #f44336;
            color: white;
        }}
        .btn-danger:hover {{
            background: #da190b;
        }}
        .message {{
            padding: 15px;
            border-radius: 8px;
            margin: 20px 0;
            display: none;
        }}
        .message.success {{
            display: block;
            background: #d4edda;
            color: #155724;
            border: 1px solid #c3e6cb;
        }}
        .message.error {{
            display: block;
            background: #f8d7da;
            color: #721c24;
            border: 1px solid #f5c6cb;
        }}
        .loading {{
            text-align: center;
            padding: 20px;
            display: none;
        }}
        .loading.active {{
            display: block;
        }}
        .spinner {{
            border: 4px solid #f3f3f3;
            border-top: 4px solid #667eea;
            border-radius: 50%;
            width: 40px;
            height: 40px;
            animation: spin 1s linear infinite;
            margin: 0 auto;
        }}
        @keyframes spin {{
            0% {{ transform: rotate(0deg); }}
            100% {{ transform: rotate(360deg); }}
        }}
        .confirmation {{
            background: #fff3cd;
            border: 1px solid #ffc107;
            border-radius: 8px;
            padding: 20px;
            margin: 20px 0;
            text-align: center;
        }}
        .confirmation h3 {{
            color: #ff6f00;
            margin-bottom: 10px;
        }}
        .error-message {{
            color: #f44336;
            font-size: 14px;
            margin-top: 5px;
        }}
    </style>
</head>
<body>
    <div class="cache-indicator">
        🟢 FRESH WORKING VERSION | Cache ID: {cache_id} | Server Time: {current_time}
    </div>

    <div class="kiosk-container">
        <div class="kiosk-header">
            <h1>🏢 Attendance Kiosk</h1>
            <p>Employee Check-In / Check-Out System</p>
        </div>

        <div class="step-indicator">
            <div class="step active" data-step="1">
                <div class="step-number">1</div>
                <div class="step-label">Enter Code</div>
            </div>
            <div class="step" data-step="2">
                <div class="step-number">2</div>
                <div class="step-label">Search</div>
            </div>
            <div class="step" data-step="3">
                <div class="step-number">3</div>
                <div class="step-label">View Info</div>
            </div>
            <div class="step" data-step="4">
                <div class="step-number">4</div>
                <div class="step-label">Camera</div>
            </div>
            <div class="step" data-step="5">
                <div class="step-number">5</div>
                <div class="step-label">Capture</div>
            </div>
            <div class="step" data-step="6">
                <div class="step-number">6</div>
                <div class="step-label">Confirm</div>
            </div>
        </div>

        <div class="content-section active" data-content="1">
            <div class="form-group">
                <label>📱 Enter Employee Code</label>
                <input type="text" id="employeeCode" placeholder="e.g., E-2606026" autofocus>
                <div class="error-message" id="codeError"></div>
            </div>
            <button type="button" class="btn-primary" id="nextBtn">Next →</button>
        </div>

        <div class="content-section" data-content="2">
            <div class="form-group">
                <label>🔍 Employee Found</label>
                <div class="loading" id="searchLoading">
                    <div class="spinner"></div>
                    <p>Searching...</p>
                </div>
                <div id="employeePreview" class="employee-info"></div>
                <div class="error-message" id="searchError"></div>
            </div>
            <div class="button-group">
                <button type="button" class="btn-secondary" id="backBtn">← Back</button>
                <button type="button" class="btn-primary" id="confirmBtn">Next →</button>
            </div>
        </div>

        <div class="content-section" data-content="3">
            <div class="form-group">
                <label>👤 Employee Information</label>
                <div id="employeeDetails" class="employee-info"></div>
            </div>
            <div class="button-group">
                <button type="button" class="btn-secondary" id="back2Btn">← Back</button>
                <button type="button" class="btn-primary" id="cameraBtn">Next →</button>
            </div>
        </div>

        <div class="content-section" data-content="4">
            <div class="form-group">
                <label>📷 Camera</label>
                <div class="camera-container">
                    <video id="cameraFeed" autoplay playsinline></video>
                </div>
            </div>
            <div class="button-group">
                <button type="button" class="btn-secondary" id="back3Btn">← Back</button>
                <button type="button" class="btn-primary" id="captureBtn">Capture Photo →</button>
            </div>
        </div>

        <div class="content-section" data-content="5">
            <div class="form-group">
                <label>📸 Photo Preview</label>
                <canvas id="photoCanvas" style="display:none;"></canvas>
                <img id="photoPreview" class="photo-preview" style="display:none;">
            </div>
            <div class="button-group">
                <button type="button" class="btn-secondary" id="retakeBtn">Retake ↻</button>
                <button type="button" class="btn-primary" id="usePhotoBtn">Use This Photo →</button>
            </div>
        </div>

        <div class="content-section" data-content="6">
            <div class="confirmation">
                <h3>Ready to Confirm Attendance</h3>
                <p id="attendanceConfirmation"></p>
            </div>
            <div class="message" id="attendanceMessage"></div>
            <div class="loading" id="attendanceLoading">
                <div class="spinner"></div>
                <p>Processing...</p>
            </div>
            <div class="button-group">
                <button type="button" class="btn-secondary" id="newEmployeeBtn">New Employee</button>
                <button type="button" class="btn-success" id="checkinBtn">✅ Check-In</button>
                <button type="button" class="btn-danger" id="checkoutBtn">🚪 Check-Out</button>
            </div>
        </div>
    </div>

    <script>
        console.log('🟢 Script loaded | Cache ID: {cache_id} | Time: {current_time}');
        let currentStep = 1;
        let selectedEmployee = null;
        let capturedPhoto = null;
        let currentGPS = null;
        const API_BASE = window.location.origin;

        function goToStep(step) {{
            console.log('Going to step:', step);
            currentStep = step;
            document.querySelectorAll('.content-section').forEach(s => s.classList.remove('active'));
            document.querySelector('.content-section[data-content="' + step + '"]').classList.add('active');
            document.querySelectorAll('.step').forEach(s => {{
                const num = parseInt(s.dataset.step);
                s.classList.remove('active', 'completed');
                if (num === step) s.classList.add('active');
                else if (num < step) s.classList.add('completed');
            }});
            if (step === 4) startCamera();
            else if (step === 5) capturePhoto();
            else if (step === 6) getGPS();
        }}

        document.getElementById('nextBtn').addEventListener('click', async function() {{
            console.log('✅ Next button clicked!');
            const code = document.getElementById('employeeCode').value.trim().toUpperCase();
            if (!code) {{
                document.getElementById('codeError').textContent = '❌ Please enter employee code';
                return;
            }}
            console.log('Searching for:', code);
            document.getElementById('codeError').textContent = '';
            document.getElementById('searchLoading').classList.add('active');
            document.getElementById('searchError').textContent = '';
            
            try {{
                const res = await fetch(API_BASE + '/coordinator/search', {{
                    method: 'POST',
                    headers: {{ 'Content-Type': 'application/json' }},
                    body: JSON.stringify({{ search_term: code }})
                }});
                const data = await res.json();
                console.log('Search result:', data);
                document.getElementById('searchLoading').classList.remove('active');
                
                if (!data.success || !data.employee) {{
                    document.getElementById('searchError').textContent = data.error || 'Employee not found';
                    return;
                }}
                
                selectedEmployee = data.employee;
                const html = '<div class="info-item"><label>Code</label><div class="value">' + data.employee.employee_code + '</div></div>' +
                    '<div class="info-item"><label>Name</label><div class="value">' + data.employee.full_name + '</div></div>' +
                    '<div class="info-item"><label>Department</label><div class="value">' + data.employee.department + '</div></div>' +
                    '<div class="info-item"><label>Designation</label><div class="value">' + data.employee.designation + '</div></div>';
                document.getElementById('employeePreview').innerHTML = html;
                document.getElementById('employeeDetails').innerHTML = html;
                goToStep(2);
            }} catch (err) {{
                console.error('Search error:', err);
                document.getElementById('searchLoading').classList.remove('active');
                document.getElementById('searchError').textContent = 'Search failed: ' + err.message;
            }}
        }});

        document.getElementById('backBtn').addEventListener('click', function() {{ goToStep(1); }});
        document.getElementById('confirmBtn').addEventListener('click', function() {{ goToStep(3); }});
        document.getElementById('back2Btn').addEventListener('click', function() {{ goToStep(2); }});
        document.getElementById('cameraBtn').addEventListener('click', function() {{ goToStep(4); }});
        document.getElementById('back3Btn').addEventListener('click', function() {{ goToStep(3); }});
        
        async function startCamera() {{
            try {{
                const stream = await navigator.mediaDevices.getUserMedia({{ video: {{ facingMode: 'user' }} }});
                document.getElementById('cameraFeed').srcObject = stream;
            }} catch (e) {{
                alert('Camera error: ' + e.message);
                goToStep(3);
            }}
        }}

        document.getElementById('captureBtn').addEventListener('click', function() {{ goToStep(5); }});
        
        function capturePhoto() {{
            const video = document.getElementById('cameraFeed');
            const canvas = document.getElementById('photoCanvas');
            const ctx = canvas.getContext('2d');
            canvas.width = video.videoWidth || 320;
            canvas.height = video.videoHeight || 240;
            ctx.drawImage(video, 0, 0);
            capturedPhoto = canvas.toDataURL('image/jpeg');
            document.getElementById('photoPreview').src = capturedPhoto;
            document.getElementById('photoPreview').style.display = 'block';
            const stream = video.srcObject;
            if (stream) stream.getTracks().forEach(function(t) {{ t.stop(); }});
        }}

        document.getElementById('retakeBtn').addEventListener('click', function() {{ capturedPhoto = null; goToStep(4); }});
        document.getElementById('usePhotoBtn').addEventListener('click', function() {{ goToStep(6); }});

        function getGPS() {{
            if (navigator.geolocation) {{
                navigator.geolocation.getCurrentPosition(
                    function(pos) {{
                        currentGPS = {{ latitude: pos.coords.latitude, longitude: pos.coords.longitude, accuracy: pos.coords.accuracy }};
                        document.getElementById('attendanceConfirmation').textContent = 'GPS Acquired ✓\\n' + selectedEmployee.full_name;
                    }},
                    function() {{
                        currentGPS = {{ latitude: 18.520430, longitude: 73.856743, accuracy: 100 }};
                        document.getElementById('attendanceConfirmation').textContent = 'Using default location\\n' + selectedEmployee.full_name;
                    }}
                );
            }} else {{
                currentGPS = {{ latitude: 18.520430, longitude: 73.856743, accuracy: 100 }};
                document.getElementById('attendanceConfirmation').textContent = 'Using default location\\n' + selectedEmployee.full_name;
            }}
        }}

        async function submitAttendance(action) {{
            if (!selectedEmployee || !currentGPS) {{ alert('Missing data'); return; }}
            document.getElementById('attendanceLoading').classList.add('active');
            document.getElementById('attendanceMessage').innerHTML = '';
            
            try {{
                const endpoint = action === 'checkin' ? '/coordinator/check-in' : '/coordinator/check-out';
                const res = await fetch(API_BASE + endpoint, {{
                    method: 'POST',
                    headers: {{ 'Content-Type': 'application/json' }},
                    body: JSON.stringify({{
                        employee_id: selectedEmployee.id,
                        latitude: currentGPS.latitude,
                        longitude: currentGPS.longitude,
                        accuracy: currentGPS.accuracy,
                        photo_base64: capturedPhoto
                    }})
                }});
                const data = await res.json();
                document.getElementById('attendanceLoading').classList.remove('active');
                
                if (data.success) {{
                    document.getElementById('attendanceMessage').textContent = data.message;
                    document.getElementById('attendanceMessage').className = 'message success';
                    setTimeout(function() {{ resetKiosk(); }}, 3000);
                }} else {{
                    document.getElementById('attendanceMessage').textContent = '❌ ' + (data.error || data.message);
                    document.getElementById('attendanceMessage').className = 'message error';
                }}
            }} catch (err) {{
                document.getElementById('attendanceLoading').classList.remove('active');
                document.getElementById('attendanceMessage').textContent = '❌ Error: ' + err.message;
                document.getElementById('attendanceMessage').className = 'message error';
            }}
        }}

        document.getElementById('checkinBtn').addEventListener('click', function() {{ submitAttendance('checkin'); }});
        document.getElementById('checkoutBtn').addEventListener('click', function() {{ submitAttendance('checkout'); }});
        document.getElementById('newEmployeeBtn').addEventListener('click', resetKiosk);

        function resetKiosk() {{
            currentStep = 1;
            selectedEmployee = null;
            capturedPhoto = null;
            currentGPS = null;
            document.getElementById('employeeCode').value = '';
            document.getElementById('photoPreview').style.display = 'none';
            document.getElementById('attendanceMessage').innerHTML = '';
            goToStep(1);
            document.getElementById('employeeCode').focus();
        }}

        document.getElementById('employeeCode').addEventListener('keypress', function(e) {{
            if (e.key === 'Enter') document.getElementById('nextBtn').click();
        }});
        
        console.log('✅ All event listeners attached - Cache ID: {cache_id}');
    </script>
</body>
</html>'''
    
    resp = make_response(html)
    resp.headers['Content-Type'] = 'text/html; charset=utf-8'
    resp.headers['Content-Security-Policy'] = "default-src *; script-src * 'unsafe-inline' 'unsafe-eval'; style-src * 'unsafe-inline';"
    resp.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, max-age=0, private'
    resp.headers['Pragma'] = 'no-cache'
    resp.headers['Expires'] = '0'
    return resp
    
    html = '''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Attendance Kiosk</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            display: flex;
            justify-content: center;
            align-items: center;
            padding: 20px;
        }
        .kiosk-container {
            background: white;
            border-radius: 15px;
            box-shadow: 0 10px 40px rgba(0, 0, 0, 0.3);
            max-width: 900px;
            width: 100%;
            padding: 40px;
        }
        .kiosk-header {
            text-align: center;
            margin-bottom: 30px;
        }
        .kiosk-header h1 {
            font-size: 32px;
            color: #333;
            margin-bottom: 10px;
        }
        .kiosk-header p {
            font-size: 14px;
            color: #666;
        }
        .step-indicator {
            display: flex;
            justify-content: space-between;
            margin-bottom: 30px;
            overflow-x: auto;
        }
        .step {
            display: flex;
            flex-direction: column;
            align-items: center;
            min-width: 80px;
        }
        .step-number {
            width: 40px;
            height: 40px;
            border-radius: 50%;
            background: #ddd;
            color: #666;
            display: flex;
            align-items: center;
            justify-content: center;
            font-weight: bold;
            margin-bottom: 8px;
            transition: all 0.3s ease;
        }
        .step.active .step-number {
            background: #667eea;
            color: white;
            transform: scale(1.2);
        }
        .step.completed .step-number {
            background: #4caf50;
            color: white;
        }
        .step-label {
            font-size: 11px;
            text-align: center;
            color: #666;
        }
        .content-section {
            display: none;
            animation: fadeIn 0.5s ease;
        }
        .content-section.active {
            display: block;
        }
        @keyframes fadeIn {
            from { opacity: 0; }
            to { opacity: 1; }
        }
        .form-group {
            margin-bottom: 20px;
        }
        .form-group label {
            display: block;
            margin-bottom: 8px;
            font-weight: 600;
            color: #333;
        }
        .form-group input {
            width: 100%;
            padding: 12px;
            border: 2px solid #ddd;
            border-radius: 8px;
            font-size: 16px;
            transition: border-color 0.3s ease;
        }
        .form-group input:focus {
            outline: none;
            border-color: #667eea;
        }
        .employee-info {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 20px;
            margin: 20px 0;
        }
        .info-item {
            background: #f5f5f5;
            padding: 15px;
            border-radius: 8px;
        }
        .info-item label {
            display: block;
            font-size: 12px;
            color: #666;
            margin-bottom: 5px;
        }
        .info-item .value {
            font-size: 16px;
            font-weight: 600;
            color: #333;
        }
        .camera-container {
            background: #000;
            border-radius: 8px;
            overflow: hidden;
            margin: 20px 0;
        }
        video {
            width: 100%;
            height: auto;
            display: block;
        }
        canvas {
            display: none;
        }
        .photo-preview {
            width: 100%;
            height: auto;
            border-radius: 8px;
            margin-top: 10px;
        }
        .button-group {
            display: flex;
            gap: 10px;
            margin-top: 20px;
            flex-wrap: wrap;
        }
        button {
            flex: 1;
            min-width: 120px;
            padding: 12px 20px;
            border: none;
            border-radius: 8px;
            font-size: 14px;
            font-weight: 600;
            cursor: pointer;
            transition: all 0.3s ease;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }
        .btn-primary {
            background: #667eea;
            color: white;
        }
        .btn-primary:hover {
            background: #5568d3;
            transform: translateY(-2px);
            box-shadow: 0 5px 15px rgba(102, 126, 234, 0.4);
        }
        .btn-secondary {
            background: #f0f0f0;
            color: #333;
            border: 2px solid #ddd;
        }
        .btn-secondary:hover {
            background: #e8e8e8;
        }
        .btn-success {
            background: #4caf50;
            color: white;
        }
        .btn-success:hover {
            background: #45a049;
        }
        .btn-danger {
            background: #f44336;
            color: white;
        }
        .btn-danger:hover {
            background: #da190b;
        }
        .message {
            padding: 15px;
            border-radius: 8px;
            margin: 20px 0;
            display: none;
        }
        .message.success {
            display: block;
            background: #d4edda;
            color: #155724;
            border: 1px solid #c3e6cb;
        }
        .message.error {
            display: block;
            background: #f8d7da;
            color: #721c24;
            border: 1px solid #f5c6cb;
        }
        .loading {
            text-align: center;
            padding: 20px;
            display: none;
        }
        .loading.active {
            display: block;
        }
        .spinner {
            border: 4px solid #f3f3f3;
            border-top: 4px solid #667eea;
            border-radius: 50%;
            width: 40px;
            height: 40px;
            animation: spin 1s linear infinite;
            margin: 0 auto;
        }
        @keyframes spin {
            0% { transform: rotate(0deg); }
            100% { transform: rotate(360deg); }
        }
        .confirmation {
            background: #fff3cd;
            border: 1px solid #ffc107;
            border-radius: 8px;
            padding: 20px;
            margin: 20px 0;
            text-align: center;
        }
        .confirmation h3 {
            color: #ff6f00;
            margin-bottom: 10px;
        }
        .error-message {
            color: #f44336;
            font-size: 14px;
            margin-top: 5px;
        }
    </style>
</head>
<body>
    <div class="kiosk-container">
        <div class="kiosk-header">
            <h1>🏢 Attendance Kiosk</h1>
            <p>Employee Check-In / Check-Out System</p>
            <p style="font-size:12px;color:green;font-weight:bold;">✅ LIVE - Server Time: ''' + current_time + '''</p>
        </div>

        <div class="step-indicator">
            <div class="step active" data-step="1">
                <div class="step-number">1</div>
                <div class="step-label">Enter Code</div>
            </div>
            <div class="step" data-step="2">
                <div class="step-number">2</div>
                <div class="step-label">Search</div>
            </div>
            <div class="step" data-step="3">
                <div class="step-number">3</div>
                <div class="step-label">View Info</div>
            </div>
            <div class="step" data-step="4">
                <div class="step-number">4</div>
                <div class="step-label">Camera</div>
            </div>
            <div class="step" data-step="5">
                <div class="step-number">5</div>
                <div class="step-label">Capture</div>
            </div>
            <div class="step" data-step="6">
                <div class="step-number">6</div>
                <div class="step-label">Confirm</div>
            </div>
        </div>

        <div class="content-section active" data-content="1">
            <div class="form-group">
                <label>📱 Enter Employee Code</label>
                <input type="text" id="employeeCode" placeholder="e.g., E-2606026" autofocus>
                <div class="error-message" id="codeError"></div>
            </div>
            <button type="button" class="btn-primary" id="nextBtn">Next →</button>
        </div>

        <div class="content-section" data-content="2">
            <div class="form-group">
                <label>🔍 Employee Found</label>
                <div class="loading" id="searchLoading">
                    <div class="spinner"></div>
                    <p>Searching...</p>
                </div>
                <div id="employeePreview" class="employee-info"></div>
                <div class="error-message" id="searchError"></div>
            </div>
            <div class="button-group">
                <button type="button" class="btn-secondary" id="backBtn">← Back</button>
                <button type="button" class="btn-primary" id="confirmBtn">Next →</button>
            </div>
        </div>

        <div class="content-section" data-content="3">
            <div class="form-group">
                <label>👤 Employee Information</label>
                <div id="employeeDetails" class="employee-info"></div>
            </div>
            <div class="button-group">
                <button type="button" class="btn-secondary" id="back2Btn">← Back</button>
                <button type="button" class="btn-primary" id="cameraBtn">Next →</button>
            </div>
        </div>

        <div class="content-section" data-content="4">
            <div class="form-group">
                <label>📷 Camera</label>
                <div class="camera-container">
                    <video id="cameraFeed" autoplay playsinline></video>
                </div>
            </div>
            <div class="button-group">
                <button type="button" class="btn-secondary" id="back3Btn">← Back</button>
                <button type="button" class="btn-primary" id="captureBtn">Capture Photo →</button>
            </div>
        </div>

        <div class="content-section" data-content="5">
            <div class="form-group">
                <label>📸 Photo Preview</label>
                <canvas id="photoCanvas" style="display:none;"></canvas>
                <img id="photoPreview" class="photo-preview" style="display:none;">
            </div>
            <div class="button-group">
                <button type="button" class="btn-secondary" id="retakeBtn">Retake ↻</button>
                <button type="button" class="btn-primary" id="usePhotoBtn">Use This Photo →</button>
            </div>
        </div>

        <div class="content-section" data-content="6">
            <div class="confirmation">
                <h3>Ready to Confirm Attendance</h3>
                <p id="attendanceConfirmation"></p>
            </div>
            <div class="message" id="attendanceMessage"></div>
            <div class="loading" id="attendanceLoading">
                <div class="spinner"></div>
                <p>Processing...</p>
            </div>
            <div class="button-group">
                <button type="button" class="btn-secondary" id="newEmployeeBtn">New Employee</button>
                <button type="button" class="btn-success" id="checkinBtn">✅ Check-In</button>
                <button type="button" class="btn-danger" id="checkoutBtn">🚪 Check-Out</button>
            </div>
        </div>
    </div>

    <script>
        console.log('🟢 Script loaded at ''' + current_time + '''');
        let currentStep = 1;
        let selectedEmployee = null;
        let capturedPhoto = null;
        let currentGPS = null;
        const API_BASE = window.location.origin;

        function goToStep(step) {
            console.log('Going to step:', step);
            currentStep = step;
            document.querySelectorAll('.content-section').forEach(s => s.classList.remove('active'));
            document.querySelector('.content-section[data-content="' + step + '"]').classList.add('active');
            document.querySelectorAll('.step').forEach(s => {
                const num = parseInt(s.dataset.step);
                s.classList.remove('active', 'completed');
                if (num === step) s.classList.add('active');
                else if (num < step) s.classList.add('completed');
            });
            if (step === 4) startCamera();
            else if (step === 5) capturePhoto();
            else if (step === 6) getGPS();
        }

        document.getElementById('nextBtn').addEventListener('click', async function() {
            console.log('Next button clicked');
            const code = document.getElementById('employeeCode').value.trim().toUpperCase();
            if (!code) {
                document.getElementById('codeError').textContent = '❌ Please enter employee code';
                return;
            }
            document.getElementById('codeError').textContent = '';
            document.getElementById('searchLoading').classList.add('active');
            document.getElementById('searchError').textContent = '';
            
            try {
                const res = await fetch(API_BASE + '/coordinator/search', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ search_term: code })
                });
                const data = await res.json();
                console.log('Search result:', data);
                document.getElementById('searchLoading').classList.remove('active');
                
                if (!data.success || !data.employee) {
                    document.getElementById('searchError').textContent = data.error || 'Employee not found';
                    return;
                }
                
                selectedEmployee = data.employee;
                const html = '<div class="info-item"><label>Code</label><div class="value">' + data.employee.employee_code + '</div></div>' +
                    '<div class="info-item"><label>Name</label><div class="value">' + data.employee.full_name + '</div></div>' +
                    '<div class="info-item"><label>Department</label><div class="value">' + data.employee.department + '</div></div>' +
                    '<div class="info-item"><label>Designation</label><div class="value">' + data.employee.designation + '</div></div>';
                document.getElementById('employeePreview').innerHTML = html;
                document.getElementById('employeeDetails').innerHTML = html;
                goToStep(2);
            } catch (err) {
                console.error('Search error:', err);
                document.getElementById('searchLoading').classList.remove('active');
                document.getElementById('searchError').textContent = 'Search failed: ' + err.message;
            }
        });

        document.getElementById('backBtn').addEventListener('click', function() { goToStep(1); });
        document.getElementById('confirmBtn').addEventListener('click', function() { goToStep(3); });
        document.getElementById('back2Btn').addEventListener('click', function() { goToStep(2); });
        document.getElementById('cameraBtn').addEventListener('click', function() { goToStep(4); });
        document.getElementById('back3Btn').addEventListener('click', function() { goToStep(3); });
        
        async function startCamera() {
            try {
                const stream = await navigator.mediaDevices.getUserMedia({ video: { facingMode: 'user' } });
                document.getElementById('cameraFeed').srcObject = stream;
            } catch (e) {
                alert('Camera error: ' + e.message);
                goToStep(3);
            }
        }

        document.getElementById('captureBtn').addEventListener('click', function() { goToStep(5); });
        
        function capturePhoto() {
            const video = document.getElementById('cameraFeed');
            const canvas = document.getElementById('photoCanvas');
            const ctx = canvas.getContext('2d');
            canvas.width = video.videoWidth || 320;
            canvas.height = video.videoHeight || 240;
            ctx.drawImage(video, 0, 0);
            capturedPhoto = canvas.toDataURL('image/jpeg');
            document.getElementById('photoPreview').src = capturedPhoto;
            document.getElementById('photoPreview').style.display = 'block';
            const stream = video.srcObject;
            if (stream) stream.getTracks().forEach(function(t) { t.stop(); });
        }

        document.getElementById('retakeBtn').addEventListener('click', function() { capturedPhoto = null; goToStep(4); });
        document.getElementById('usePhotoBtn').addEventListener('click', function() { goToStep(6); });

        function getGPS() {
            if (navigator.geolocation) {
                navigator.geolocation.getCurrentPosition(
                    function(pos) {
                        currentGPS = { latitude: pos.coords.latitude, longitude: pos.coords.longitude, accuracy: pos.coords.accuracy };
                        document.getElementById('attendanceConfirmation').textContent = 'GPS Acquired ✓\\n' + selectedEmployee.full_name;
                    },
                    function() {
                        currentGPS = { latitude: 18.520430, longitude: 73.856743, accuracy: 100 };
                        document.getElementById('attendanceConfirmation').textContent = 'Using default location\\n' + selectedEmployee.full_name;
                    }
                );
            } else {
                currentGPS = { latitude: 18.520430, longitude: 73.856743, accuracy: 100 };
                document.getElementById('attendanceConfirmation').textContent = 'Using default location\\n' + selectedEmployee.full_name;
            }
        }

        async function submitAttendance(action) {
            if (!selectedEmployee || !currentGPS) { alert('Missing data'); return; }
            document.getElementById('attendanceLoading').classList.add('active');
            document.getElementById('attendanceMessage').innerHTML = '';
            
            try {
                const endpoint = action === 'checkin' ? '/coordinator/check-in' : '/coordinator/check-out';
                const res = await fetch(API_BASE + endpoint, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        employee_id: selectedEmployee.id,
                        latitude: currentGPS.latitude,
                        longitude: currentGPS.longitude,
                        accuracy: currentGPS.accuracy,
                        photo_base64: capturedPhoto
                    })
                });
                const data = await res.json();
                document.getElementById('attendanceLoading').classList.remove('active');
                
                if (data.success) {
                    document.getElementById('attendanceMessage').textContent = data.message;
                    document.getElementById('attendanceMessage').className = 'message success';
                    setTimeout(function() { resetKiosk(); }, 3000);
                } else {
                    document.getElementById('attendanceMessage').textContent = '❌ ' + (data.error || data.message);
                    document.getElementById('attendanceMessage').className = 'message error';
                }
            } catch (err) {
                document.getElementById('attendanceLoading').classList.remove('active');
                document.getElementById('attendanceMessage').textContent = '❌ Error: ' + err.message;
                document.getElementById('attendanceMessage').className = 'message error';
            }
        }

        document.getElementById('checkinBtn').addEventListener('click', function() { submitAttendance('checkin'); });
        document.getElementById('checkoutBtn').addEventListener('click', function() { submitAttendance('checkout'); });
        document.getElementById('newEmployeeBtn').addEventListener('click', resetKiosk);

        function resetKiosk() {
            currentStep = 1;
            selectedEmployee = null;
            capturedPhoto = null;
            currentGPS = null;
            document.getElementById('employeeCode').value = '';
            document.getElementById('photoPreview').style.display = 'none';
            document.getElementById('attendanceMessage').innerHTML = '';
            goToStep(1);
            document.getElementById('employeeCode').focus();
        }

        document.getElementById('employeeCode').addEventListener('keypress', function(e) {
            if (e.key === 'Enter') document.getElementById('nextBtn').click();
        });
        
        console.log('✅ All event listeners attached');
    </script>
</body>
</html>'''
    
    resp = make_response(html)
    resp.headers['Content-Type'] = 'text/html; charset=utf-8'
    resp.headers['Content-Security-Policy'] = "default-src *; script-src * 'unsafe-inline' 'unsafe-eval'; style-src * 'unsafe-inline';"
    resp.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, max-age=0'
    resp.headers['Pragma'] = 'no-cache'
    resp.headers['Expires'] = '0'
    return resp


@coordinator_bp.route("/kiosk", methods=["GET"])
@login_required
def kiosk_new():
    """Same as dashboard - alternative URL"""
    return dashboard()


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
            # Try by name - search in user.full_name via join
            from app.models.user import User
            employee = Employee.query.join(User).filter(
                User.full_name.ilike(f"%{search_term}%")
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
                "full_name": employee.full_name,
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
                "error": f"{employee.full_name} is already checked in",
                "status": "already_checked_in"
            }), 409
        
        # Get office settings for distance calculation (no validation - coordinator can mark from anywhere)
        office = OfficeSettings.query.first()
        if not office:
            return jsonify({"success": False, "error": "Office settings not configured"}), 500
        
        # Calculate distance for record-keeping only (no restriction)
        distance_m = haversine_metres(
            office.latitude, office.longitude,
            float(latitude), float(longitude)
        )
        
        # No GPS accuracy or geofence validation for coordinator
        logger.info(
            "Coordinator check-in | employee=%s | distance=%.0fm (not enforced)",
            employee.employee_code,
            distance_m
        )
        
        # Create or update attendance record
        now = get_naive_ist()  # Use IST time
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
            "message": f"✓ {employee.full_name} checked in successfully",
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
                "error": f"{employee.full_name} has no check-in for today",
                "status": "no_check_in"
            }), 404
        
        if not attendance.check_in_time:
            return jsonify({
                "success": False,
                "error": f"{employee.full_name} has not checked in yet",
                "status": "not_checked_in"
            }), 409
        
        if attendance.check_out_time:
            return jsonify({
                "success": False,
                "error": f"{employee.full_name} has already checked out",
                "status": "already_checked_out"
            }), 409
        
        # Get office settings for distance calculation (no validation - coordinator can mark from anywhere)
        office = OfficeSettings.query.first()
        if not office:
            return jsonify({"success": False, "error": "Office settings not configured"}), 500
        
        # Calculate distance for record-keeping only (no restriction)
        distance_m = haversine_metres(
            office.latitude, office.longitude,
            float(latitude), float(longitude)
        )
        
        # No GPS accuracy or geofence validation for coordinator
        logger.info(
            "Coordinator check-out | employee=%s | distance=%.0fm (not enforced)",
            employee.employee_code,
            distance_m
        )
        
        # Record check-out
        now = get_naive_ist()  # Use IST time
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
            "message": f"✓ {employee.full_name} checked out successfully",
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
