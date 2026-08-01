// ============================================================================
// COMPLETE ATTENDANCE SYSTEM - TIME + GPS + CAMERA + CHECK-IN
// ============================================================================
// This script MUST run immediately and work standalone
// No dependencies on other modules or async loading
// ============================================================================

console.log('[ATTENDANCE] Loading attendance.js - COMPLETE VERSION');

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
  
  // ========== 3. CAMERA CAPTURE ==========
  const photoZone = document.getElementById('photo-zone');
  if (photoZone) {
    photoZone.addEventListener('click', async () => {
      console.log('[CAMERA] Photo zone clicked');
      try {
        if (typeof CameraCapture === 'undefined') {
          throw new Error('CameraCapture not loaded');
        }
        
        const cam = new CameraCapture('ci-video', 'ci-canvas');
        const photoZone = document.getElementById('photo-zone');
        const videoContainer = document.getElementById('ci-video-container');
        const captureBtn = document.getElementById('ci-btn-capture');
        
        if (photoZone) photoZone.style.display = 'none';
        if (videoContainer) videoContainer.style.display = 'block';
        if (captureBtn) captureBtn.style.display = 'block';
        
        console.log('[CAMERA] Starting camera');
        await cam.start();
        console.log('[CAMERA] Camera started');
        
        if (captureBtn) {
          captureBtn.onclick = async () => {
            console.log('[CAMERA] Capture button clicked');
            const jpeg = await cam.capture();
            console.log('[CAMERA] Frame captured, size:', jpeg.length);
            
            await cam.stop();
            console.log('[CAMERA] Camera stopped');
            
            if (videoContainer) videoContainer.style.display = 'none';
            
            const preview = document.getElementById('ci-selfie-preview');
            const previewImg = document.getElementById('ci-selfie-img');
            const retakeBtn = document.getElementById('ci-btn-retake');
            
            if (preview) preview.style.display = 'block';
            if (previewImg) previewImg.src = jpeg;
            if (captureBtn) captureBtn.style.display = 'none';
            if (retakeBtn) retakeBtn.style.display = 'block';
            
            console.log('[CAMERA] Uploading photo');
            await uploadPhoto(jpeg, 'checkin');
          };
        }
      } catch (e) {
        console.error('[CAMERA] Error:', e.message);
        alert('❌ Camera: ' + e.message);
      }
    });
  } else {
    console.warn('[CAMERA] photo-zone element not found');
  }
  
  // ========== 4. PHOTO UPLOAD ==========
  async function uploadPhoto(jpeg, type) {
    console.log('[UPLOAD] Starting photo upload, type:', type, 'size:', jpeg.length);
    try {
      const csrf = document.querySelector('meta[name="csrf-token"]')?.getAttribute('content') || '';
      const res = await fetch('/attendance/capture-selfie', {
        method: 'POST',
        headers: { 
          'Content-Type': 'application/json', 
          'X-CSRFToken': csrf 
        },
        body: JSON.stringify({ selfie: jpeg, type: type })
      });
      
      console.log('[UPLOAD] Response status:', res.status);
      const d = await res.json();
      console.log('[UPLOAD] Response data:', d);
      
      if (!res.ok || !d.success) {
        console.error('[UPLOAD] Failed:', d.message);
        alert('❌ ' + (d.message || 'Upload failed'));
        return;
      }
      
      console.log('[UPLOAD] Success!');
      
      if (type === 'checkin') {
        window.ciReady = true;
        
        const badge = document.getElementById('ci-photo-badge');
        if (badge) {
          badge.className = 'badge bg-success-subtle text-success small';
          badge.innerHTML = '<i class="bi bi-check-circle me-1"></i>✓ Captured';
          console.log('[UI] Badge updated');
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
        
        alert('✅ Photo uploaded!');
      }
    } catch (e) {
      console.error('[UPLOAD] Error:', e.message);
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
      
      if (!window.ciReady) {
        alert('⚠️ Upload photo first');
        console.warn('[CHECKIN] Photo not ready');
        return;
      }
      
      if (!window.lastGPS || !window.lastGPS.lat) {
        alert('⚠️ Waiting for GPS...');
        console.warn('[CHECKIN] GPS not ready');
        return;
      }
      
      console.log('[CHECKIN] Ready - GPS:', window.lastGPS);
      
      const csrf = document.querySelector('meta[name="csrf-token"]')?.getAttribute('content') || '';
      const form = new FormData();
      form.append('latitude', window.lastGPS.lat);
      form.append('longitude', window.lastGPS.lon);
      form.append('accuracy', window.lastGPS.acc);
      
      checkInBtn.disabled = true;
      
      fetch('/attendance/checkin', { 
        method: 'POST', 
        headers: { 'X-CSRFToken': csrf }, 
        body: form 
      })
        .then(r => r.json())
        .then(d => {
          console.log('[CHECKIN] Response:', d);
          if (d.success) {
            alert('✅ Checked in!');
            setTimeout(() => location.reload(), 1500);
          } else {
            alert('❌ ' + (d.message || 'Failed'));
            checkInBtn.disabled = false;
          }
        })
        .catch(e => {
          console.error('[CHECKIN] Error:', e.message);
          alert('❌ ' + e.message);
          checkInBtn.disabled = false;
        });
    });
  } else {
    console.warn('[CHECKIN] btn-checkin element not found');
  }
  
  // ========== RETAKE BUTTON ==========
  const retakeBtn = document.getElementById('ci-btn-retake');
  if (retakeBtn) {
    retakeBtn.addEventListener('click', () => {
      console.log('[CAMERA] Retake clicked');
      const photoZone = document.getElementById('photo-zone');
      const preview = document.getElementById('ci-selfie-preview');
      const captureBtn = document.getElementById('ci-btn-capture');
      
      if (preview) preview.style.display = 'none';
      if (retakeBtn) retakeBtn.style.display = 'none';
      if (photoZone) photoZone.style.display = 'block';
      if (captureBtn) captureBtn.style.display = 'none';
    });
  }
  
  console.log('[ATTENDANCE] Phase 1 complete - All handlers registered');
})();
