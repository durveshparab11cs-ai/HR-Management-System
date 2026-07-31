'use strict';

(function () {
  // Attendance system - Simple camera capture (works on Render)
  
  const el = (id) => document.getElementById(id);
  let ciPhotoReady = false;
  let coPhotoReady = false;
  let gpsWatchId = null;
  
  // Setup photo click handlers
  function setupPhotoClick() {
    const ciZone = el('photo-zone');
    const coZone = el('co-photo-zone');
    
    if (ciZone) {
      ciZone.addEventListener('click', () => {
        openCameraCapture('ci');
      });
    }
    
    if (coZone) {
      coZone.addEventListener('click', () => {
        openCameraCapture('co');
      });
    }
  }
  
  // Open native camera via HTML5 input
  function openCameraCapture(type) {
    console.log('Opening camera for:', type);
    
    // Create file input
    const input = document.createElement('input');
    input.type = 'file';
    input.accept = 'image/*';
    input.capture = 'user'; // Forces camera on mobile
    
    input.onchange = (e) => {
      const file = e.target.files[0];
      if (file) {
        handleCapture(type, file);
      }
    };
    
    // Trigger camera
    input.click();
  }
  
  // Handle captured photo
  function handleCapture(type, file) {
    console.log('Photo captured:', file.name);
    
    const reader = new FileReader();
    
    reader.onload = (e) => {
      const dataUrl = e.target.result;
      showPhoto(type, dataUrl);
    };
    
    reader.readAsDataURL(file);
  }
  
  // Show captured photo
  function showPhoto(type, dataUrl) {
    const previewImg = el(type === 'ci' ? 'ci-selfie-img' : 'co-selfie-img');
    const previewContainer = el(type === 'ci' ? 'ci-selfie-preview' : 'co-selfie-preview');
    const photoZone = el(type === 'ci' ? 'photo-zone' : 'co-photo-zone');
    const retakeBtn = el(type === 'ci' ? 'ci-btn-retake' : 'co-btn-retake');
    
    if (previewImg) previewImg.src = dataUrl;
    if (previewContainer) previewContainer.style.display = 'block';
    if (photoZone) photoZone.style.display = 'none';
    if (retakeBtn) retakeBtn.style.display = 'block';
    
    // Upload photo
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
      openCameraCapture('ci');
    });
    
    el('co-btn-retake')?.addEventListener('click', () => {
      el('co-selfie-preview').style.display = 'none';
      el('co-photo-zone').style.display = 'block';
      el('co-btn-retake').style.display = 'none';
      coPhotoReady = false;
      openCameraCapture('co');
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

