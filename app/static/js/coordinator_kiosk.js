// Coordinator Attendance Kiosk JavaScript
// Moved to external file to avoid CSP inline script blocking

alert('JavaScript file loaded! If you see this, the file is working.');
console.log('🚀 Coordinator Dashboard JavaScript loaded');

// ── CSRF token for Flask-WTF protected endpoints ─────────────
// Read once from the meta tag injected by Jinja2
const CSRF_TOKEN = document.querySelector('meta[name="csrf-token"]')?.content || '';
console.log('🔑 CSRF Token:', CSRF_TOKEN ? 'Present' : 'Missing');

// Wrapper: identical to fetch() but always injects X-CSRFToken header
async function apiFetch(url, options = {}) {
    options.headers = Object.assign({
        'Content-Type': 'application/json',
        'X-CSRFToken': CSRF_TOKEN,
    }, options.headers || {});
    return fetch(url, options);
}

// State Management
let currentStep = 1;
let selectedEmployee = null;
let capturedPhoto = null;

const API_BASE = window.location.origin;
console.log('🌐 API Base:', API_BASE);

// Step Navigation
function goToStep(step) {
    console.log('📍 goToStep called with step:', step);
    
    // Validate Step 1 before going to Step 2
    if (step === 2) {
        const code = document.getElementById('employeeCode').value.trim();
        console.log('🔍 Employee code entered:', code);
        if (!code) {
            document.getElementById('codeError').textContent = '❌ Please enter employee code';
            return;
        }
        document.getElementById('codeError').textContent = '';
    }

    // Update current step and UI
    currentStep = step;
    console.log('✅ Current step updated to:', currentStep);
    updateUI();

    // Perform step-specific actions AFTER UI updates
    setTimeout(() => {
        if (step === 2) {
            console.log('🔎 Triggering searchEmployee() for step 2');
            searchEmployee();
        }
    }, 100);
}

function validateStep(step) {
    return true; // Validation now handled in goToStep
}

// Update confirmation text when moving to step 6
function updateUI() {
    // Update content sections
    document.querySelectorAll('.content-section').forEach(section => {
        section.classList.remove('active');
    });
    document.querySelector(`.content-section[data-content="${currentStep}"]`).classList.add('active');

    // Update step indicators
    document.querySelectorAll('.step').forEach(step => {
        const stepNum = parseInt(step.dataset.step);
        step.classList.remove('active', 'completed');
        
        if (stepNum === currentStep) {
            step.classList.add('active');
        } else if (stepNum < currentStep) {
            step.classList.add('completed');
        }
    });

    // Special handling for each step
    if (currentStep === 4) {
        startCamera();
    } else if (currentStep === 5) {
        capturePhotoFromCamera();
    } else if (currentStep === 6 && selectedEmployee) {
        const empName = selectedEmployee.full_name;
        document.getElementById('attendanceConfirmation').textContent = 
            `Ready to mark attendance for ${empName}. Check-in or Check-out?`;
    }
}

// Step 1-2: Search Employee
async function searchEmployee() {
    console.log('🔎 searchEmployee() called');
    const code = document.getElementById('employeeCode').value.trim().toUpperCase();
    console.log('📝 Search term:', code);
    
    if (!code || code.length < 2) {
        document.getElementById('searchError').textContent = '❌ Enter at least 2 characters';
        return;
    }

    const searchLoading = document.getElementById('searchLoading');
    const searchResults = document.getElementById('searchResults');
    const searchError = document.getElementById('searchError');

    searchLoading.classList.add('active');
    searchResults.innerHTML = '';
    searchError.textContent = '';
    
    console.log('📡 Sending POST request to /coordinator/search');

    try {
        const response = await apiFetch(`${API_BASE}/coordinator/search`, {
            method: 'POST',
            body: JSON.stringify({ search_term: code })
        });
        
        console.log('📥 Response status:', response.status);

        const data = await response.json();
        console.log('📦 Response data:', data);
        searchLoading.classList.remove('active');

        if (!data.success || !data.employee) {
            searchError.textContent = `❌ ${data.error || 'No employee found'}`;
            return;
        }

        // Display single result as card
        const emp = data.employee;
        console.log('✅ Employee found:', emp.full_name, emp.employee_code);
        const card = document.createElement('div');
        card.className = 'employee-card selected';
        card.innerHTML = `
            <strong>${emp.employee_code}</strong> — ${emp.full_name}<br>
            <small>${emp.department} | ${emp.designation}</small>
        `;
        searchResults.appendChild(card);

        // Auto-select
        selectEmployee(emp);
    } catch (error) {
        console.error('❌ Search error:', error);
        searchLoading.classList.remove('active');
        searchError.textContent = `❌ Search failed: ${error.message}`;
    }
}

function selectEmployee(emp) {
    selectedEmployee = emp;

    // Mark card as selected
    document.querySelectorAll('.employee-card').forEach(card => {
        card.classList.remove('selected');
        card.classList.add('selected');
    });

    document.getElementById('nextFromSearch').style.display = 'block';

    // Display info
    displayEmployeeInfo(emp);
}

