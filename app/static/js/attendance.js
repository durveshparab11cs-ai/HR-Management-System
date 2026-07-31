'use strict';

(function () {
  // Attendance system - LIVE CAMERA ONLY (getUserMedia API)
  
  const el = (id) => document.getElementById(id);
  let ciPhotoReady = false;
  let coPhotoReady = false;
  let gpsWatchId = null;
  let ciCamera = null;  // CameraCapture instance for check-in
  let coCamera = null;  // CameraCapture instance for check-out
  
  // Setup photo click handlers
  function setupPhotoClick() {
    const ciZone = el('photo-zone');
    const coZone = el('co-photo-zone');
    
    if (ciZone) {
      ciZone.addEventListener('click', () => {
        takeCamera('ci');
      });
    }
    
    if (coZone) {
      coZone.addEventListener('click', () => {
        takeCamera('co');
      });
    }
  }
  
  // Open live camera using getUserMedia
  async function takeCamera(type) {
    console.log('Opening live camera for:', type);
    
    const photoZone = el(type === 'ci' ? 'photo-zone' : 'co-photo-zone');
    const videoContainer = el(type === 'ci' ? 'ci-video-container' : 'co-video-container');
    const videoEl = el(type === 'ci' ? 'ci-video' : 'co-video');
    const canvasEl = el(type === 'ci' ? 'ci-canvas' : 'co-canvas');
    const captureBtn = el(type === 'ci' ? 'ci-btn-capture' : 'co-btn-capture');
    const cameraStatus = el(type === 'ci' ? 'ci-camera-status' : 'co-camera-status');
    const cameraError = el(type === 'ci' ? 'ci-camera-error' : 'co-camera-error');
    const cameraDisabled = el(type === 'ci' ? 'ci-camera-disabled' : 'co-camera-disabled');
    
    try {
      // Hide photo zone
      if (photoZone) photoZone.style.display = 'none';
      
      // Initialize camera if not already done
      if (type === 'ci' && !ciCamera) {
        ciCamera = new CameraCapture('ci-video', 'ci-canvas');
      } else if (type === 'co' && !coCamera) {
        coCamera = new CameraCapture('co-video', 'co-canvas');
      }
      
      const camera = type === 'ci' ? ciCamera : coCamera;
      
      // Start camera
      await camera.start();
      
      // Show video container and capture button
      if (videoContainer) videoContainer.style.display = 'block';
      if (captureBtn) captureBtn.style.display = 'block';
      if (cameraStatus) cameraStatus.style.display = 'block';
      if (cameraError) cameraError.style.display = 'none';
      if (cameraDisabled) cameraDisabled.style.display = 'none';
      
      // Attach capture button event
      if (captureBtn) {
        captureBtn.onclick = async () => {
          await captureFrame(type);
        };
      }
    } catch (err) {
      console.error('Camera error:', err);
      
      // Show appropriate error message
      if (err.name === 'NotAllowedError' || err.name === 'PermissionDeniedError') {
        console.log('Camera permission denied');
        if (cameraDisabled) cameraDisabled.style.display = 'block';
      } else if (err.name === 'NotFoundError' || err.name === 'DevicesNotFoundError') {
        console.log('No camera device found');
        if (cameraError) {
          el(type === 'ci' ? 'ci-error-text' : 'co-error-text').textContent = 'No camera device found';
          cameraError.style.display = 'block';
        }
      } else {
        console.log('General camera error:', err.message);
        if (cameraError) {
          el(type === 'ci' ? 'ci-error-text' : 'co-error-text').textContent = err.message || 'Camera error';
          cameraError.style.display = 'block';
        }
      }
      
      // Show photo zone again for retry
      if (photoZone) photoZone.style.display = 'block';
    }
  }
  
  // Capture frame from live camera
  async function captureFrame(type) {
    console.log('Capturing frame for:', type);
    
    const camera = type === 'ci' ? ciCamera : coCamera;
    const videoContainer = el(type === 'ci' ? 'ci-video-container' : 'co-video-container');
    const captureBtn = el(type === 'ci' ? 'ci-btn-capture' : 'co-btn-capture');
    
    try {
      // Capture and compress
      const base64 = await camera.capture();
      
      // Stop camera
      await camera.stop();
      if (type === 'ci') ciCamera = null;
      else coCamera = null;
      
      // Hide video container
      if (videoContainer) videoContainer.style.display = 'none';
      if (captureBtn) captureBtn.style.display = 'none';
      
      // Display photo
      displayPhoto(type, base64);
    } catch (err) {
      console.error('Capture error:', err);
      alert('Error capturing photo: ' + err.message);
    }
  }
  
  // Display captured photo
  function displayPhoto(type, dataUrl) {
    const photoZone = el(type === 'ci' ? 'photo-zone' : 'co-photo-zone');
    const previewImg = el(type === 'ci' ? 'ci-selfie-img' : 'co-selfie-img');
    const previewContainer = el(type === 'ci' ? 'ci-selfie-preview' : 'co-selfie-preview');
    const retakeBtn = el(type === 'ci' ? 'ci-btn-retake' : 'co-btn-retake');
    
    if (photoZone) photoZone.style.display = 'none';
    if (previewImg) previewImg.src = dataUrl;
    if (previewContainer) previewContainer.style.display = 'block';
    if (retakeBtn) retakeBtn.style.display = 'block';
    
    // Upload immediately
    uploadSelfie(type, dataUrl);
  }
  
  // Upload selfie
  async function uploadSelfie(type, dataUrl) {
    try {
      // Get CSRF token - try multiple sources
      let csrfToken = '';
      
      // First try: meta tag (most reliable)
      const metaTag = document.querySelector('meta[name="csrf-token"]');
      if (metaTag && metaTag.hasAttribute('content')) {
        csrfToken = metaTag.getAttribute('content').trim();
      }
      
      // Second try: window variable
      if (!csrfToken && window.csrf_token) {
        csrfToken = String(window.csrf_token).trim();
      }
      
      // Validate CSRF token (should not contain < or >)
      if (csrfToken && (csrfToken.includes('<') || csrfToken.includes('>'))) {
        console.warn('Invalid CSRF token detected, clearing');
        csrfToken = '';
      }
      
      console.log('Using CSRF token:', csrfToken ? '(present)' : '(missing)');
      console.log('Uploading selfie for type:', type);
      
      const res = await fetch('/attendance/capture-selfie', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-CSRFToken': csrfToken || ''
        },
        body: JSON.stringify({
          selfie: dataUrl,
          type: type === 'ci' ? 'checkin' : 'checkout'
        })
      });
      
      const data = await res.json();
      console.log('Upload response:', data);
      
      if (data.success) {
        if (type === 'ci') ciPhotoReady = true;
        else coPhotoReady = true;
        
        console.log('Photo ready, generating proof image');
        
        // Generate proof image
        generateProof(type);
        enableCheckin();
        alert('✓ Photo captured successfully! Ready for check-in.');
      } else {
        alert('❌ Upload failed: ' + (data.error || 'Unknown error'));
      }
    } catch (err) {
      console.error('Upload error:', err);
      alert('❌ Upload failed: ' + err.message);
    }
  }
  
  // Update clock display
  function updateClock() {
    const now = new Date();
    
    // Format time
    const hours = String(now.getHours()).padStart(2, '0');
    const minutes = String(now.getMinutes()).padStart(2, '0');
    const seconds = String(now.getSeconds()).padStart(2, '0');
    const clockDisplay = `${hours}:${minutes}:${seconds}`;
    
    // Format date
    const options = { weekday: 'short', month: 'short', day: 'numeric', year: 'numeric' };
    const dateDisplay = now.toLocaleDateString('en-IN', options);
    
    // Update DOM
    const clockEl = el('att-clock');
    const dateEl = el('att-date');
    
    if (clockEl) clockEl.textContent = clockDisplay;
    if (dateEl) dateEl.textContent = dateDisplay;
  }
  
  // Helper: Get CSRF token safely
  function getCsrfToken() {
    let csrfToken = '';
    
    // Try meta tag first (most reliable)
    const metaTag = document.querySelector('meta[name="csrf-token"]');
    if (metaTag && metaTag.hasAttribute('content')) {
      csrfToken = metaTag.getAttribute('content').trim();
    }
    
    // Try window variable
    if (!csrfToken && window.csrf_token) {
      csrfToken = String(window.csrf_token).trim();
    }
    
    // Validate (no HTML tags)
    if (csrfToken && (csrfToken.includes('<') || csrfToken.includes('>'))) {
      console.warn('Invalid CSRF token detected');
      return '';
    }
    
    return csrfToken;
  }
  
  // Generate proof image
  async function generateProof(type) {
    try {
      const csrfToken = getCsrfToken();
      
      await fetch('/attendance/generate-proof-image', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-CSRFToken': csrfToken || ''
        },
        body: JSON.stringify({
          type: type === 'ci' ? 'checkin' : 'checkout',
          latitude: window.lat || 0,
          longitude: window.lon || 0,
          accuracy: window.acc || 0
        })
      });
    } catch (err) {
      console.error('Proof generation error:', err);
    }
  }
  
  // Enable check-in
  function enableCheckin() {
    const btn = el('btn-checkin');
    if (btn && ciPhotoReady) {
      btn.disabled = false;
    }
  }
  
  // Get GPS (background, doesn't block)
  function getGPS() {
    if (!navigator.geolocation) {
      const gpsText = el('gps-text');
      if (gpsText) gpsText.textContent = 'Geolocation not available';
      return;
    }
    
    const gpsStatus = el('gps-dot');
    const gpsText = el('gps-text');
    
    // First, try to get one immediate position
    navigator.geolocation.getCurrentPosition(
      (pos) => {
        window.lat = pos.coords.latitude;
        window.lon = pos.coords.longitude;
        window.acc = pos.coords.accuracy;
        
        if (gpsStatus) {
          gpsStatus.classList.remove('acquiring');
          gpsStatus.classList.add('ok');
        }
        if (gpsText) gpsText.textContent = 'GPS Ready ✓';
        
        // Update map if available
        if (window.map && window.OFFICE) {
          window.map.setView([window.lat, window.lon], 17);
        }
        
        // Now watch for updates
        gpsWatchId = navigator.geolocation.watchPosition(
          (pos) => {
            window.lat = pos.coords.latitude;
            window.lon = pos.coords.longitude;
            window.acc = pos.coords.accuracy;
            
            if (window.map && window.OFFICE) {
              window.map.setView([window.lat, window.lon], 17);
            }
          },
          () => {
            // Errors on watch are ignored
          },
          {
            enableHighAccuracy: true,
            timeout: 10000,
            maximumAge: 0
          }
        );
      },
      (err) => {
        console.warn('GPS error:', err);
        if (gpsStatus) {
          gpsStatus.classList.remove('acquiring');
          gpsStatus.classList.add('error');
        }
        if (gpsText) gpsText.textContent = 'GPS unavailable - Enable location services';
        
        // Still watch in background
        gpsWatchId = navigator.geolocation.watchPosition(
          (pos) => {
            window.lat = pos.coords.latitude;
            window.lon = pos.coords.longitude;
            window.acc = pos.coords.accuracy;
            
            if (gpsStatus) {
              gpsStatus.classList.remove('error');
              gpsStatus.classList.add('ok');
            }
            if (gpsText) gpsText.textContent = 'GPS Ready ✓';
            
            if (window.map && window.OFFICE) {
              window.map.setView([window.lat, window.lon], 17);
            }
          },
          () => {
            // Ignore watch errors
          },
          {
            enableHighAccuracy: true,
            timeout: 10000,
            maximumAge: 0
          }
        );
      },
      {
        enableHighAccuracy: true,
        timeout: 10000,
        maximumAge: 0
      }
    );
  }
  
  // Init map
  function initMap() {
    const container = el('att-map');
    if (!container || typeof L === 'undefined') {
      console.warn('Map container not ready or Leaflet not loaded');
      return;
    }
    
    // Ensure the map container is properly visible
    container.style.display = 'block';
    container.style.zIndex = '1';
    
    window.map = L.map('att-map');
    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
      maxZoom: 19,
      attribution: '© OpenStreetMap'
    }).addTo(window.map);
    
    const officeData = document.getElementById('office-data');
    if (officeData) {
      const data = JSON.parse(officeData.textContent);
      window.OFFICE = data;
      
      if (data.lat && data.lon) {
        // Draw office marker
        L.marker([data.lat, data.lon], {
          icon: L.divIcon({
            html: '<div style="background:blue;width:14px;height:14px;border-radius:50%;border:2px solid white;box-shadow:0 0 4px blue;"></div>'
          })
        }).addTo(window.map);
        
        // Draw 25m radius circle
        L.circle([data.lat, data.lon], {
          radius: Math.max(data.radius || 100, 25),
          color: 'blue',
          weight: 2,
          fillColor: 'blue',
          fillOpacity: 0.1
        }).addTo(window.map);
        
        // Center map on office
        window.map.setView([data.lat, data.lon], 17);
        
        console.log('Map initialized with office at:', data.lat, data.lon, 'radius:', data.radius);
      }
    }
  }
  
  // Boot
  function boot() {
    console.log('Attendance system starting...');
    
    // Update clock immediately and every second
    updateClock();
    setInterval(updateClock, 1000);
    
    // Setup events
    setupPhotoClick();
    
    // Setup retake buttons
    el('ci-btn-retake')?.addEventListener('click', () => {
      el('ci-selfie-preview').style.display = 'none';
      el('photo-zone').style.display = 'block';
      el('ci-btn-retake').style.display = 'none';
      ciPhotoReady = false;
      takeCamera('ci');
    });
    
    el('co-btn-retake')?.addEventListener('click', () => {
      el('co-selfie-preview').style.display = 'none';
      el('co-photo-zone').style.display = 'block';
      el('co-btn-retake').style.display = 'none';
      coPhotoReady = false;
      takeCamera('co');
    });
    
    // Setup check-in/out
    el('btn-checkin')?.addEventListener('click', () => {
      if (ciPhotoReady) {
        const csrfToken = getCsrfToken();
        
        fetch('/attendance/checkin', {
          method: 'POST',
          headers: {
            'X-CSRFToken': csrfToken || ''
          }
        }).then(() => location.reload());
      }
    });
    
    el('btn-checkout')?.addEventListener('click', () => {
      if (coPhotoReady) {
        const csrfToken = getCsrfToken();
        
        fetch('/attendance/checkout', {
          method: 'POST',
          headers: {
            'X-CSRFToken': csrfToken || ''
          }
        }).then(() => location.reload());
      }
    });
    
    // Init map FIRST before GPS
    initMap();
    
    // Get GPS (non-blocking)
    getGPS();
    
    console.log('Attendance system ready');
  }
  
  // Wait for DOM
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', boot);
  } else {
    boot();
  }
  
})();

