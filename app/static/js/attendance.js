'use strict';

(function () {
  // Attendance system - Direct camera capture via getUserMedia
  
  const el = (id) => document.getElementById(id);
  let ciPhotoReady = false;
  let coPhotoReady = false;
  let gpsWatchId = null;
  let currentStream = null;
  
  // Setup photo click handlers
  function setupPhotoClick() {
    const ciZone = el('photo-zone');
    const coZone = el('co-photo-zone');
    
    if (ciZone) {
      ciZone.addEventListener('click', () => startLiveCamera('ci'));
    }
    
    if (coZone) {
      coZone.addEventListener('click', () => startLiveCamera('co'));
    }
  }
  
  // Start live camera using getUserMedia
  async function startLiveCamera(type) {
    const photoZone = el(type === 'ci' ? 'photo-zone' : 'co-photo-zone');
    const videoContainer = el(type === 'ci' ? 'ci-video-container' : 'co-video-container');
    const video = el(type === 'ci' ? 'ci-video' : 'co-video');
    const captureBtn = el(type === 'ci' ? 'ci-btn-capture' : 'co-btn-capture');
    const cameraStatus = el(type === 'ci' ? 'ci-camera-status' : 'co-camera-status');
    
    try {
      console.log('Requesting camera access for type:', type);
      
      // Stop any existing stream
      if (currentStream) {
        currentStream.getTracks().forEach(track => track.stop());
      }
      
      // Request camera - try user-facing camera first
      const constraints = {
        video: {
          facingMode: 'user',
          width: { ideal: 1280 },
          height: { ideal: 720 }
        },
        audio: false
      };
      
      const stream = await navigator.mediaDevices.getUserMedia(constraints);
      currentStream = stream;
      
      console.log('Camera access granted! Stream active.');
      
      // Hide photo zone, show video
      if (photoZone) photoZone.style.display = 'none';
      if (videoContainer) videoContainer.style.display = 'block';
      
      // Attach stream to video element
      video.srcObject = stream;
      video.play();
      
      console.log('Video element setup complete');
      
      // Show status and capture button
      if (cameraStatus) cameraStatus.style.display = 'block';
      if (captureBtn) {
        captureBtn.style.display = 'block';
        captureBtn.onclick = () => captureFrame(type, video, stream);
      }
      
    } catch (err) {
      console.error('Camera error occurred:', err);
      console.error('Error type:', err.name);
      console.error('Error message:', err.message);
      
      // Show error message
      if (photoZone) {
        photoZone.innerHTML = `
          <div style="text-align:center;padding:20px;color:#991b1b">
            <i class="bi bi-exclamation-circle fs-1 d-block mb-2"></i>
            <div class="fw-bold" style="font-size:14px;margin-bottom:8px">Camera Access Required</div>
            <div style="font-size:12px;color:#666;margin-bottom:12px">
              ${err.name === 'NotAllowedError' ? 
                'Permission denied. Please enable camera in your browser settings.' :
                'Camera unavailable: ' + err.message}
            </div>
            <div style="font-size:11px;background:#fef3c7;padding:8px;border-radius:6px;color:#92400e">
              <strong>Fix:</strong> Check address bar for camera icon and enable access
            </div>
          </div>
        `;
        photoZone.style.display = 'block';
      }
    }
  }
  
  // Capture frame from video stream
  function captureFrame(type, video, stream) {
    const canvas = el(type === 'ci' ? 'ci-canvas' : 'co-canvas');
    const ctx = canvas.getContext('2d');
    
    try {
      // Set canvas dimensions
      canvas.width = video.videoWidth;
      canvas.height = video.videoHeight;
      
      console.log(`Capturing frame: ${canvas.width}x${canvas.height}`);
      
      // Flip for selfie (mirror)
      ctx.scale(-1, 1);
      ctx.drawImage(video, -canvas.width, 0);
      
      // Get JPEG data
      const dataUrl = canvas.toDataURL('image/jpeg', 0.95);
      
      console.log('Frame captured, size:', dataUrl.length);
      
      // Stop camera stream
      stream.getTracks().forEach(track => track.stop());
      currentStream = null;
      
      // Show preview and upload
      showPhotoPreview(type, dataUrl);
      
    } catch (err) {
      console.error('Capture error:', err);
      alert('Failed to capture photo: ' + err.message);
    }
  }
  
  // Show photo preview
  function showPhotoPreview(type, dataUrl) {
    const videoContainer = el(type === 'ci' ? 'ci-video-container' : 'co-video-container');
    const previewContainer = el(type === 'ci' ? 'ci-selfie-preview' : 'co-selfie-preview');
    const previewImg = el(type === 'ci' ? 'ci-selfie-img' : 'co-selfie-img');
    const captureBtn = el(type === 'ci' ? 'ci-btn-capture' : 'co-btn-capture');
    const retakeBtn = el(type === 'ci' ? 'ci-btn-retake' : 'co-btn-retake');
    const cameraStatus = el(type === 'ci' ? 'ci-camera-status' : 'co-camera-status');
    
    // Hide video, show preview
    if (videoContainer) videoContainer.style.display = 'none';
    if (previewContainer) previewContainer.style.display = 'block';
    if (previewImg) previewImg.src = dataUrl;
    
    // Update buttons
    if (captureBtn) captureBtn.style.display = 'none';
    if (retakeBtn) retakeBtn.style.display = 'block';
    if (cameraStatus) cameraStatus.style.display = 'none';
    
    // Upload photo
    uploadSelfie(type, dataUrl);
  }
  
  // Upload selfie
  async function uploadSelfie(type, dataUrl) {
    try {
      // Get CSRF token
      let csrfToken = '';
      const metaTag = document.querySelector('meta[name="csrf-token"]');
      if (metaTag) csrfToken = metaTag.getAttribute('content');
      if (!csrfToken) {
        const scriptTag = document.querySelector('script#csrf');
        if (scriptTag) csrfToken = scriptTag.textContent;
      }
      if (!csrfToken && window.csrf_token) {
        csrfToken = window.csrf_token;
      }
      
      console.log('========== UPLOAD SELFIE START ==========');
      console.log('Type:', type);
      console.log('CSRF Token:', csrfToken ? 'Present (' + csrfToken.length + ' chars)' : 'MISSING');
      console.log('Data URL length:', dataUrl.length);
      console.log('Data URL format:', dataUrl.substring(0, 30) + '...');
      
      const payload = {
        selfie: dataUrl,
        type: type === 'ci' ? 'checkin' : 'checkout'
      };
      
      console.log('Payload keys:', Object.keys(payload));
      
      const res = await fetch('/attendance/capture-selfie', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-CSRFToken': csrfToken || ''
        },
        body: JSON.stringify(payload)
      });
      
      console.log('Response status:', res.status);
      console.log('Response headers:', {
        'content-type': res.headers.get('content-type'),
        'content-length': res.headers.get('content-length')
      });
      
      const data = await res.json();
      console.log('Upload response:', data);
      
      if (!res.ok) {
        console.error('Response NOT OK. Status:', res.status);
        alert('❌ Upload failed (HTTP ' + res.status + '): ' + (data.message || 'Unknown error'));
        return;
      }
      
      if (data.success) {
        if (type === 'ci') {
          ciPhotoReady = true;
          console.log('✅ ciPhotoReady set to TRUE');
        } else {
          coPhotoReady = true;
          console.log('✅ coPhotoReady set to TRUE');
        }
        
        console.log('Photo ready. Photo ID:', data.photo_id);
        console.log('Generating proof image...');
        
        // Generate proof image (fire and forget)
        generateProof(type);
        
        // Update button immediately
        console.log('Calling enableCheckin()');
        enableCheckin();
        
        // Update badge
        const badge = el(type === 'ci' ? 'ci-photo-badge' : 'co-photo-badge');
        if (badge) {
          badge.className = 'badge bg-success-subtle text-success small';
          badge.innerHTML = '<i class="bi bi-check-circle me-1"></i>✓ Captured';
          console.log('✅ Badge updated');
        } else {
          console.error('❌ Badge element not found:', type === 'ci' ? 'ci-photo-badge' : 'co-photo-badge');
        }
        
        // Update button text
        const btnText = el(type === 'ci' ? 'ci-text' : 'co-text');
        if (btnText && type === 'ci') {
          btnText.textContent = 'Check In Now';
          console.log('✅ Button text updated to "Check In Now"');
        } else if (btnText && type === 'co') {
          btnText.textContent = 'Check Out Now';
          console.log('✅ Button text updated to "Check Out Now"');
        } else {
          console.error('❌ Button text element not found');
        }
        
        console.log('========== UPLOAD SELFIE SUCCESS ==========');
        alert('✓ Photo captured successfully! Ready for ' + (type === 'ci' ? 'check-in' : 'check-out') + '.');
      } else {
        console.error('Server returned success=false');
        alert('❌ Upload failed: ' + (data.message || data.error || 'Unknown error'));
      }
    } catch (err) {
      console.error('========== UPLOAD SELFIE ERROR ==========');
      console.error('Error type:', err.name);
      console.error('Error message:', err.message);
      console.error('Stack:', err.stack);
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
  
  // Generate proof image
  async function generateProof(type) {
    try {
      let csrfToken = '';
      const metaTag = document.querySelector('meta[name="csrf-token"]');
      if (metaTag) csrfToken = metaTag.getAttribute('content');
      if (!csrfToken) {
        const scriptTag = document.querySelector('script#csrf');
        if (scriptTag) csrfToken = scriptTag.textContent;
      }
      if (!csrfToken && window.csrf_token) csrfToken = window.csrf_token;
      
      const res = await fetch('/attendance/generate-proof-image', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-CSRFToken': csrfToken || ''
        },
        body: JSON.stringify({
          type: type === 'ci' ? 'checkin' : 'checkout',
          latitude: window.lat || 0,
          longitude: window.lon || 0,
          accuracy: window.acc || 0,
          distance_metres: window.distanceMetres || 0
        })
      });
      
      const data = await res.json();
      console.log('Proof generation response:', data);
    } catch (err) {
      console.error('Proof generation error:', err);
    }
  }
  
  // Enable check-in/checkout buttons
  function enableCheckin() {
    const btn = el('btn-checkin');
    const btnCheckout = el('btn-checkout');
    
    console.log('enableCheckin() called - ciPhotoReady:', ciPhotoReady, ', coPhotoReady:', coPhotoReady);
    
    // Enable check-in button if photo is ready and not already checked in
    if (btn && ciPhotoReady) {
      const isAlreadyCheckedIn = btn.textContent.includes('Already Checked In');
      if (!isAlreadyCheckedIn) {
        btn.disabled = false;
        console.log('✅ Check-in button ENABLED');
      }
    }
    
    // Enable check-out button if photo is ready and user is checked in
    if (btnCheckout && coPhotoReady) {
      const isAlreadyCheckedOut = btnCheckout.textContent.includes('Already Checked Out');
      const notCheckedIn = btnCheckout.textContent.includes('Check In First');
      if (!isAlreadyCheckedOut && !notCheckedIn) {
        btnCheckout.disabled = false;
        console.log('✅ Check-out button ENABLED');
      }
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
    
    // Setup retake buttons - restart camera
    el('ci-btn-retake')?.addEventListener('click', () => {
      el('ci-selfie-preview').style.display = 'none';
      el('photo-zone').style.display = 'block';
      el('ci-btn-retake').style.display = 'none';
      ciPhotoReady = false;
      startLiveCamera('ci');
    });
    
    el('co-btn-retake')?.addEventListener('click', () => {
      el('co-selfie-preview').style.display = 'none';
      el('co-photo-zone').style.display = 'block';
      el('co-btn-retake').style.display = 'none';
      coPhotoReady = false;
      startLiveCamera('co');
    });
    
    // Setup check-in/out
    el('btn-checkin')?.addEventListener('click', () => {
      if (!ciPhotoReady) {
        alert('❌ Photo not uploaded yet. Please capture a photo first.');
        return;
      }
      
      let csrfToken = '';
      const metaTag = document.querySelector('meta[name="csrf-token"]');
      if (metaTag) csrfToken = metaTag.getAttribute('content');
      if (!csrfToken) {
        const scriptTag = document.querySelector('script#csrf');
        if (scriptTag) csrfToken = scriptTag.textContent;
      }
      if (!csrfToken && window.csrf_token) csrfToken = window.csrf_token;
      
      console.log('Check-in button clicked. GPS:', window.lat, window.lon, window.acc);
      
      const formData = new FormData();
      formData.append('latitude', window.lat || 0);
      formData.append('longitude', window.lon || 0);
      formData.append('accuracy', window.acc || 0);
      
      const btn = el('btn-checkin');
      const btnText = el('ci-text');
      const spinner = el('ci-spin');
      
      if (btn && btnText && spinner) {
        btn.disabled = true;
        spinner.style.display = 'inline-block';
        btnText.textContent = 'Processing...';
      }
      
      fetch('/attendance/checkin', {
        method: 'POST',
        headers: {
          'X-CSRFToken': csrfToken || ''
        },
        body: formData
      })
      .then(res => res.json())
      .then(data => {
        console.log('Check-in response:', data);
        if (data.success) {
          alert('✅ Check-in successful!\n' + data.message);
          location.reload();
        } else {
          alert('❌ Check-in failed:\n' + data.message);
          if (btn && btnText && spinner) {
            btn.disabled = false;
            spinner.style.display = 'none';
            btnText.textContent = 'Check In Now';
          }
        }
      })
      .catch(err => {
        console.error('Check-in error:', err);
        alert('❌ Check-in failed: ' + err.message);
        if (btn && btnText && spinner) {
          btn.disabled = false;
          spinner.style.display = 'none';
          btnText.textContent = 'Check In Now';
        }
      });
    });
    
    el('btn-checkout')?.addEventListener('click', () => {
      if (!coPhotoReady) {
        alert('❌ Photo not uploaded yet. Please capture a photo first.');
        return;
      }
      
      let csrfToken = '';
      const metaTag = document.querySelector('meta[name="csrf-token"]');
      if (metaTag) csrfToken = metaTag.getAttribute('content');
      if (!csrfToken) {
        const scriptTag = document.querySelector('script#csrf');
        if (scriptTag) csrfToken = scriptTag.textContent;
      }
      if (!csrfToken && window.csrf_token) csrfToken = window.csrf_token;
      
      console.log('Check-out button clicked. GPS:', window.lat, window.lon, window.acc);
      
      const formData = new FormData();
      formData.append('latitude', window.lat || 0);
      formData.append('longitude', window.lon || 0);
      formData.append('accuracy', window.acc || 0);
      
      const btn = el('btn-checkout');
      const btnText = el('co-text');
      const spinner = el('co-spin');
      
      if (btn && btnText && spinner) {
        btn.disabled = true;
        spinner.style.display = 'inline-block';
        btnText.textContent = 'Processing...';
      }
      
      fetch('/attendance/checkout', {
        method: 'POST',
        headers: {
          'X-CSRFToken': csrfToken || ''
        },
        body: formData
      })
      .then(res => res.json())
      .then(data => {
        console.log('Check-out response:', data);
        if (data.success) {
          alert('✅ Check-out successful!\n' + data.message);
          location.reload();
        } else {
          alert('❌ Check-out failed:\n' + data.message);
          if (btn && btnText && spinner) {
            btn.disabled = false;
            spinner.style.display = 'none';
            btnText.textContent = 'Check Out Now';
          }
        }
      })
      .catch(err => {
        console.error('Check-out error:', err);
        alert('❌ Check-out failed: ' + err.message);
        if (btn && btnText && spinner) {
          btn.disabled = false;
          spinner.style.display = 'none';
          btnText.textContent = 'Check Out Now';
        }
      });
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
