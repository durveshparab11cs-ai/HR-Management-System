// ============================================================================
// COMPLETE ATTENDANCE SYSTEM - TIME + GPS + CAMERA + CHECK-IN/OUT
// ============================================================================
// This script MUST run immediately and work standalone
// No dependencies on other modules or async loading
// ============================================================================

console.log('[ATTENDANCE] Loading attendance.js - COMPLETE VERSION WITH CAMERA');

// ========== GLOBAL STATE INITIALIZATION ==========
// Initialize photo ready flags from backend state
window.ciPhotoReady = typeof HAS_CI_PHOTO !== 'undefined' ? HAS_CI_PHOTO : false;
window.coPhotoReady = typeof HAS_CO_PHOTO !== 'undefined' ? HAS_CO_PHOTO : false;
console.log('[STATE] ciPhotoReady:', window.ciPhotoReady);
console.log('[STATE] coPhotoReady:', window.coPhotoReady);

// ========== GLOBAL CAMERA MANAGER ==========
class CameraManager {
  constructor(elementPrefix) {
    this.prefix = elementPrefix; // 'ci' for check-in, 'co' for check-out
    this.stream = null;
    this.isCapturing = false;
    console.log('[CAM-' + this.prefix.toUpperCase() + '] Initialized');
  }
  
  async start() {
    try {
      console.log('[CAM-' + this.prefix.toUpperCase() + '] Requesting camera access');
      const stream = await navigator.mediaDevices.getUserMedia({
        video: { facingMode: 'user', width: { ideal: 1280 }, height: { ideal: 720 } },
        audio: false
      });
      
      this.stream = stream;
      const video = document.getElementById(this.prefix + '-video');
      if (video) {
        video.srcObject = stream;
        video.onloadedmetadata = () => {
          video.play();
          console.log('[CAM-' + this.prefix.toUpperCase() + '] Video playing');
        };
      }
      
      console.log('[CAM-' + this.prefix.toUpperCase() + '] Camera started successfully');
      return true;
    } catch (e) {
      console.error('[CAM-' + this.prefix.toUpperCase() + '] Start error:', e.message);
      throw e;
    }
  }
  
  async stop() {
    try {
      if (this.stream) {
        this.stream.getTracks().forEach(track => track.stop());
        this.stream = null;
        console.log('[CAM-' + this.prefix.toUpperCase() + '] Camera stopped');
      }
    } catch (e) {
      console.error('[CAM-' + this.prefix.toUpperCase() + '] Stop error:', e.message);
    }
  }
  
  async capture() {
    try {
      const video = document.getElementById(this.prefix + '-video');
      const canvas = document.getElementById(this.prefix + '-canvas');
      
      if (!video || !canvas) {
        throw new Error('Video or canvas element not found');
      }
      
      const ctx = canvas.getContext('2d');
      canvas.width = video.videoWidth;
      canvas.height = video.videoHeight;
      
      ctx.drawImage(video, 0, 0, canvas.width, canvas.height);
      const jpeg = canvas.toDataURL('image/jpeg', 0.95);
      
      console.log('[CAM-' + this.prefix.toUpperCase() + '] Captured:', jpeg.length, 'bytes');
      return jpeg;
    } catch (e) {
      console.error('[CAM-' + this.prefix.toUpperCase() + '] Capture error:', e.message);
      throw e;
    }
  }
}

