'use strict';

// MINIMAL ATTENDANCE MODULE — GPS + Camera + Check-in (no map dependency)

(function(){
  const el = id => document.getElementById(id);
  let ciReady = false, coReady = false;
  let lastGPS = { lat: null, lon: null, acc: null };

  // GPS tracking — no map, just coordinates
  function startGPS() {
    if (!navigator.geolocation) {
      el('gps-text').innerHTML = '❌ Geolocation not available';
      el('gps-dot').className = 'gps-indicator error';
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
        
        el('gps-dot').className = 'gps-indicator ok';
        el('gps-text').textContent = '✓ GPS locked — ' + acc.toFixed(0) + 'm accuracy';
        el('gps-coords').style.display = 'block';
        el('gps-latlon').textContent = lat.toFixed(6) + ', ' + lon.toFixed(6);
        el('gps-dist-text').textContent = acc.toFixed(0) + 'm';
      },
      error => {
        el('gps-dot').className = 'gps-indicator error';
        el('gps-text').innerHTML = '❌ GPS Error: ' + error.message;
      },
      { enableHighAccuracy: true, timeout: 10000, maximumAge: 0 }
    );
  }

  // ──────────────────────────────────────────────────────────────────────────
  // CAMERA + PHOTO UPLOAD
  // ──────────────────────────────────────────────────────────────────────────

  el('photo-zone')?.addEventListener('click', async() => {
    try {
      const cam = new CameraCapture('ci-video', 'ci-canvas');
      el('photo-zone').style.display = 'none';
      el('ci-video-container').style.display = 'block';
      el('ci-btn-capture').style.display = 'block';
      
      await cam.start();
      
      el('ci-btn-capture').onclick = async() => {
        const jpeg = await cam.capture();
        await cam.stop();
        
        el('ci-video-container').style.display = 'none';
        el('ci-selfie-preview').style.display = 'block';
        el('ci-selfie-img').src = jpeg;
        el('ci-btn-capture').style.display = 'none';
        el('ci-btn-retake').style.display = 'block';
        
        await uploadCheckIn(jpeg);
      };
    } catch (e) {
      alert('📷 Camera error: ' + e.message);
    }
  });

  el('co-photo-zone')?.addEventListener('click', async() => {
    try {
      const cam = new CameraCapture('co-video', 'co-canvas');
      el('co-photo-zone').style.display = 'none';
      el('co-video-container').style.display = 'block';
      el('co-btn-capture').style.display = 'block';
      
      await cam.start();
      
      el('co-btn-capture').onclick = async() => {
        const jpeg = await cam.capture();
        await cam.stop();
        
        el('co-video-container').style.display = 'none';
        el('co-selfie-preview').style.display = 'block';
        el('co-selfie-img').src = jpeg;
        el('co-btn-capture').style.display = 'none';
        el('co-btn-retake').style.display = 'block';
        
        await uploadCheckOut(jpeg);
      };
    } catch (e) {
      alert('📷 Camera error: ' + e.message);
    }
  });

  el('ci-btn-retake')?.addEventListener('click', () => {
    el('ci-selfie-preview').style.display = 'none';
    el('photo-zone').style.display = 'block';
    ciReady = false;
  });

  el('co-btn-retake')?.addEventListener('click', () => {
    el('co-selfie-preview').style.display = 'none';
    el('co-photo-zone').style.display = 'block';
    coReady = false;
  });

  async function uploadCheckIn(jpeg) {
    try {
      const csrf = document.querySelector('meta[name="csrf-token"]')?.getAttribute('content') || '';
      const res = await fetch('/attendance/capture-selfie', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', 'X-CSRFToken': csrf },
        body: JSON.stringify({ selfie: jpeg, type: 'checkin' })
      });
      
      const d = await res.json();
      if (!res.ok || !d.success) {
        alert('❌ ' + (d.message || 'Upload failed'));
        return;
      }
      
      ciReady = true;
      el('ci-photo-badge').className = 'badge bg-success-subtle text-success small';
      el('ci-photo-badge').innerHTML = '<i class="bi bi-check-circle me-1"></i>✓ Captured';
      el('ci-text').textContent = 'Check In Now';
      el('btn-checkin').disabled = false;
      alert('✅ Photo uploaded! Button enabled.');
    } catch (e) {
      alert('❌ Upload error: ' + e.message);
    }
  }

  async function uploadCheckOut(jpeg) {
    try {
      const csrf = document.querySelector('meta[name="csrf-token"]')?.getAttribute('content') || '';
      const res = await fetch('/attendance/capture-selfie', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', 'X-CSRFToken': csrf },
        body: JSON.stringify({ selfie: jpeg, type: 'checkout' })
      });
      
      const d = await res.json();
      if (!res.ok || !d.success) {
        alert('❌ ' + (d.message || 'Upload failed'));
        return;
      }
      
      coReady = true;
      el('co-photo-badge').className = 'badge bg-success-subtle text-success small';
      el('co-photo-badge').innerHTML = '<i class="bi bi-check-circle me-1"></i>✓ Captured';
      el('co-text').textContent = 'Check Out Now';
      el('btn-checkout').disabled = false;
      alert('✅ Photo uploaded! Button enabled.');
    } catch (e) {
      alert('❌ Upload error: ' + e.message);
    }
  }

  // ──────────────────────────────────────────────────────────────────────────
  // CHECK-IN / CHECK-OUT BUTTONS
  // ──────────────────────────────────────────────────────────────────────────

  el('btn-checkin')?.addEventListener('click', () => {
    if (!ciReady) {
      alert('⚠️ Please capture and upload your selfie first');
      return;
    }
    if (!lastGPS.lat) {
      alert('⚠️ GPS not available yet. Please wait...');
      return;
    }
    
    const csrf = document.querySelector('meta[name="csrf-token"]')?.getAttribute('content') || '';
    const form = new FormData();
    form.append('latitude', lastGPS.lat);
    form.append('longitude', lastGPS.lon);
    form.append('accuracy', lastGPS.acc);
    
    el('btn-checkin').disabled = true;
    
    fetch('/attendance/checkin', {
      method: 'POST',
      headers: { 'X-CSRFToken': csrf },
      body: form
    })
    .then(r => r.json())
    .then(d => {
      if (d.success) {
        alert('✅ Check-in successful!');
        setTimeout(() => location.reload(), 1000);
      } else {
        alert('❌ ' + (d.message || 'Check-in failed'));
        el('btn-checkin').disabled = false;
      }
    })
    .catch(e => {
      alert('❌ ' + e.message);
      el('btn-checkin').disabled = false;
    });
  });

  el('btn-checkout')?.addEventListener('click', () => {
    if (!coReady) {
      alert('⚠️ Please capture and upload your selfie first');
      return;
    }
    if (!lastGPS.lat) {
      alert('⚠️ GPS not available yet. Please wait...');
      return;
    }
    
    const csrf = document.querySelector('meta[name="csrf-token"]')?.getAttribute('content') || '';
    const form = new FormData();
    form.append('latitude', lastGPS.lat);
    form.append('longitude', lastGPS.lon);
    form.append('accuracy', lastGPS.acc);
    
    el('btn-checkout').disabled = true;
    
    fetch('/attendance/checkout', {
      method: 'POST',
      headers: { 'X-CSRFToken': csrf },
      body: form
    })
    .then(r => r.json())
    .then(d => {
      if (d.success) {
        alert('✅ Check-out successful!');
        setTimeout(() => location.reload(), 1000);
      } else {
        alert('❌ ' + (d.message || 'Check-out failed'));
        el('btn-checkout').disabled = false;
      }
    })
    .catch(e => {
      alert('❌ ' + e.message);
      el('btn-checkout').disabled = false;
    });
  });

  // ──────────────────────────────────────────────────────────────────────────
  // INIT ON DOM READY
  // ──────────────────────────────────────────────────────────────────────────

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', startGPS);
  } else {
    startGPS();
  }

})();

