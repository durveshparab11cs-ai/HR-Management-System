/**
 * attendance.js — Smart HRMS GPS Attendance
 *
 * Flow:
 *  1. Try GPS via navigator.geolocation
 *  2. If GPS fails/denied → use office coords as fallback for development
 *  3. Buttons are UNLOCKED immediately in dev fallback
 *  4. Server validates coordinates on submit
 */
'use strict';

(function () {

  const OFFICE    = JSON.parse(document.getElementById('office-data')?.textContent || '{}');
  const CI_URL    = '/attendance/checkin';
  const CO_URL    = '/attendance/checkout';
  const PHOTO_URL = '/attendance/upload-photo';
  const R         = 6_371_000;

  let lat = null, lon = null, acc = null, gpsReady = false;
  let map, empMarker;

  function el(id) { return document.getElementById(id); }

  // ── Clock ─────────────────────────────────────────────────────────────
  (function () {
    const c = el('att-clock'), d = el('att-date');
    if (!c) return;
    const tick = () => {
      const n = new Date();
      c.textContent = n.toLocaleTimeString(undefined, { hour:'2-digit', minute:'2-digit', second:'2-digit' });
      if (d) d.textContent = n.toLocaleDateString(undefined, { weekday:'long', year:'numeric', month:'long', day:'numeric' });
    };
    tick(); setInterval(tick, 1000);
  })();

  // ── UTC → IST converter for all .utc-to-ist spans ────────────────
  (function convertUtcToIst() {
    // IST = UTC + 5:30 = UTC + 330 minutes
    document.querySelectorAll('.utc-to-ist').forEach(function(span) {
      const iso = span.textContent.trim();
      if (!iso) return;
      try {
        const d = new Date(iso);
        if (isNaN(d.getTime())) return;
        // Add 5h30m to UTC
        const ist = new Date(d.getTime() + 330 * 60 * 1000);
        const hh  = String(ist.getUTCHours()).padStart(2, '0');
        const mm  = String(ist.getUTCMinutes()).padStart(2, '0');
        span.textContent = `${hh}:${mm}`;
      } catch(e) { /* ignore */ }
    });
  })();
  function initMap() {
    const container = el('att-map');
    if (!container || !OFFICE.lat) return;

    map = L.map('att-map', { zoomControl: true, attributionControl: false });
    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
      maxZoom: 19
    }).addTo(map);

    // Office marker
    L.marker([OFFICE.lat, OFFICE.lon], { icon: mkIcon('#1a3c6e') })
      .addTo(map)
      .bindPopup(`<strong>${OFFICE.name || 'Office'}</strong><br>Geofence: ${OFFICE.radius}m radius`);

    // Geofence circle
    L.circle([OFFICE.lat, OFFICE.lon], {
      radius: OFFICE.radius,
      color: '#1a3c6e',
      fillColor: '#1a3c6e',
      fillOpacity: .08,
      weight: 2,
      dashArray: '6 4'
    }).addTo(map);

    map.setView([OFFICE.lat, OFFICE.lon], 17);

    // Critical: force Leaflet to recalculate container size
    setTimeout(() => map.invalidateSize(), 100);
    setTimeout(() => map.invalidateSize(), 500);
  }

  function mkIcon(color) {
    return L.divIcon({
      html:`<div style="background:${color};width:14px;height:14px;border-radius:50%;border:3px solid #fff;box-shadow:0 2px 8px rgba(0,0,0,.4)"></div>`,
      className:'', iconAnchor:[7,7]
    });
  }

  function updateEmpMarker(empLat, empLon, within) {
    const color = within ? '#10b981' : '#ef4444';
    if (empMarker) empMarker.setLatLng([empLat, empLon]).setIcon(mkIcon(color));
    else empMarker = L.marker([empLat, empLon], { icon:mkIcon(color) }).addTo(map).bindPopup('Your location');
    map.setView([empLat, empLon], 17);
  }

  // ── Haversine ─────────────────────────────────────────────────────────
  function haversine(la1, lo1, la2, lo2) {
    const r = Math.PI/180;
    const a = Math.sin((la2-la1)*r/2)**2 + Math.cos(la1*r)*Math.cos(la2*r)*Math.sin((lo2-lo1)*r/2)**2;
    return R * 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1-a));
  }

  // ── Status ────────────────────────────────────────────────────────────
  function setStatus(state, msg) {
    const dot  = el('gps-dot');
    const text = el('gps-text');
    if (dot) {
      dot.className = 'gps-dot ' + (state === 'ok' ? 'found' : state === 'error' ? 'error' : 'acquiring');
    }
    if (text) {
      text.textContent = msg;
      text.style.color = state === 'ok' ? '#10b981' : state === 'error' ? '#ef4444' : '#f59e0b';
    }
  }

  // ── Buttons ───────────────────────────────────────────────────────────
  function enableButtons() {
    const ci = el('btn-checkin'), co = el('btn-checkout');
    if (ci && (typeof CAN_CHECKIN==='undefined'||CAN_CHECKIN)) {
      ci.disabled = false;
      const t=el('ci-text'); if(t) t.textContent='Check In';
      const i=el('ci-icon'); if(i) i.className='bi bi-box-arrow-in-right';
    }
    if (co && (typeof CAN_CHECKOUT==='undefined'||CAN_CHECKOUT)) {
      co.disabled = false;
      const t=el('co-text'); if(t) t.textContent='Check Out';
      const i=el('co-icon'); if(i) i.className='bi bi-box-arrow-right';
    }
  }

  function disableButtons(msg) {
    ['btn-checkin','btn-checkout'].forEach(id => {
      const b = el(id); if (!b) return;
      b.disabled = true;
      const t = el(id==='btn-checkin'?'ci-text':'co-text'); if(t) t.textContent = msg;
    });
  }

  // ── GPS success handler ───────────────────────────────────────────────
  function onGPSSuccess(pos) {
    lat = pos.coords.latitude;
    lon = pos.coords.longitude;
    acc = pos.coords.accuracy;
    gpsReady = true;

    const dist   = haversine(lat, lon, OFFICE.lat, OFFICE.lon);
    const within = dist <= OFFICE.radius;

    if (map) updateEmpMarker(lat, lon, within);
    enableButtons();

    setStatus(within ? 'ok' : 'error',
      within
        ? `✓ Inside office zone — ${dist.toFixed(0)}m from office (±${Math.round(acc)}m accuracy)`
        : `✗ Outside office zone — ${dist.toFixed(0)}m from office (limit: ${OFFICE.radius}m)`
    );

    const coordsEl = el('gps-coords');
    if (coordsEl) coordsEl.style.display = '';
    const ct = el('coords-text');
    if (ct) ct.textContent = `${lat.toFixed(6)}, ${lon.toFixed(6)} (±${Math.round(acc)}m)`;
    const dt = el('distance-text');
    if (dt) { dt.textContent = `${dist.toFixed(0)}m from office`; dt.style.color = within ? '#10b981' : '#ef4444'; }
  }

  // ── GPS init ──────────────────────────────────────────────────────────
  function startGPS() {
    setStatus('acquiring', 'Requesting GPS… please allow location if prompted.');

    if (!navigator.geolocation) {
      useFallback('Geolocation not supported by this browser.');
      return;
    }

    if (navigator.permissions) {
      navigator.permissions.query({ name: 'geolocation' }).then(result => {
        if (result.state === 'denied') {
          useFallback('Location permission denied. Please enable it in browser settings.');
        } else {
          // 'granted' or 'prompt'
          // Enable buttons with fallback immediately so UI is never blocked
          useFallback('');
          // Then try to get real GPS in background
          requestGPS();
        }
      }).catch(() => {
        useFallback('');
        requestGPS();
      });
    } else {
      useFallback('');
      requestGPS();
    }
  }

  function requestGPS() {
    // Try high accuracy first (GPS chip), then fall back to network location
    let attempts = 0;

    function tryGPS(highAccuracy) {
      attempts++;
      navigator.geolocation.getCurrentPosition(
        onGPSSuccess,
        (err) => {
          if (err.code === 1) {
            // Permission denied — use fallback
            useFallback('Location permission denied. Check browser site settings.');
          } else if (highAccuracy && attempts <= 2) {
            // High accuracy failed — retry with low accuracy
            setStatus('acquiring', 'High accuracy GPS not available, trying network location…');
            setTimeout(() => tryGPS(false), 1000);
          } else {
            // All attempts failed — start watchPosition as last resort
            setStatus('acquiring', 'GPS timeout — trying continuous location watch…');
            let watchId = navigator.geolocation.watchPosition(
              (pos) => {
                navigator.geolocation.clearWatch(watchId);
                onGPSSuccess(pos);
              },
              () => useFallback('Could not acquire GPS. Using office location as fallback.'),
              { enableHighAccuracy: false, timeout: 20000, maximumAge: 60000 }
            );
            // Stop watching after 30s regardless
            setTimeout(() => {
              navigator.geolocation.clearWatch(watchId);
              if (!gpsReady) useFallback('GPS timed out. Using office location as fallback.');
            }, 30000);
          }
        },
        {
          enableHighAccuracy: highAccuracy,
          timeout: highAccuracy ? 10000 : 15000,
          maximumAge: highAccuracy ? 0 : 30000  // no cache for high accuracy
        }
      );
    }

    tryGPS(true);
  }

  function useFallback(reason) {
    if (OFFICE.lat) {
      lat = OFFICE.lat;
      lon = OFFICE.lon;
      acc = 9999;
      gpsReady = true;
      enableButtons();
      if (reason) {
        setStatus('acquiring',
          `⚠ ${reason} Using office location as estimate.`
        );
      } else {
        setStatus('acquiring', 'Locating… buttons enabled. GPS updating in background.');
      }
      if (map) updateEmpMarker(lat, lon, true);
    } else {
      if (reason) setStatus('error', reason);
      enableButtons(); // Enable anyway — server will validate
    }
  }

  // ── Submit attendance ─────────────────────────────────────────────────
  async function submitAttendance(url, type) {
    if (!gpsReady || lat === null) {
      showToast('Location not ready. Please wait…', 'warn');
      return;
    }
    setLoading(type, true);
    const fd = new FormData();
    fd.append('latitude',  lat);
    fd.append('longitude', lon);
    fd.append('accuracy',  acc || '');
    try {
      const res  = await fetch(url, {
        method:'POST',
        headers:{ 'X-CSRFToken': CSRF_TOKEN, 'X-Requested-With': 'XMLHttpRequest' },
        body: fd,
      });
      const data = await res.json();
      if (data.success) {
        // Convert returned UTC time to IST for display
        let displayTime = data.time || '';
        if (displayTime) {
          try {
            const today = new Date().toISOString().split('T')[0];
            const utcDt = new Date(`${today}T${displayTime}:00Z`);
            const istDt = new Date(utcDt.getTime() + 330 * 60 * 1000);
            const hh = String(istDt.getUTCHours()).padStart(2,'0');
            const mm = String(istDt.getUTCMinutes()).padStart(2,'0');
            displayTime = `${hh}:${mm} IST`;
          } catch(e) { displayTime = data.time; }
        }
        const msg = data.message
          ? data.message.replace(/\d{2}:\d{2}\s*(UTC)?/g, displayTime)
          : `Done at ${displayTime}`;
        showToast(msg, 'success');
        setTimeout(() => location.reload(), 1800);
      } else {
        showToast(data.message, 'error');
        if (data.gps && !data.gps.within_radius) {
          const rb = el('rejection-box');
          if (rb) {
            rb.style.display = '';
            const d = (data.gps.distance_metres||0).toFixed(0);
            const a = data.gps.allowed_radius || OFFICE.radius;
            el('rj-emp-dist')?.textContent && (el('rj-emp-dist').textContent = `${d} m`);
            el('rj-allowed')?.textContent  && (el('rj-allowed').textContent  = `${a} m`);
            el('rj-move-by')?.textContent  && (el('rj-move-by').textContent  = `${Math.max(0, d-a).toFixed(0)} m closer`);
          }
        }
        setLoading(type, false);
      }
    } catch {
      showToast('Network error. Check your connection.', 'error');
      setLoading(type, false);
    }
  }

  function setLoading(type, on) {
    const isCI = type === 'in';
    const btn  = el(isCI ? 'btn-checkin' : 'btn-checkout');
    const spin = el(isCI ? 'ci-spin'     : 'co-spin');
    const icon = el(isCI ? 'ci-icon'     : 'co-icon');
    const txt  = el(isCI ? 'ci-text'     : 'co-text');
    if (btn)  btn.disabled       = on;
    if (spin) spin.style.display = on ? 'block' : 'none';
    if (icon) icon.style.display = on ? 'none'  : '';
    if (txt)  txt.textContent    = on ? 'Processing…' : (isCI ? 'Check In' : 'Check Out');
  }

  // ── Photo upload ──────────────────────────────────────────────────────
  function initPhotoUpload() {
    // Photo upload is always available — not gated by CAN_PHOTO flag
    const zone      = el('photo-zone');
    const photoInp  = el('photo-input');
    const btnUpload = el('btn-upload-photo');
    const previewEl = el('photo-preview-img');
    const photoSpin = el('photo-spin');
    const photoTxt  = el('photo-txt');
    if (!zone || !photoInp) return;  // Not rendered (already uploaded)
    zone.addEventListener('click', () => photoInp.click());
    zone.addEventListener('dragover', e=>{e.preventDefault();zone.classList.add('drag-over');});
    zone.addEventListener('dragleave', ()=>zone.classList.remove('drag-over'));
    zone.addEventListener('drop', e=>{e.preventDefault();zone.classList.remove('drag-over');if(e.dataTransfer.files[0])handleFile(e.dataTransfer.files[0]);});
    photoInp.addEventListener('change', ()=>{if(photoInp.files[0])handleFile(photoInp.files[0]);});

    function handleFile(f) {
      if(!['image/jpeg','image/png','image/webp'].includes(f.type)){showToast('Only JPG, PNG, WEBP.','error');return;}
      if(f.size>5*1024*1024){showToast('Max 5 MB.','error');return;}
      const r=new FileReader();
      r.onload=e=>{
        if(previewEl){previewEl.src=e.target.result;previewEl.style.display='block';}
      };
      r.readAsDataURL(f);
      if(btnUpload) btnUpload.style.display='';
    }

    btnUpload?.addEventListener('click', async()=>{
      const f=photoInp.files[0];
      if(!f){showToast('Select a photo first.','warn');return;}
      btnUpload.disabled=true;
      if(photoSpin) photoSpin.style.display='inline-block';
      if(photoTxt)  photoTxt.textContent='Uploading…';
      const fd=new FormData(); fd.append('photo',f);
      try{
        const res=await fetch(PHOTO_URL,{method:'POST',headers:{'X-CSRFToken':CSRF_TOKEN,'X-Requested-With':'XMLHttpRequest'},body:fd});
        const d=await res.json();
        if(d.success){
          showToast('Photo uploaded successfully.','success');
          setTimeout(()=>location.reload(),1500);
        } else {
          showToast(d.message||'Upload failed.','error');
          btnUpload.disabled=false;
          if(photoSpin) photoSpin.style.display='none';
          if(photoTxt)  photoTxt.textContent='Upload Photo';
        }
      }catch{
        showToast('Upload error. Please try again.','error');
        btnUpload.disabled=false;
        if(photoSpin) photoSpin.style.display='none';
        if(photoTxt)  photoTxt.textContent='Upload Photo';
      }
    });
  }

  // ── Toast ─────────────────────────────────────────────────────────────
  function showToast(msg, type) {
    // Support both possible container IDs
    const c = el('att-toast-container') || el('att-toasts');
    if (!c) {
      // fallback — append to body
      const d = document.createElement('div');
      d.style.cssText = 'position:fixed;top:80px;right:24px;z-index:9999;min-width:300px';
      d.id = 'att-toast-container';
      document.body.appendChild(d);
      return showToast(msg, type);
    }
    const icons = { success: '✅', error: '❌', warn: '⚠️' };
    const t = document.createElement('div');
    t.className = `att-toast${type === 'error' ? ' error' : type === 'warn' ? ' warn' : ''}`;
    t.innerHTML = `<span class="att-toast-icon">${icons[type] || 'ℹ️'}</span><div>${msg}</div><button class="att-toast-close" onclick="this.parentElement.remove()">✕</button>`;
    c.appendChild(t);
    setTimeout(() => { if (t.parentElement) t.remove(); }, 6000);
  }

  // ── Boot ──────────────────────────────────────────────────────────────
  el('btn-checkin')?.addEventListener('click', () => submitAttendance(CI_URL, 'in'));
  el('btn-checkout')?.addEventListener('click', () => submitAttendance(CO_URL, 'out'));

  initMap();
  startGPS();
  initPhotoUpload();

})();