function displayEmployeeInfo(emp) {
    const details = document.getElementById('employeeDetails');
    details.innerHTML = `
        <div class="info-item">
            <label>Employee Code</label>
            <div class="value">${emp.employee_code || emp.code}</div>
        </div>
        <div class="info-item">
            <label>Full Name</label>
            <div class="value">${emp.full_name || emp.name}</div>
        </div>
        <div class="info-item">
            <label>Department</label>
            <div class="value">${emp.department || 'N/A'}</div>
        </div>
        <div class="info-item">
            <label>Branch/Location</label>
            <div class="value">${emp.branch || emp.location || 'N/A'}</div>
        </div>
    `;
}

// ── Camera state ──────────────────────────────────────────────
let cameraStream = null;

// Step 4: Start camera — called by updateUI() when step === 4
async function startCamera() {
    const video      = document.getElementById('cameraFeed');
    const container  = document.getElementById('cameraContainer');
    const errBox     = document.getElementById('cameraError');
    const errMsg     = document.getElementById('cameraErrorMsg');
    const captureBtn = document.getElementById('captureBtn');

    // Reset to "trying" state
    container.style.display  = 'block';
    errBox.style.display     = 'none';
    captureBtn.style.display = 'flex';

    // Stop any existing stream
    if (cameraStream) {
        cameraStream.getTracks().forEach(t => t.stop());
        cameraStream = null;
    }

    // Check API availability (requires HTTPS or localhost)
    if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
        showCameraError('Camera API not available. Make sure the page is accessed over HTTPS.');
        return;
    }

    try {
        try {
            cameraStream = await navigator.mediaDevices.getUserMedia({ video: true });
        } catch (firstErr) {
            console.error('getUserMedia attempt 1 failed:', firstErr.name, firstErr.message);
            throw firstErr;
        }
        video.srcObject = cameraStream;
    } catch (err) {
        const messages = {
            'NotFoundError':        'Camera is in use by another app (Teams, Zoom, etc.) or the driver needs a restart. Close other apps and click Retry.',
            'NotAllowedError':      'Camera permission denied. Click the camera icon in the address bar and set it to Allow.',
            'NotReadableError':     'Camera is being used by another application. Close Teams, Zoom or any video app and click Retry.',
            'OverconstrainedError': 'Camera settings not supported. Click Retry.',
            'SecurityError':        'Camera blocked by browser security policy.',
            'AbortError':           'Camera access was interrupted. Click Retry.',
        };
        const friendly = messages[err.name];
        showCameraError(friendly
            ? `${friendly} [${err.name}]`
            : `Camera error — ${err.name}: ${err.message}`);
    }
}

function showCameraError(msg) {
    if (cameraStream) {
        cameraStream.getTracks().forEach(t => t.stop());
        cameraStream = null;
    }
    document.getElementById('cameraContainer').style.display = 'none';
    document.getElementById('cameraError').style.display     = 'block';
    document.getElementById('cameraErrorMsg').textContent    = msg;
    document.getElementById('captureBtn').style.display      = 'none';
}

// Retry camera after failure
function retryCamera() {
    document.getElementById('cameraContainer').style.display = 'block';
    document.getElementById('cameraError').style.display     = 'none';
    document.getElementById('captureBtn').style.display      = 'flex';
    startCamera();
}

// Handle file upload as camera fallback
function handleFileUpload(event) {
    const file = event.target.files[0];
    if (!file) return;

    console.log('📁 File uploaded:', file.name, file.type);

    const reader = new FileReader();
    reader.onload = function(e) {
        capturedPhoto = e.target.result;
        console.log('✅ Photo loaded from file');
        goToStep(5); // Go to preview step
    };
    reader.readAsDataURL(file);
}

function capturePhotoFromCamera() {
    if (!cameraStream) {
        return;
    }

    const video  = document.getElementById('cameraFeed');
    const canvas = document.getElementById('photoCanvas');
    const ctx    = canvas.getContext('2d');

    canvas.width  = video.videoWidth  || 640;
    canvas.height = video.videoHeight || 480;
    ctx.drawImage(video, 0, 0);
    capturedPhoto = canvas.toDataURL('image/jpeg', 0.85);

    const preview = document.getElementById('photoPreview');
    preview.src   = capturedPhoto;
    preview.style.display = 'block';

    cameraStream.getTracks().forEach(t => t.stop());
    cameraStream = null;
}

function recapturePhoto() {
    document.getElementById('photoPreview').style.display = 'none';
    capturedPhoto = null;
    goToStep(4);
}

