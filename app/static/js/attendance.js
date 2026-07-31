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
    const statusText = el(type === 'ci' ? 'ci-status-text' : 'co-status-text');
    
    try {
      // Validate video element exists
      if (!videoEl) {
        throw new Error(`Video element not found: ${type === 'ci' ? 'ci-video' : 'co-video'}`);
      }
      
      console.log('Video element found:', videoEl.id);
      
      // Hide photo zone
      if (photoZone) photoZone.style.display = 'none';
      
      // Show status: requesting camera
      if (cameraStatus) cameraStatus.style.display = 'block';
      if (statusText) statusText.textContent = 'Requesting camera access...';
      if (cameraError) cameraError.style.display = 'none';
      if (cameraDisabled) cameraDisabled.style.display = 'none';
      
      // Initialize camera if not already done
      if (type === 'ci' && !ciCamera) {
        ciCamera = new CameraCapture('ci-video', 'ci-canvas');
      } else if (type === 'co' && !coCamera) {
        coCamera = new CameraCapture('co-video', 'co-canvas');
      }
      
      const camera = type === 'ci' ? ciCamera : coCamera;
      console.log('Camera instance created');
      
      // Start camera with timeout
      console.log('Starting camera stream...');
      await Promise.race([
        camera.start(),
        new Promise((_, reject) => 
          setTimeout(() => reject(new Error('Camera startup timeout')), 8000)
        )
      ]);
      
      console.log('Camera stream started, showing video container');
      
      // Show video container and capture button
      if (videoContainer) {
        videoContainer.style.display = 'block';
        console.log('Video container shown');
      }
      if (captureBtn) {
        captureBtn.style.display = 'block';
        console.log('Capture button shown');
      }
      
      if (statusText) statusText.textContent = 'Camera ready - tap Capture Selfie below';
      
      // Attach capture button event
      if (captureBtn) {
        captureBtn.onclick = async () => {
          await captureFrame(type);
        };
      }
    } catch (err) {
      console.error('Camera error:', err.name, err.message);
      console.error('Full error details:', err);
      
      // Check if this is a permission error on Render (production environment)
      const isPermissionError = err.name === 'NotAllowedError' || 
                                err.name === 'PermissionDeniedError' ||
                                err.message.includes('Permission');
      
      const isDeviceNotFound = err.name === 'NotFoundError' || 
                               err.name === 'DevicesNotFoundError' ||
                               err.message.includes('Requested device not found');
      
      const isTimeoutError = err.message && err.message.includes('timeout');
      
      // On Render (production), if getUserMedia fails, offer file upload fallback
      const isProduction = window.location.hostname !== 'localhost' && 
                          !window.location.hostname.startsWith('127.0.0.1');
      
      if ((isPermissionError || isDeviceNotFound || isTimeoutError) && isProduction) {
        console.log('Production environment - falling back to file upload');
        useFallbackFileUpload(type);
        return;
      }
      
      // Show appropriate error message for development
      if (isPermissionError) {
        console.log('Camera permission denied');
        if (cameraDisabled) cameraDisabled.style.display = 'block';
      } else if (isDeviceNotFound) {
        console.log('No camera device found');
        if (cameraError) {
          el(type === 'ci' ? 'ci-error-text' : 'co-error-text').textContent = 'No camera device found';
          cameraError.style.display = 'block';
        }
      } else if (isTimeoutError) {
        console.log('Camera timeout - device may be busy or unavailable');
        if (cameraError) {
          el(type === 'ci' ? 'ci-error-text' : 'co-error-text').textContent = 'Camera startup timeout - try again';
          cameraError.style.display = 'block';
        }
      } else {
        console.log('General camera error:', err.message);
        if (cameraError) {
          el(type === 'ci' ? 'ci-error-text' : 'co-error-text').textContent = err.message || 'Camera error';
          cameraError.style.display = 'block';
        }
      }
      
      // Hide video container and button if error
      if (videoContainer) videoContainer.style.display = 'none';
      if (captureBtn) captureBtn.style.display = 'none';
      
      // Show photo zone again for retry
      if (photoZone) photoZone.style.display = 'block';
    }
  }
  
  // Fallback: File upload when camera is not available (for Render production)
  function useFallbackFileUpload(type) {
    console.log('Using file upload fallback for:', type);
    
    const photoZone = el(type === 'ci' ? 'photo-zone' : 'co-photo-zone');
    const videoContainer = el(type === 'ci' ? 'ci-video-container' : 'co-video-container');
    const captureBtn = el(type === 'ci' ? 'ci-btn-capture' : 'co-btn-capture');
    const cameraStatus = el(type === 'ci' ? 'ci-camera-status' : 'co-camera-status');
    const cameraError = el(type === 'ci' ? 'ci-camera-error' : 'co-camera-error');
    
    if (videoContainer) videoContainer.style.display = 'none';
    if (captureBtn) captureBtn.style.display = 'none';
    if (cameraStatus) cameraStatus.style.display = 'none';
    if (cameraError) cameraError.style.display = 'none';
    if (photoZone) photoZone.style.display = 'block';
    
    // Create file input
    const input = document.createElement('input');
    input.type = 'file';
    input.accept = 'image/*';
    input.capture = 'environment';  // Try camera capture first
    
    input.addEventListener('change', (e) => {
      const file = e.target.files[0];
      if (file && file.type.startsWith('image/')) {
        console.log('File selected:', file.name, file.type);
        const reader = new FileReader();
        reader.onload = (event) => {
          const dataUrl = event.target.result;
          displayPhoto(type, dataUrl);
        };
        reader.readAsDataURL(file);
      }
    });
    
    // Trigger file picker
    input.click();
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
    const photoZone = el(type === 'ci' ? 'photo-zone' : 'co-photo-zone');
    const photoBadge = el(type === 'ci' ? 'ci-photo-badge' : 'co-photo-badge');
    const photoError = el(type === 'ci' ? 'ci-photo-error' : 'co-photo-error');
    const photoMsg = el(type === 'ci' ? 'ci-error-msg' : 'co-error-msg');
    
    try {
      // Get CSRF token
      let csrfToken = '';
      const metaTag = document.querySelector('meta[name="csrf-token"]');
      if (metaTag && metaTag.hasAttribute('content')) {
        csrfToken = metaTag.getAttribute('content').trim();
      }
      if (!csrfToken && window.csrf_token) {
        csrfToken = String(window.csrf_token).trim();
      }
      if (csrfToken && (csrfToken.includes('<') || csrfToken.includes('>'))) {
        console.warn('Invalid CSRF token detected');
        csrfToken = '';
      }
      
      console.log('Uploading selfie for type:', type);
      console.log('Data URL length:', dataUrl.length, 'bytes');
      console.log('CSRF token present:', !!csrfToken);
      
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
      
      console.log('Response status:', res.status);
      
      if (!res.ok) {
        const text = await res.text();
        console.error('HTTP error:', res.status, text);
        throw new Error(`HTTP ${res.status}: ${text}`);
      }
      
      const data = await res.json();
      console.log('Upload response:', data);
      
      if (data.success) {
        console.log('Photo uploaded successfully, photo_id:', data.photo_id);
        
        // Update state
        if (type === 'ci') {
          ciPhotoReady = true;
        } else {
          coPhotoReady = true;
        }
        
        // Update UI: Show badge as "✓ Captured"
        if (photoBadge) {
          photoBadge.className = 'badge bg-success-subtle text-success small';
          photoBadge.innerHTML = '<i class="bi bi-check-circle me-1"></i>✓ Captured';
        }
        if (photoError) {
          photoError.style.display = 'none';
        }
        
        console.log('Enabling check-in button');
        enableCheckin();
        
        // Generate proof image
        console.log('Generating proof image');
        await generateProof(type);
        
        alert('✓ Photo captured successfully!');
      } else {
        const errorMsg = data.message || data.error || 'Unknown error';
        console.error('Upload failed:', errorMsg);
        
        if (photoError) {
          photoMsg.textContent = errorMsg;
          photoError.style.display = 'block';
        }
        
        alert('❌ Upload failed: ' + errorMsg);
      }
    } catch (err) {
      console.error('Upload error:', err);
      console.error('Stack:', err.stack);
      
      if (photoError) {
        photoMsg.textContent = err.message;
        photoError.style.display = 'block';
      }
      
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
      console.log('Generating proof image for:', type);
      
      // Wait a moment for GPS to be available
      if (!window.lat || !window.lon) {
        console.warn('Waiting for GPS coordinates...');
        await new Promise(resolve => setTimeout(resolve, 500));
      }
      
      // Ensure we have GPS data
      const lat = window.lat || 0;
      const lon = window.lon || 0;
      const acc = window.acc || 100;
      
      if (!lat || !lon) {
        console.warn('GPS coordinates still not available, using defaults');
      }
      
      // Calculate distance from office if available
      let distanceMetres = 0;
      if (window.OFFICE && window.lat && window.lon) {
        distanceMetres = calculateDistance(
          window.OFFICE.lat,
          window.OFFICE.lon,
          window.lat,
          window.lon
        );
        console.log('Distance from office:', distanceMetres, 'meters');
      } else {
        console.warn('Office data not available for distance calculation');
      }
      
      const csrfToken = getCsrfToken();
      
      const payload = {
        type: type === 'ci' ? 'checkin' : 'checkout',
        latitude: lat,
        longitude: lon,
        accuracy: acc,
        distance_metres: distanceMetres
      };
      
      console.log('Proof image payload:', payload);
      
      const res = await fetch('/attendance/generate-proof-image', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-CSRFToken': csrfToken || ''
        },
        body: JSON.stringify(payload)
      });
      
      console.log('Proof generation response status:', res.status);
      
      if (!res.ok) {
        const text = await res.text();
        console.error('Proof generation HTTP error:', res.status, text);
        throw new Error(`HTTP ${res.status}: Proof generation failed`);
      }
      
      const data = await res.json();
      console.log('Proof generation response:', data);
      
      if (!data.success) {
        console.error('Proof generation failed:', data.message);
      }
    } catch (err) {
      console.error('Proof generation error:', err);
      // Don't alert — this is non-critical, photo still exists
    }
  }
  
  // Calculate distance between two GPS points (Haversine formula)
  function calculateDistance(lat1, lon1, lat2, lon2) {
    const R = 6371000; // Earth radius in meters
    const toRad = Math.PI / 180;
    
    const dLat = (lat2 - lat1) * toRad;
    const dLon = (lon2 - lon1) * toRad;
    
    const a = Math.sin(dLat / 2) * Math.sin(dLat / 2) +
              Math.cos(lat1 * toRad) * Math.cos(lat2 * toRad) *
              Math.sin(dLon / 2) * Math.sin(dLon / 2);
    
    const c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a));
    return Math.round(R * c);
  }
  
  // Enable check-in
  function enableCheckin() {
    const btn = el('btn-checkin');
    const btnText = el('ci-text');
    
    if (btn && ciPhotoReady) {
      console.log('Enabling check-in button');
      btn.disabled = false;
      btn.style.opacity = '1';
      btn.style.cursor = 'pointer';
      
      if (btnText) {
        btnText.textContent = 'Check In Now';
      }
      
      // Auto-trigger check-in after a short delay for UX
      console.log('Auto-submitting check-in in 1 second');
      setTimeout(() => {
        console.log('Auto-triggering check-in...');
        if (btn && !btn.dataset.clicked) {
          btn.dataset.clicked = 'true';
          btn.click();
        }
      }, 1000);
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
    el('btn-checkin')?.addEventListener('click', async () => {
      if (ciPhotoReady) {
        console.log('Check-in button clicked');
        const btn = el('btn-checkin');
        const btnText = el('ci-text');
        const btnIcon = el('ci-icon');
        const btnSpin = el('ci-spin');
        
        try {
          // Show loading state
          btn.disabled = true;
          if (btnSpin) btnSpin.style.display = 'block';
          if (btnIcon) btnIcon.style.display = 'none';
          if (btnText) btnText.textContent = 'Submitting...';
          
          const csrfToken = getCsrfToken();
          
          console.log('Sending check-in with GPS:', window.lat, window.lon, window.acc);
          
          const res = await fetch('/attendance/checkin', {
            method: 'POST',
            headers: {
              'Content-Type': 'application/x-www-form-urlencoded',
              'X-CSRFToken': csrfToken || ''
            },
            body: new URLSearchParams({
              latitude: window.lat || 0,
              longitude: window.lon || 0,
              accuracy: window.acc || 0
            })
          });
          
          console.log('Check-in response status:', res.status);
          
          if (!res.ok) {
            const text = await res.text();
            throw new Error(`HTTP ${res.status}: ${text}`);
          }
          
          const data = await res.json();
          console.log('Check-in response:', data);
          
          if (data.success) {
            if (btnText) btnText.textContent = '✓ Checked In';
            alert('✓ Check-in successful! Time: ' + data.time);
            setTimeout(() => location.reload(), 1500);
          } else {
            throw new Error(data.message || 'Check-in failed');
          }
        } catch (err) {
          console.error('Check-in error:', err);
          btn.disabled = false;
          if (btnSpin) btnSpin.style.display = 'none';
          if (btnIcon) btnIcon.style.display = 'block';
          if (btnText) btnText.textContent = 'Check In Now';
          alert('❌ Check-in failed: ' + err.message);
        }
      }
    });
    
    el('btn-checkout')?.addEventListener('click', async () => {
      if (coPhotoReady) {
        console.log('Check-out button clicked');
        const btn = el('btn-checkout');
        const btnText = el('co-text');
        const btnIcon = el('co-icon');
        const btnSpin = el('co-spin');
        
        try {
          // Show loading state
          btn.disabled = true;
          if (btnSpin) btnSpin.style.display = 'block';
          if (btnIcon) btnIcon.style.display = 'none';
          if (btnText) btnText.textContent = 'Submitting...';
          
          const csrfToken = getCsrfToken();
          
          console.log('Sending check-out with GPS:', window.lat, window.lon, window.acc);
          
          const res = await fetch('/attendance/checkout', {
            method: 'POST',
            headers: {
              'Content-Type': 'application/x-www-form-urlencoded',
              'X-CSRFToken': csrfToken || ''
            },
            body: new URLSearchParams({
              latitude: window.lat || 0,
              longitude: window.lon || 0,
              accuracy: window.acc || 0
            })
          });
          
          console.log('Check-out response status:', res.status);
          
          if (!res.ok) {
            const text = await res.text();
            throw new Error(`HTTP ${res.status}: ${text}`);
          }
          
          const data = await res.json();
          console.log('Check-out response:', data);
          
          if (data.success) {
            if (btnText) btnText.textContent = '✓ Checked Out';
            alert('✓ Check-out successful! Worked: ' + data.working);
            setTimeout(() => location.reload(), 1500);
          } else {
            throw new Error(data.message || 'Check-out failed');
          }
        } catch (err) {
          console.error('Check-out error:', err);
          btn.disabled = false;
          if (btnSpin) btnSpin.style.display = 'none';
          if (btnIcon) btnIcon.style.display = 'block';
          if (btnText) btnText.textContent = 'Check Out Now';
          alert('❌ Check-out failed: ' + err.message);
        }
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

