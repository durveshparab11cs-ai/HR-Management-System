'use strict';

(function () {
  // Attendance system - LIVE CAMERA capture
  
  const el = (id) => document.getElementById(id);
  let ciPhotoReady = false;
  let coPhotoReady = false;
  let gpsWatchId = null;
  
  // Setup camera click handlers
  function setupPhotoClick() {
    const ciZone = el('photo-zone');
    const coZone = el('co-photo-zone');
    
    if (ciZone) {
      ciZone.addEventListener('click', () => startCamera('ci'));
    }
    
    if (coZone) {
      coZone.addEventListener('click', () => startCamera('co'));
    }
  }
  
  // Start camera
  async function startCamera(type) {
    const videoContainer = el(type === 'ci' ? 'ci-video-container' : 'co-video-container');
    const video = el(type === 'ci' ? 'ci-video' : 'co-video');
    const photoZone = el(type === 'ci' ? 'photo-zone' : 'co-photo-zone');
    const cameraStatus = el(type === 'ci' ? 'ci-camera-status' : 'co-camera-status');
    const cameraError = el(type === 'ci' ? 'ci-camera-error' : 'co-camera-error');
    const captureBtn = el(type === 'ci' ? 'ci-btn-capture' : 'co-btn-capture');
    
    try {
      // Request camera access
      const stream = await navigator.mediaDevices.getUserMedia({
        video: { facingMode: 'user', width: { ideal: 1280 }, height: { ideal: 720 } },
        audio: false
      });
      
      // Hide photo zone, show video
      if (photoZone) photoZone.style.display = 'none';
      if (videoContainer) videoContainer.style.display = 'block';
      if (video) video.srcObject = stream;
      
      // Show camera status and capture button
      if (cameraStatus) cameraStatus.style.display = 'block';
      if (captureBtn) captureBtn.style.display = 'block';
      if (cameraError) cameraError.style.display = 'none';
      
      // Store stream for later cleanup
      video.dataset.stream = 'active';
      
      // Setup capture button
      captureBtn.onclick = () => capturePhoto(type, video, stream);
      
    } catch (err) {
      console.error('Camera error:', err);
      
      if (cameraError) {
        cameraError.style.display = 'block';
        el(type === 'ci' ? 'ci-error-text' : 'co-error-text').textContent = 
          err.name === 'NotAllowedError' 
            ? 'Camera permission denied - check browser settings' 
            : 'Camera not available: ' + err.message;
      }
      
      if (photoZone) photoZone.style.display = 'block';
      if (videoContainer) videoContainer.style.display = 'none';
    }
  }
  
  // Capture photo from video
  function capturePhoto(type, video, stream) {
    const canvas = el(type === 'ci' ? 'ci-canvas' : 'co-canvas');
    const ctx = canvas.getContext('2d');
    
    // Set canvas size to video size
    canvas.width = video.videoWidth;
    canvas.height = video.videoHeight;
    
    // Flip horizontally (mirror effect) for selfies
    ctx.scale(-1, 1);
    ctx.drawImage(video, -canvas.width, 0);
    
    // Get image data
    const dataUrl = canvas.toDataURL('image/jpeg', 0.95);
    
    // Stop camera stream
    stream.getTracks().forEach(track => track.stop());
    
    // Show preview
    handleCapturedPhoto(type, dataUrl);
  }
  
  // Handle captured photo
  function handleCapturedPhoto(type, dataUrl) {
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
    
    // Show retake button, hide capture
    if (captureBtn) captureBtn.style.display = 'none';
    if (retakeBtn) retakeBtn.style.display = 'block';
    if (cameraStatus) cameraStatus.style.display = 'none';
    
    // Upload the photo
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
    
    // Setup retake buttons - restart camera
    el('ci-btn-retake')?.addEventListener('click', () => {
      const videoContainer = el('ci-video-container');
      const previewContainer = el('ci-selfie-preview');
      const photoZone = el('photo-zone');
      const captureBtn = el('ci-btn-capture');
      const retakeBtn = el('ci-btn-retake');
      
      if (videoContainer) videoContainer.style.display = 'none';
      if (previewContainer) previewContainer.style.display = 'none';
      if (photoZone) photoZone.style.display = 'block';
      if (captureBtn) captureBtn.style.display = 'none';
      if (retakeBtn) retakeBtn.style.display = 'none';
      
      ciPhotoReady = false;
      startCamera('ci');
    });
    
    el('co-btn-retake')?.addEventListener('click', () => {
      const videoContainer = el('co-video-container');
      const previewContainer = el('co-selfie-preview');
      const photoZone = el('co-photo-zone');
      const captureBtn = el('co-btn-capture');
      const retakeBtn = el('co-btn-retake');
      
      if (videoContainer) videoContainer.style.display = 'none';
      if (previewContainer) previewContainer.style.display = 'none';
      if (photoZone) photoZone.style.display = 'block';
      if (captureBtn) captureBtn.style.display = 'none';
      if (retakeBtn) retakeBtn.style.display = 'none';
      
      coPhotoReady = false;
      startCamera('co');
    });
    
    // Setup check-in/out
    el('btn-checkin')?.addEventListener('click', () => {
      if (ciPhotoReady) {
        let csrfToken = '';
        const metaTag = document.querySelector('meta[name="csrf-token"]');
        if (metaTag) csrfToken = metaTag.getAttribute('content');
        if (!csrfToken) {
          const scriptTag = document.querySelector('script#csrf');
          if (scriptTag) csrfToken = scriptTag.textContent;
        }
        if (!csrfToken && window.csrf_token) csrfToken = window.csrf_token;
        
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
        let csrfToken = '';
        const metaTag = document.querySelector('meta[name="csrf-token"]');
        if (metaTag) csrfToken = metaTag.getAttribute('content');
        if (!csrfToken) {
          const scriptTag = document.querySelector('script#csrf');
          if (scriptTag) csrfToken = scriptTag.textContent;
        }
        if (!csrfToken && window.csrf_token) csrfToken = window.csrf_token;
        
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