// Immediate initialization - do this FIRST before anything else
(function() {
  console.log('[ATTENDANCE] Phase 1: DOM initialization starting');
  
  // ========== 1. TIME CLOCK - Update every second ==========
  function updateClock() {
    try {
      const now = new Date();
      const h = String(now.getHours()).padStart(2, '0');
      const m = String(now.getMinutes()).padStart(2, '0');
      const s = String(now.getSeconds()).padStart(2, '0');
      
      const clockEl = document.getElementById('att-clock');
      if (clockEl) {
        clockEl.textContent = h + ':' + m + ':' + s;
        // console.log('[CLOCK] Updated:', h + ':' + m + ':' + s);
      }
    } catch (e) {
      console.error('[CLOCK] Error:', e.message);
    }
  }
  
  function updateDate() {
    try {
      const now = new Date();
      const day = now.toLocaleDateString('en-US', { weekday: 'long' });
      const date = now.toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' });
      
      const dateEl = document.getElementById('att-date');
      if (dateEl) {
        dateEl.textContent = day + ', ' + date;
        console.log('[DATE] Updated:', day + ', ' + date);
      }
    } catch (e) {
      console.error('[DATE] Error:', e.message);
    }
  }
  
  // Start clock immediately
  console.log('[CLOCK] Starting immediate update');
  updateClock();
  updateDate();
  setInterval(updateClock, 1000);
  console.log('[CLOCK] Clock interval set - updates every 1 second');
  
  // ========== 2. GPS - Start watching immediately ==========
  function startGPS() {
    console.log('[GPS] Starting GPS watch');
    
    if (!navigator.geolocation) {
      console.error('[GPS] Geolocation not available');
      const gpsText = document.getElementById('gps-text');
      if (gpsText) gpsText.innerHTML = '❌ Geolocation not available';
      return;
    }
    
    window.lastGPS = { lat: null, lon: null, acc: null };
    
    navigator.geolocation.watchPosition(
      position => {
        const lat = position.coords.latitude;
        const lon = position.coords.longitude;
        const acc = position.coords.accuracy;
        
        window.lastGPS = { lat, lon, acc };
        window.lat = lat;
        window.lon = lon;
        window.acc = acc;
        
        console.log('[GPS] Position locked:', lat.toFixed(4), lon.toFixed(4), 'accuracy:', acc.toFixed(0) + 'm');
        
        // Update UI
        const gpsText = document.getElementById('gps-text');
        if (gpsText) {
          gpsText.textContent = '✓ GPS locked — ' + acc.toFixed(0) + 'm accuracy';
        }
        
        const gpsDot = document.getElementById('gps-dot');
        if (gpsDot) {
          gpsDot.className = 'gps-indicator ok';
        }
        
        const gpsCoords = document.getElementById('gps-coords');
        if (gpsCoords) {
          gpsCoords.style.display = 'block';
        }
        
        const gpsLatLon = document.getElementById('gps-latlon');
        if (gpsLatLon) {
          gpsLatLon.textContent = lat.toFixed(6) + ', ' + lon.toFixed(6);
        }
        
        const gpsDistText = document.getElementById('gps-dist-text');
        if (gpsDistText) {
          gpsDistText.textContent = acc.toFixed(0) + 'm';
        }
        
        // Update map if callback is available
        if (typeof window.mapUpdateUserLocation === 'function') {
          window.mapUpdateUserLocation(lat, lon);
        }
      },
      error => {
        console.error('[GPS] Error:', error.code, error.message);
        const gpsText = document.getElementById('gps-text');
        if (gpsText) {
          gpsText.innerHTML = '❌ GPS Error: ' + error.message;
        }
        const gpsDot = document.getElementById('gps-dot');
        if (gpsDot) {
          gpsDot.className = 'gps-indicator error';
        }
      },
      { enableHighAccuracy: true, timeout: 10000, maximumAge: 0 }
    );
  }
  
  // Start GPS immediately
  console.log('[GPS] Starting geolocation watch');
  startGPS();
  
  // ========== 3. CAMERA CAPTURE FOR CHECK-IN ==========
  const photoZone = document.getElementById('photo-zone');
  if (photoZone) {
    console.log('[PHOTO-ZONE] Check-in zone found, adding click handler');
    photoZone.addEventListener('click', async (e) => {
      e.preventDefault();
      e.stopPropagation();
      console.log('[PHOTO-ZONE] Clicked - starting camera');
      try {
        const cam = new CameraManager('ci');
        const videoContainer = document.getElementById('ci-video-container');
        const captureBtn = document.getElementById('ci-btn-capture');
        const statusDiv = document.getElementById('ci-camera-status');
        
        console.log('[PHOTO-ZONE] Elements:', {
          videoContainer: !!videoContainer,
          captureBtn: !!captureBtn,
          statusDiv: !!statusDiv
        });
        
        photoZone.style.display = 'none';
        if (videoContainer) videoContainer.style.display = 'block';
        if (statusDiv) statusDiv.style.display = 'block';
        
        console.log('[PHOTO-ZONE] Starting camera...');
        await cam.start();
        console.log('[PHOTO-ZONE] Camera started successfully');
        
        if (captureBtn) {
          captureBtn.style.display = 'block';
          captureBtn.onclick = async () => {
            console.log('[PHOTO-ZONE] Capture button clicked');
            try {
              console.log('[PHOTO-ZONE] Capturing frame...');
              const jpeg = await cam.capture();
              console.log('[PHOTO-ZONE] Frame captured, size:', jpeg.length);
              
              await cam.stop();
              console.log('[PHOTO-ZONE] Camera stopped');
              
              if (videoContainer) videoContainer.style.display = 'none';
              if (statusDiv) statusDiv.style.display = 'none';
              if (captureBtn) captureBtn.style.display = 'none';
              
              const preview = document.getElementById('ci-selfie-preview');
              const previewImg = document.getElementById('ci-selfie-img');
              const retakeBtn = document.getElementById('ci-btn-retake');
              
              if (preview) preview.style.display = 'block';
              if (previewImg) {
                previewImg.src = jpeg;
                console.log('[PHOTO-ZONE] Preview image set');
              }
              if (retakeBtn) retakeBtn.style.display = 'block';
              
              window.ciSelfieData = jpeg;
              console.log('[PHOTO-ZONE] Uploading check-in photo, size:', jpeg.length);
              await uploadPhoto(jpeg, 'checkin');
            } catch (e) {
              console.error('[PHOTO-ZONE] Capture error:', e.message, e.stack);
              alert('❌ Capture failed: ' + e.message);
              await cam.stop();
              if (videoContainer) videoContainer.style.display = 'none';
              if (photoZone) photoZone.style.display = 'block';
            }
          };
        }
      } catch (e) {
        console.error('[PHOTO-ZONE] Error:', e.message, e.stack);
        alert('❌ Camera: ' + e.message);
        photoZone.style.display = 'block';
      }
    });
  } else {
    console.warn('[PHOTO-ZONE] Check-in photo-zone element NOT found on page');
  }
  
  // ========== 3b. CAMERA CAPTURE FOR CHECK-OUT ==========
  const coPhotoZone = document.getElementById('co-photo-zone');
  if (coPhotoZone) {
    console.log('[CO-PHOTO-ZONE] Check-out zone found, adding click handler');
    coPhotoZone.addEventListener('click', async (e) => {
      e.preventDefault();
      e.stopPropagation();
      console.log('[CO-PHOTO-ZONE] Clicked - starting camera');
      try {
        const cam = new CameraManager('co');
        const videoContainer = document.getElementById('co-video-container');
        const captureBtn = document.getElementById('co-btn-capture');
        const statusDiv = document.getElementById('co-camera-status');
        
        console.log('[CO-PHOTO-ZONE] Elements:', {
          videoContainer: !!videoContainer,
          captureBtn: !!captureBtn,
          statusDiv: !!statusDiv
        });
        
        coPhotoZone.style.display = 'none';
        if (videoContainer) videoContainer.style.display = 'block';
        if (statusDiv) statusDiv.style.display = 'block';
        
        console.log('[CO-PHOTO-ZONE] Starting camera...');
        await cam.start();
        console.log('[CO-PHOTO-ZONE] Camera started successfully');
        
        if (captureBtn) {
          captureBtn.style.display = 'block';
          captureBtn.onclick = async () => {
            console.log('[CO-PHOTO-ZONE] Capture button clicked');
            try {
              console.log('[CO-PHOTO-ZONE] Capturing frame...');
              const jpeg = await cam.capture();
              console.log('[CO-PHOTO-ZONE] Frame captured, size:', jpeg.length);
              
              await cam.stop();
              console.log('[CO-PHOTO-ZONE] Camera stopped');
              
              if (videoContainer) videoContainer.style.display = 'none';
              if (statusDiv) statusDiv.style.display = 'none';
              if (captureBtn) captureBtn.style.display = 'none';
              
              const preview = document.getElementById('co-selfie-preview');
              const previewImg = document.getElementById('co-selfie-img');
              const retakeBtn = document.getElementById('co-btn-retake');
              
              if (preview) preview.style.display = 'block';
              if (previewImg) {
                previewImg.src = jpeg;
                console.log('[CO-PHOTO-ZONE] Preview image set');
              }
              if (retakeBtn) retakeBtn.style.display = 'block';
              
              window.coSelfieData = jpeg;
              console.log('[CO-PHOTO-ZONE] Uploading check-out photo, size:', jpeg.length);
              await uploadPhoto(jpeg, 'checkout');
            } catch (e) {
              console.error('[CO-PHOTO-ZONE] Capture error:', e.message, e.stack);
              alert('❌ Capture failed: ' + e.message);
              await cam.stop();
              if (videoContainer) videoContainer.style.display = 'none';
              if (coPhotoZone) coPhotoZone.style.display = 'block';
            }
          };
        }
      } catch (e) {
        console.error('[CO-PHOTO-ZONE] Error:', e.message, e.stack);
        alert('❌ Camera: ' + e.message);
        coPhotoZone.style.display = 'block';
      }
    });
  } else {
    console.warn('[CO-PHOTO-ZONE] Check-out photo-zone element NOT found on page');
  }
  
  
  // ========== 4. PHOTO UPLOAD ==========
  async function uploadPhoto(jpeg, type) {
    console.log('[UPLOAD] Starting photo upload, type:', type, 'size:', jpeg.length);
    try {
      const csrf = document.querySelector('meta[name="csrf-token"]')?.getAttribute('content') || '';
      
      console.log('[UPLOAD] CSRF token present:', !!csrf);
      
      // Use /capture-selfie endpoint which handles base64 JSON
      const res = await fetch('/attendance/capture-selfie', {
        method: 'POST',
        headers: { 
          'Content-Type': 'application/json', 
          'X-CSRFToken': csrf 
        },
        body: JSON.stringify({ selfie: jpeg, type: type })
      });
      
      console.log('[UPLOAD] Response status:', res.status);
      console.log('[UPLOAD] Response content-type:', res.headers.get('content-type'));
      
      // Check if response is actually JSON
      const contentType = res.headers.get('content-type') || '';
      if (!contentType.includes('application/json')) {
        console.error('[UPLOAD] INVALID RESPONSE TYPE: Expected JSON but got', contentType);
        const text = await res.text();
        console.error('[UPLOAD] Response body (first 500 chars):', text.substring(0, 500));
        alert('❌ Server error (invalid response type). Check console.');
        return;
      }
      
      let d;
      try {
        d = await res.json();
      } catch (parseErr) {
        console.error('[UPLOAD] JSON PARSE ERROR:', parseErr.message);
        const text = await res.text();
        console.error('[UPLOAD] Response body:', text.substring(0, 200));
        alert('❌ Invalid response from server. Please try again.');
        return;
      }
      
      console.log('[UPLOAD] Response data:', d);
      
      if (!res.ok || !d.success) {
        console.error('[UPLOAD] Failed:', d.message || d.error);
        alert('❌ ' + (d.message || d.error || 'Upload failed'));
        return;
      }
      
      console.log('[UPLOAD] Success!');
      
      if (type === 'checkout') {
        window.coPhotoReady = true;
        
        const badge = document.getElementById('co-photo-badge');
        if (badge) {
          badge.className = 'badge bg-success-subtle text-success small';
          badge.innerHTML = '<i class="bi bi-check-circle me-1"></i>✓ Captured';
          console.log('[UI] Check-out photo badge updated');
        }
        
        const btn = document.getElementById('btn-checkout');
        if (btn) {
          btn.disabled = false;
          console.log('[UI] Check-out button enabled');
        }
        
        const text = document.getElementById('co-text');
        if (text) {
          text.textContent = 'Check Out Now';
          console.log('[UI] Check-out button text updated');
        }
        
        alert('✅ Check-out photo uploaded!');
      } else {
        window.ciPhotoReady = true;
        
        const badge = document.getElementById('ci-photo-badge');
        if (badge) {
          badge.className = 'badge bg-success-subtle text-success small';
          badge.innerHTML = '<i class="bi bi-check-circle me-1"></i>✓ Captured';
          console.log('[UI] Check-in photo badge updated');
        }
        
        const btn = document.getElementById('btn-checkin');
        if (btn) {
          btn.disabled = false;
          console.log('[UI] Check-in button enabled');
        }
        
        const text = document.getElementById('ci-text');
        if (text) {
          text.textContent = 'Check In Now';
          console.log('[UI] Check-in button text updated');
        }
        
        alert('✅ Check-in photo uploaded!');
      }
    } catch (e) {
      console.error('[UPLOAD] ERROR:', e.message);
      console.error('[UPLOAD] Stack:', e.stack);
      alert('❌ Upload: ' + e.message);
    }
  }
  
  // Make uploadPhoto globally available
  window.uploadPhoto = uploadPhoto;
  
  // ========== 5. CHECK-IN BUTTON HANDLER ==========
  const checkInBtn = document.getElementById('btn-checkin');
  if (checkInBtn) {
    checkInBtn.addEventListener('click', () => {
      console.log('[CHECKIN] Button clicked');
      
      if (!window.ciPhotoReady) {
        alert('⚠️ Upload check-in photo first');
        console.warn('[CHECKIN] Photo not ready');
        return;
      }
      
      if (!window.lastGPS || !window.lastGPS.lat) {
        alert('⚠️ Waiting for GPS...');
        console.warn('[CHECKIN] GPS not ready');
        return;
      }
      
      console.log('[CHECKIN] Ready - GPS:', window.lastGPS);
      checkInBtn.disabled = true;
      
      const spinner = document.getElementById('ci-spin');
      if (spinner) spinner.style.display = 'inline-block';
      
      const csrf = document.querySelector('meta[name="csrf-token"]')?.getAttribute('content') || '';
      const form = new FormData();
      form.append('latitude', window.lastGPS.lat);
      form.append('longitude', window.lastGPS.lon);
      form.append('accuracy', window.lastGPS.acc);
      
      fetch('/attendance/checkin', { 
        method: 'POST', 
        headers: { 'X-CSRFToken': csrf }, 
        body: form 
      })
        .then(r => r.json())
        .then(d => {
          console.log('[CHECKIN] Response:', d);
          if (spinner) spinner.style.display = 'none';
          
          if (d.success) {
            alert('✅ Checked in at ' + (d.check_in_time || 'now'));
            setTimeout(() => location.reload(), 1500);
          } else {
            alert('❌ ' + (d.message || 'Check-in failed'));
            checkInBtn.disabled = false;
          }
        })
        .catch(e => {
          console.error('[CHECKIN] Error:', e.message);
          if (spinner) spinner.style.display = 'none';
          alert('❌ ' + e.message);
          checkInBtn.disabled = false;
        });
    });
  } else {
    console.warn('[CHECKIN] btn-checkin element not found');
  }
  
  // ========== 5b. CHECK-OUT BUTTON HANDLER ==========
  const checkOutBtn = document.getElementById('btn-checkout');
  if (checkOutBtn) {
    checkOutBtn.addEventListener('click', () => {
      console.log('[CHECKOUT] Button clicked');
      
      if (!window.coPhotoReady) {
        alert('⚠️ Upload check-out photo first');
        console.warn('[CHECKOUT] Photo not ready');
        return;
      }
      
      if (!window.lastGPS || !window.lastGPS.lat) {
        alert('⚠️ Waiting for GPS...');
        console.warn('[CHECKOUT] GPS not ready');
        return;
      }
      
      console.log('[CHECKOUT] Ready - GPS:', window.lastGPS);
      checkOutBtn.disabled = true;
      
      const spinner = document.getElementById('co-spin');
      if (spinner) spinner.style.display = 'inline-block';
      
      const csrf = document.querySelector('meta[name="csrf-token"]')?.getAttribute('content') || '';
      const form = new FormData();
      form.append('latitude', window.lastGPS.lat);
      form.append('longitude', window.lastGPS.lon);
      form.append('accuracy', window.lastGPS.acc);
      
      fetch('/attendance/checkout', { 
        method: 'POST', 
        headers: { 'X-CSRFToken': csrf }, 
        body: form 
      })
        .then(r => r.json())
        .then(d => {
          console.log('[CHECKOUT] Response:', d);
          if (spinner) spinner.style.display = 'none';
          
          if (d.success) {
            alert('✅ Checked out at ' + (d.check_out_time || 'now'));
            setTimeout(() => location.reload(), 1500);
          } else {
            alert('❌ ' + (d.message || 'Check-out failed'));
            checkOutBtn.disabled = false;
          }
        })
        .catch(e => {
          console.error('[CHECKOUT] Error:', e.message);
          if (spinner) spinner.style.display = 'none';
          alert('❌ ' + e.message);
          checkOutBtn.disabled = false;
        });
    });
  } else {
    console.warn('[CHECKOUT] btn-checkout element not found');
  }
  
  // ========== 6. RETAKE BUTTONS ==========
  const retakeBtnCI = document.getElementById('ci-btn-retake');
  if (retakeBtnCI) {
    retakeBtnCI.addEventListener('click', () => {
      console.log('[RETAKE-CI] Clicked');
      const photoZone = document.getElementById('photo-zone');
      const preview = document.getElementById('ci-selfie-preview');
      const captureBtn = document.getElementById('ci-btn-capture');
      
      if (preview) preview.style.display = 'none';
      if (retakeBtnCI) retakeBtnCI.style.display = 'none';
      if (photoZone) photoZone.style.display = 'block';
      if (captureBtn) captureBtn.style.display = 'none';
      
      window.ciPhotoReady = false;
    });
  }
  
  const retakeBtnCO = document.getElementById('co-btn-retake');
  if (retakeBtnCO) {
    retakeBtnCO.addEventListener('click', () => {
      console.log('[RETAKE-CO] Clicked');
      const photoZone = document.getElementById('co-photo-zone');
      const preview = document.getElementById('co-selfie-preview');
      const captureBtn = document.getElementById('co-btn-capture');
      
      if (preview) preview.style.display = 'none';
      if (retakeBtnCO) retakeBtnCO.style.display = 'none';
      if (photoZone) photoZone.style.display = 'block';
      if (captureBtn) captureBtn.style.display = 'none';
      
      window.coPhotoReady = false;
    });
  }
  
  console.log('[ATTENDANCE] Phase 1 complete - All handlers registered');
})();

