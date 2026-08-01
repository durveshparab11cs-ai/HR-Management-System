'use strict';

// ═════════════════════════════════════════════════════════════════════════════
// ATTENDANCE MODULE — GPS + Camera + Check-in/out
// ═════════════════════════════════════════════════════════════════════════════

(function(){
  'use strict';

  const el = id => document.getElementById(id);
  let ciReady = false, coReady = false;
  let map = null, gpsMarker = null, officeCircle = null;
  let lastGPS = { lat: null, lon: null, acc: null };

  // ──────────────────────────────────────────────────────────────────────────
  // GPS & MAP INITIALIZATION
  // ──────────────────────────────────────────────────────────────────────────

  function initMap() {
    try {
      const officeData = JSON.parse(el('office-data').textContent);
      
      // Create map
      map = L.map('att-map').setView([officeData.lat, officeData.lon], 17);
      L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
        attribution: '© OpenStreetMap',
        maxZoom: 19
      }).addTo(map);
      
      // Office location marker
      const officeMarker = L.marker([officeData.lat, officeData.lon], {
        icon: L.icon({
          iconUrl: 'data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iMzIiIGhlaWdodD0iMzIiIHZpZXdCb3g9IjAgMCAzMiAzMiIgZmlsbD0ibm9uZSIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj48Y2lyY2xlIGN4PSIxNiIgY3k9IjE2IiByPSIxNCIgZmlsbD0iIzEwYjk4MSIgc3Ryb2tlPSIjZmZmIiBzdHJva2Utd2lkdGg9IjIiLz48cGF0aCBkPSJNMTYgOHY2bTMtM2gtNiIgc3Ryb2tlPSIjZmZmIiBzdHJva2Utd2lkdGg9IjIiIHN0cm9rZS1saW5lY2FwPSJyb3VuZCIvPjwvc3ZnPg==',
          iconSize: [32, 32],
          iconAnchor: [16, 16]
        })
      }).addTo(map).bindPopup('<strong>'+officeData.name+'</strong><br>Office Location');
      
      // Geofence circle
      officeCircle = L.circle([officeData.lat, officeData.lon], {
        radius: officeData.radius,
        color: '#10b981',
        fillColor: '#d1fae5',
        fillOpacity: 0.2,
        weight: 2,
        dashArray: '5,5'
      }).addTo(map);
      
      console.log('[MAP] Initialized with office at', officeData.lat, officeData.lon);
      startGPS();
    } catch (e) {
      console.error('[MAP] Init failed:', e);
      el('gps-text').innerHTML = '<i class="bi bi-exclamation-circle"></i> Map error: ' + e.message;
    }
  }

  // ──────────────────────────────────────────────────────────────────────────
  // GPS TRACKING
  // ──────────────────────────────────────────────────────────────────────────

  function startGPS() {
    const officeData = JSON.parse(el('office-data').textContent);
    
    if (!navigator.geolocation) {
      el('gps-text').innerHTML = '<i class="bi bi-exclamation-circle"></i> Geolocation not available';
      el('gps-dot').className = 'gps-indicator error';
      return;
    }

    console.log('[GPS] Starting geolocation watch...');
    
    const watchId = navigator.geolocation.watchPosition(
      position => {
        const lat = position.coords.latitude;
        const lon = position.coords.longitude;
        const acc = position.coords.accuracy;
        
        lastGPS = { lat, lon, acc };
        window.lat = lat;
        window.lon = lon;
        window.acc = acc;
        
        console.log('[GPS] Position:', lat.toFixed(6), lon.toFixed(6), 'acc±'+acc.toFixed(0)+'m');
        
        // Update map
        if (gpsMarker) map.removeLayer(gpsMarker);
        gpsMarker = L.marker([lat, lon], {
          icon: L.icon({
            iconUrl: 'data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iMjgiIGhlaWdodD0iMjgiIHZpZXdCb3g9IjAgMCAyOCAyOCIgZmlsbD0ibm9uZSIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj48Y2lyY2xlIGN4PSIxNCIgY3k9IjE0IiByPSIxMiIgZmlsbD0iIzMwODlmYyIgc3Ryb2tlPSIjZmZmIiBzdHJva2Utd2lkdGg9IjIiLz48Y2lyY2xlIGN4PSIxNCIgY3k9IjE0IiByPSI2IiBmaWxsPSIjZmZmIi8+PC9zdmc+',
            iconSize: [28, 28],
            iconAnchor: [14, 14]
          })
        }).addTo(map);
        
        // Calculate distance
        const R = 6371000; // Earth radius in meters
        const dLat = (officeData.lat - lat) * Math.PI / 180;
        const dLon = (officeData.lon - lon) * Math.PI / 180;
        const a = Math.sin(dLat/2) * Math.sin(dLat/2) +
                  Math.cos(lat * Math.PI / 180) * Math.cos(officeData.lat * Math.PI / 180) *
                  Math.sin(dLon/2) * Math.sin(dLon/2);
        const c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1-a));
        const dist = R * c;
        
        const inside = dist <= officeData.radius;
        const badge = el('gps-dist-badge');
        badge.innerHTML = '<span class="dist-badge '+(inside?'inside':'outside')+'">' +
          '<i class="bi bi-'+(inside?'check-circle':'x-circle')+'"></i> ' +
          dist.toFixed(0) + 'm from office</span>';
        
        // Update status
        el('gps-dot').className = 'gps-indicator ' + (inside ? 'ok' : 'found');
        el('gps-text').textContent = (inside ? '✓' : '⚠') + ' GPS OK — ' + dist.toFixed(0) + 'm away';
        el('gps-latlon').textContent = lat.toFixed(6) + ', ' + lon.toFixed(6);
        el('gps-coords').style.display = 'block';
        el('gps-dist-text').textContent = dist.toFixed(0) + 'm';
        
        // Show rejection if outside
        if (!inside) {
          el('rejection-box').style.display = 'block';
          el('rj-emp-dist').textContent = dist.toFixed(0) + 'm';
          el('rj-allowed').textContent = officeData.radius + 'm';
          el('rj-move-by').textContent = (dist - officeData.radius).toFixed(0) + 'm closer';
        } else {
          el('rejection-box').style.display = 'none';
        }
        
        // Zoom map to show both
        const bounds = L.latLngBounds([[lat, lon], [officeData.lat, officeData.lon]]);
        map.fitBounds(bounds.pad(0.1));
      },
      error => {
        console.error('[GPS] Error:', error.code, error.message);
        el('gps-dot').className = 'gps-indicator error';
        
        let msg = 'GPS Error';
        if (error.code === 1) msg = 'Location permission denied';
        else if (error.code === 2) msg = 'GPS unavailable';
        else if (error.code === 3) msg = 'GPS timeout';
        
        el('gps-text').innerHTML = '<i class="bi bi-exclamation-triangle"></i> ' + msg;
      },
      {
        enableHighAccuracy: true,
        timeout: 10000,
        maximumAge: 0
      }
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
      console.log('[CAMERA] Check-in camera started');
      
      el('ci-btn-capture').onclick = async() => {
        const jpeg = await cam.capture();
        await cam.stop();
        
        el('ci-video-container').style.display = 'none';
        el('ci-selfie-preview').style.display = 'block';
        el('ci-selfie-img').src = jpeg;
        el('ci-btn-capture').style.display = 'none';
        el('ci-btn-retake').style.display = 'block';
        
        console.log('[UPLOAD] Uploading check-in photo...');
        await uploadCheckIn(jpeg);
      };
    } catch (e) {
      console.error('[CAMERA] Error:', e);
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
      console.log('[CAMERA] Check-out camera started');
      
      el('co-btn-capture').onclick = async() => {
        const jpeg = await cam.capture();
        await cam.stop();
        
        el('co-video-container').style.display = 'none';
        el('co-selfie-preview').style.display = 'block';
        el('co-selfie-img').src = jpeg;
        el('co-btn-capture').style.display = 'none';
        el('co-btn-retake').style.display = 'block';
        
        console.log('[UPLOAD] Uploading check-out photo...');
        await uploadCheckOut(jpeg);
      };
    } catch (e) {
      console.error('[CAMERA] Error:', e);
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
      
      console.log('[UPLOAD] POST /attendance/capture-selfie (check-in)...');
      const res = await fetch('/attendance/capture-selfie', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', 'X-CSRFToken': csrf },
        body: JSON.stringify({ selfie: jpeg, type: 'checkin' })
      });
      
      const d = await res.json();
      console.log('[UPLOAD] Response:', res.status, d);
      
      if (!res.ok || !d.success) {
        console.error('[UPLOAD] Failed:', d.message);
        alert('❌ Upload failed: ' + (d.message || 'Unknown error'));
        return;
      }
      
      console.log('[UPLOAD] Success! Photo ID:', d.photo_id);
      ciReady = true;
      el('ci-photo-badge').className = 'badge bg-success-subtle text-success small';
      el('ci-photo-badge').innerHTML = '<i class="bi bi-check-circle me-1"></i>✓ Captured';
      el('ci-text').textContent = 'Check In Now';
      el('btn-checkin').disabled = false;
      alert('✅ Photo uploaded! Check-In button enabled.');
    } catch (e) {
      console.error('[UPLOAD] Error:', e);
      alert('❌ Upload error: ' + e.message);
    }
  }

  async function uploadCheckOut(jpeg) {
    try {
      const csrf = document.querySelector('meta[name="csrf-token"]')?.getAttribute('content') || '';
      
      console.log('[UPLOAD] POST /attendance/capture-selfie (check-out)...');
      const res = await fetch('/attendance/capture-selfie', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', 'X-CSRFToken': csrf },
        body: JSON.stringify({ selfie: jpeg, type: 'checkout' })
      });
      
      const d = await res.json();
      console.log('[UPLOAD] Response:', res.status, d);
      
      if (!res.ok || !d.success) {
        console.error('[UPLOAD] Failed:', d.message);
        alert('❌ Upload failed: ' + (d.message || 'Unknown error'));
        return;
      }
      
      console.log('[UPLOAD] Success! Photo ID:', d.photo_id);
      coReady = true;
      el('co-photo-badge').className = 'badge bg-success-subtle text-success small';
      el('co-photo-badge').innerHTML = '<i class="bi bi-check-circle me-1"></i>✓ Captured';
      el('co-text').textContent = 'Check Out Now';
      el('btn-checkout').disabled = false;
      alert('✅ Photo uploaded! Check-Out button enabled.');
    } catch (e) {
      console.error('[UPLOAD] Error:', e);
      alert('❌ Upload error: ' + e.message);
    }
  }

  // ──────────────────────────────────────────────────────────────────────────
  // CHECK-IN / CHECK-OUT BUTTONS
  // ──────────────────────────────────────────────────────────────────────────

  el('btn-checkin')?.addEventListener('click', () => {
    if (!ciReady) {
      alert('⚠️ Please upload your selfie first');
      return;
    }
    if (!lastGPS.lat || !lastGPS.lon) {
      alert('⚠️ GPS not available. Please enable location services');
      return;
    }
    
    const csrf = document.querySelector('meta[name="csrf-token"]')?.getAttribute('content') || '';
    const form = new FormData();
    form.append('latitude', lastGPS.lat);
    form.append('longitude', lastGPS.lon);
    form.append('accuracy', lastGPS.acc);
    
    el('btn-checkin').disabled = true;
    el('ci-spin').style.display = 'block';
    
    console.log('[CHECKIN] POST /attendance/checkin with GPS:', lastGPS);
    
    fetch('/attendance/checkin', {
      method: 'POST',
      headers: { 'X-CSRFToken': csrf },
      body: form
    })
    .then(r => r.json())
    .then(d => {
      console.log('[CHECKIN] Response:', d);
      if (d.success) {
        alert('✅ Check-in successful!');
        location.reload();
      } else {
        alert('❌ Check-in failed: ' + d.message);
        el('btn-checkin').disabled = false;
        el('ci-spin').style.display = 'none';
      }
    })
    .catch(e => {
      console.error('[CHECKIN] Error:', e);
      alert('❌ Check-in error: ' + e.message);
      el('btn-checkin').disabled = false;
      el('ci-spin').style.display = 'none';
    });
  });

  el('btn-checkout')?.addEventListener('click', () => {
    if (!coReady) {
      alert('⚠️ Please upload your selfie first');
      return;
    }
    if (!lastGPS.lat || !lastGPS.lon) {
      alert('⚠️ GPS not available. Please enable location services');
      return;
    }
    
    const csrf = document.querySelector('meta[name="csrf-token"]')?.getAttribute('content') || '';
    const form = new FormData();
    form.append('latitude', lastGPS.lat);
    form.append('longitude', lastGPS.lon);
    form.append('accuracy', lastGPS.acc);
    
    el('btn-checkout').disabled = true;
    el('co-spin').style.display = 'block';
    
    console.log('[CHECKOUT] POST /attendance/checkout with GPS:', lastGPS);
    
    fetch('/attendance/checkout', {
      method: 'POST',
      headers: { 'X-CSRFToken': csrf },
      body: form
    })
    .then(r => r.json())
    .then(d => {
      console.log('[CHECKOUT] Response:', d);
      if (d.success) {
        alert('✅ Check-out successful!');
        location.reload();
      } else {
        alert('❌ Check-out failed: ' + d.message);
        el('btn-checkout').disabled = false;
        el('co-spin').style.display = 'none';
      }
    })
    .catch(e => {
      console.error('[CHECKOUT] Error:', e);
      alert('❌ Check-out error: ' + e.message);
      el('btn-checkout').disabled = false;
      el('co-spin').style.display = 'none';
    });
  });

  // ──────────────────────────────────────────────────────────────────────────
  // INIT ON DOM READY
  // ──────────────────────────────────────────────────────────────────────────

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initMap);
  } else {
    initMap();
  }

})();

