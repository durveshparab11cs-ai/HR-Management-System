'use strict';

// Complete attendance module with time + GPS + camera + check-in

(function(){
  const el = id => document.getElementById(id);
  let ciReady = false, coReady = false;
  let lastGPS = { lat: null, lon: null, acc: null };

  // 1. TIME CLOCK
  function updateClock() {
    const now = new Date();
    const h = String(now.getHours()).padStart(2, '0');
    const m = String(now.getMinutes()).padStart(2, '0');
    const s = String(now.getSeconds()).padStart(2, '0');
    const clock = el('att-clock');
    if (clock) clock.textContent = h + ':' + m + ':' + s;
  }

  function updateDate() {
    const now = new Date();
    const day = now.toLocaleDateString('en-US', { weekday: 'long' });
    const date = now.toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' });
    const dateEl = el('att-date');
    if (dateEl) dateEl.textContent = day + ', ' + date;
  }

  // 2. GPS
  function startGPS() {
    if (!navigator.geolocation) {
      const gpsText = el('gps-text');
      if (gpsText) gpsText.innerHTML = '❌ Geolocation not available';
      return;
    }

    navigator.geolocation.watchPosition(
      position => {
        const lat = position.coords.latitude;
        const lon = position.coords.longitude;
        const acc = position.coords.accuracy;
        
        lastGPS = { lat, lon, acc };
        window.lat = lat;
        window.lon = lon;
        window.acc = acc;
        
        const gpsText = el('gps-text');
        if (gpsText) gpsText.textContent = '✓ GPS locked — ' + acc.toFixed(0) + 'm accuracy';
        const gpsDot = el('gps-dot');
        if (gpsDot) gpsDot.className = 'gps-indicator ok';
        const gpsCoords = el('gps-coords');
        if (gpsCoords) gpsCoords.style.display = 'block';
        const gpsLatLon = el('gps-latlon');
        if (gpsLatLon) gpsLatLon.textContent = lat.toFixed(6) + ', ' + lon.toFixed(6);
        const gpsDistText = el('gps-dist-text');
        if (gpsDistText) gpsDistText.textContent = acc.toFixed(0) + 'm';
      },
      error => {
        const gpsText = el('gps-text');
        if (gpsText) gpsText.innerHTML = '❌ GPS Error: ' + error.message;
        const gpsDot = el('gps-dot');
        if (gpsDot) gpsDot.className = 'gps-indicator error';
      },
      { enableHighAccuracy: true, timeout: 10000, maximumAge: 0 }
    );
  }

  // 3. CAMERA CAPTURE
  el('photo-zone')?.addEventListener('click', async () => {
    try {
      if (typeof CameraCapture === 'undefined') throw new Error('CameraCapture not loaded');
      
      const cam = new CameraCapture('ci-video', 'ci-canvas');
      el('photo-zone').style.display = 'none';
      el('ci-video-container').style.display = 'block';
      el('ci-btn-capture').style.display = 'block';
      
      await cam.start();
      
      el('ci-btn-capture').onclick = async () => {
        const jpeg = await cam.capture();
        await cam.stop();
        
        el('ci-video-container').style.display = 'none';
        el('ci-selfie-preview').style.display = 'block';
        el('ci-selfie-img').src = jpeg;
        el('ci-btn-capture').style.display = 'none';
        el('ci-btn-retake').style.display = 'block';
        
        uploadPhoto(jpeg, 'checkin');
      };
    } catch (e) {
      alert('❌ Camera: ' + e.message);
    }
  });

  async function uploadPhoto(jpeg, type) {
    try {
      const csrf = document.querySelector('meta[name="csrf-token"]')?.getAttribute('content') || '';
      const res = await fetch('/attendance/capture-selfie', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', 'X-CSRFToken': csrf },
        body: JSON.stringify({ selfie: jpeg, type: type })
      });
      
      const d = await res.json();
      if (!res.ok || !d.success) {
        alert('❌ ' + (d.message || 'Upload failed'));
        return;
      }
      
      if (type === 'checkin') {
        ciReady = true;
        const badge = el('ci-photo-badge');
        if (badge) {
          badge.className = 'badge bg-success-subtle text-success small';
          badge.innerHTML = '<i class="bi bi-check-circle me-1"></i>✓ Captured';
        }
        const btn = el('btn-checkin');
        if (btn) btn.disabled = false;
        const text = el('ci-text');
        if (text) text.textContent = 'Check In Now';
        alert('✅ Photo uploaded!');
      }
    } catch (e) {
      alert('❌ Upload: ' + e.message);
    }
  }

  // 4. CHECK-IN BUTTON
  el('btn-checkin')?.addEventListener('click', () => {
    if (!ciReady) {
      alert('⚠️ Upload photo first');
      return;
    }
    if (!lastGPS.lat) {
      alert('⚠️ Waiting for GPS...');
      return;
    }
    
    const csrf = document.querySelector('meta[name="csrf-token"]')?.getAttribute('content') || '';
    const form = new FormData();
    form.append('latitude', lastGPS.lat);
    form.append('longitude', lastGPS.lon);
    form.append('accuracy', lastGPS.acc);
    
    el('btn-checkin').disabled = true;
    
    fetch('/attendance/checkin', { method: 'POST', headers: { 'X-CSRFToken': csrf }, body: form })
      .then(r => r.json())
      .then(d => {
        if (d.success) {
          alert('✅ Checked in!');
          setTimeout(() => location.reload(), 1500);
        } else {
          alert('❌ ' + (d.message || 'Failed'));
          el('btn-checkin').disabled = false;
        }
      })
      .catch(e => {
        alert('❌ ' + e.message);
        el('btn-checkin').disabled = false;
      });
  });

  // INIT
  updateClock();
  updateDate();
  setInterval(updateClock, 1000);
  startGPS();
  
})();