// Step 6: Submit Attendance
async function submitAttendance(action) {
    if (!selectedEmployee) {
        alert('Please select an employee first');
        return;
    }

    if (!capturedPhoto) {
        console.warn('No photo captured - proceeding without photo');
    }

    const attendanceLoading = document.getElementById('attendanceLoading');
    const attendanceMessage = document.getElementById('attendanceMessage');

    attendanceLoading.classList.add('active');
    attendanceMessage.innerHTML = '';
    attendanceMessage.className = 'message';

    try {
        const endpoint = action === 'checkin' ? '/coordinator/check-in' : '/coordinator/check-out';

        let lat = 0, lng = 0, acc = 0;
        try {
            const geoPos = await new Promise((resolve, reject) => {
                navigator.geolocation.getCurrentPosition(resolve, reject, { timeout: 10000 });
            });
            lat = geoPos.coords.latitude;
            lng = geoPos.coords.longitude;
            acc = geoPos.coords.accuracy;
        } catch (geoErr) {
            console.warn('GPS unavailable:', geoErr.message);
        }

        const response = await apiFetch(`${API_BASE}${endpoint}`, {
            method: 'POST',
            body: JSON.stringify({
                employee_id:  selectedEmployee.id,
                latitude:     lat,
                longitude:    lng,
                accuracy:     acc,
                photo_base64: capturedPhoto
            })
        });

        const data = await response.json();
        attendanceLoading.classList.remove('active');

        if (data.success) {
            attendanceMessage.textContent = `✅ ${data.message}`;
            attendanceMessage.className   = 'message success';
            setTimeout(() => resetKiosk(), 3000);
        } else {
            attendanceMessage.textContent = `❌ ${data.error || data.message}`;
            attendanceMessage.className   = 'message error';
        }
    } catch (error) {
        attendanceLoading.classList.remove('active');
        attendanceMessage.textContent = `❌ Error: ${error.message}`;
        attendanceMessage.className   = 'message error';
    }
}

function resetKiosk() {
    currentStep      = 1;
    selectedEmployee = null;
    capturedPhoto    = null;

    if (cameraStream) {
        cameraStream.getTracks().forEach(t => t.stop());
        cameraStream = null;
    }

    document.getElementById('employeeCode').value           = '';
    document.getElementById('employeeCode').focus();
    document.getElementById('searchResults').innerHTML      = '';
    document.getElementById('nextFromSearch').style.display = 'none';
    document.getElementById('photoPreview').style.display   = 'none';
    document.getElementById('searchError').textContent      = '';
    document.getElementById('codeError').textContent        = '';

    updateUI();
}

// Initialize when DOM is ready
console.log('⏳ Waiting for DOM to be ready...');

document.addEventListener('DOMContentLoaded', function() {
    console.log('📄 DOM loaded, attaching event listeners');
    
    // Test if button exists
    const nextBtn = document.getElementById('nextStep1');
    console.log('🔘 nextStep1 button:', nextBtn ? 'FOUND' : 'NOT FOUND');
    
    if (!nextBtn) {
        console.error('❌ CRITICAL: nextStep1 button not found in DOM!');
        alert('ERROR: Next button not found! Check HTML.');
        return;
    }
    
    // Enter key on employee code input
    document.getElementById('employeeCode').addEventListener('keypress', function(e) {
        if (e.key === 'Enter') goToStep(2);
    });

    // Wire up all button event listeners (CSP compliant - no inline onclick)
    document.getElementById('nextStep1').addEventListener('click', () => {
        console.log('🖱️ Next button clicked!');
        goToStep(2);
    });
    document.getElementById('backStep2').addEventListener('click', () => goToStep(1));
    document.getElementById('nextFromSearch').addEventListener('click', () => goToStep(3));
    document.getElementById('backStep3').addEventListener('click', () => goToStep(2));
    document.getElementById('nextStep3').addEventListener('click', () => goToStep(4));
    document.getElementById('backStep4').addEventListener('click', () => goToStep(3));
    document.getElementById('captureBtn').addEventListener('click', () => goToStep(5));
    document.getElementById('recaptureBtn').addEventListener('click', recapturePhoto);
    document.getElementById('usePhotoBtn').addEventListener('click', () => goToStep(6));
    document.getElementById('newEmployeeBtn').addEventListener('click', resetKiosk);
    document.getElementById('checkInBtn').addEventListener('click', () => submitAttendance('checkin'));
    document.getElementById('checkOutBtn').addEventListener('click', () => submitAttendance('checkout'));
    document.getElementById('startOverLink').addEventListener('click', (e) => {
        e.preventDefault();
        resetKiosk();
    });
    document.getElementById('retryCameraBtn').addEventListener('click', retryCamera);
    document.getElementById('fileUpload').addEventListener('change', handleFileUpload);

    console.log('✅ All event listeners attached');

    updateUI();
});

// Also try immediate execution in case DOM is already loaded
if (document.readyState === 'loading') {
    console.log('📄 Document still loading, waiting for DOMContentLoaded...');
} else {
    console.log('📄 Document already loaded, executing initialization immediately');
    // DOM already loaded, execute immediately
    setTimeout(() => {
        const nextBtn = document.getElementById('nextStep1');
        if (nextBtn && !nextBtn.onclick) {
            console.log('🔧 Attaching listeners immediately (DOM was already ready)');
            nextBtn.addEventListener('click', () => {
                console.log('🖱️ Next button clicked (immediate listener)!');
                goToStep(2);
            });
        }
    }, 100);
}