// ============================================================================
// LEAFLET MAP INITIALIZATION — GPS Verification with Geofence
// ============================================================================

(function() {
  console.log('[MAP] Phase 2: Leaflet map initialization starting');
  
  // ========== 1. PARSE OFFICE DATA ==========
  function getOfficeData() {
    try {
      const officeDataEl = document.getElementById('office-data');
      if (!officeDataEl) {
        console.error('[MAP] office-data script element not found');
        return null;
      }
      
      const data = JSON.parse(officeDataEl.textContent);
      console.log('[MAP] Office data loaded:', data);
      return data;
    } catch (e) {
      console.error('[MAP] Failed to parse office data:', e.message);
      return null;
    }
  }
  
  const officeData = getOfficeData();
  if (!officeData) {
    console.warn('[MAP] Cannot initialize map - office data unavailable');
    return;
  }
  
  // ========== 2. INITIALIZE MAP ==========
  let map = null;
  let userMarker = null;
  let geofenceCircle = null;
  
  function initMap() {
    try {
      // Create map instance
      map = L.map('att-map').setView(
        [officeData.lat, officeData.lon],
        16
      );
      
      console.log('[MAP] Map instance created, centered on office');
      
      // Add OpenStreetMap tile layer
      L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
        attribution: '© OpenStreetMap contributors',
        maxZoom: 19,
        minZoom: 12
      }).addTo(map);
      
      console.log('[MAP] Tile layer added');
      
      // Add office location marker (red pin)
      const officeMarker = L.marker(
        [officeData.lat, officeData.lon],
        {
          icon: L.icon({
            iconUrl: 'https://raw.githubusercontent.com/pointhi/leaflet-color-markers/master/img/marker-icon-2x-red.png',
            shadowUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/0.7.7/images/marker-shadow.png',
            iconSize: [25, 41],
            iconAnchor: [12, 41],
            popupAnchor: [1, -34],
            shadowSize: [41, 41]
          }),
          title: 'Office Location: ' + officeData.name
        }
      )
        .bindPopup(officeData.name + '<br>Lat: ' + officeData.lat.toFixed(6) + '<br>Lon: ' + officeData.lon.toFixed(6))
        .addTo(map);
      
      console.log('[MAP] Office marker added at', officeData.lat, officeData.lon);
      
      // Add geofence circle (green)
      geofenceCircle = L.circle(
        [officeData.lat, officeData.lon],
        {
          radius: officeData.radius,
          color: '#10b981',
          fillColor: '#d1fae5',
          fillOpacity: 0.2,
          weight: 2,
          dashArray: '4, 4'
        }
      )
        .bindPopup('Geofence Radius: ' + officeData.radius + 'm')
        .addTo(map);
      
      console.log('[MAP] Geofence circle added, radius:', officeData.radius, 'm');
      
      // Add user location marker (blue) — will be updated when GPS updates
      if (window.lastGPS && window.lastGPS.lat) {
        userMarker = L.marker(
          [window.lastGPS.lat, window.lastGPS.lon],
          {
            icon: L.icon({
              iconUrl: 'https://raw.githubusercontent.com/pointhi/leaflet-color-markers/master/img/marker-icon-2x-blue.png',
              shadowUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/0.7.7/images/marker-shadow.png',
              iconSize: [25, 41],
              iconAnchor: [12, 41],
              popupAnchor: [1, -34],
              shadowSize: [41, 41]
            }),
            title: 'Your Location'
          }
        )
          .bindPopup('Your Location<br>Lat: ' + window.lastGPS.lat.toFixed(6) + '<br>Lon: ' + window.lastGPS.lon.toFixed(6))
          .addTo(map);
        
        console.log('[MAP] User marker added at', window.lastGPS.lat, window.lastGPS.lon);
      } else {
        console.warn('[MAP] GPS not available yet, user marker will be added when GPS locks');
      }
      
      // ========== 3. GPS UPDATE CALLBACK ==========
      // This function will be called whenever GPS position updates
      window.mapUpdateUserLocation = function(lat, lon) {
        try {
          if (!map) {
            console.warn('[MAP] Map not initialized yet');
            return;
          }
          
          if (!userMarker) {
            // Create marker if it doesn't exist
            userMarker = L.marker(
              [lat, lon],
              {
                icon: L.icon({
                  iconUrl: 'https://raw.githubusercontent.com/pointhi/leaflet-color-markers/master/img/marker-icon-2x-blue.png',
                  shadowUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/0.7.7/images/marker-shadow.png',
                  iconSize: [25, 41],
                  iconAnchor: [12, 41],
                  popupAnchor: [1, -34],
                  shadowSize: [41, 41]
                }),
                title: 'Your Location'
              }
            )
              .bindPopup('Your Location<br>Lat: ' + lat.toFixed(6) + '<br>Lon: ' + lon.toFixed(6))
              .addTo(map);
            
            console.log('[MAP] User marker created at', lat, lon);
          } else {
            // Update existing marker
            userMarker.setLatLng([lat, lon]);
            userMarker.setPopupContent('Your Location<br>Lat: ' + lat.toFixed(6) + '<br>Lon: ' + lon.toFixed(6));
          }
        } catch (e) {
          console.error('[MAP] Error updating user location:', e.message);
        }
      };
      
      console.log('[MAP] mapUpdateUserLocation callback registered');
      
      // Fit map to show both office and user (if available)
      if (userMarker) {
        const group = new L.featureGroup([officeMarker, userMarker, geofenceCircle]);
        map.fitBounds(group.getBounds(), { padding: [50, 50] });
        console.log('[MAP] Map view adjusted to fit office and user markers');
      }
      
      console.log('[MAP] Leaflet map initialization complete');
    } catch (e) {
      console.error('[MAP] Initialization error:', e.message, e.stack);
    }
  }
  
  // Initialize map when DOM is ready
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initMap);
    console.log('[MAP] Waiting for DOMContentLoaded');
  } else {
    // DOM already loaded (this script runs in extra_js after </body>)
    console.log('[MAP] DOM ready, initializing map immediately');
    initMap();
  }
})();
