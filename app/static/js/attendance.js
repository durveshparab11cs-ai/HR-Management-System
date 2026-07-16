/**
 * attendance.js — Smart HRMS GPS Attendance
 * Complete rewrite: live Leaflet map, 10s auto-refresh, accuracy circle,
 * coord info panel, refresh button, full error handling.
 */
'use strict';

(function () {

  /* ── Constants ──────────────────────────────────────────────────── */
  const OFFICE    = JSON.parse(document.getElementById('office-data')?.textContent || '{}');
  const CI_URL    = '/attendance/checkin';
  const CO_URL    = '/attendance/checkout';
  const PHOTO_URL = '/attendance/upload-photo';
  const R         = 6_371_000;
  // Generous timeouts — Chromium on HTTPS can be slow to get first fix
  const GPS_OPTS_HI  = { enableHighAccuracy: true,  timeout: 30000, maximumAge: 0 };
  const GPS_OPTS_LO  = { enableHighAccuracy: false, timeout: 30000, maximumAge: 60000 };

  /* ── State ──────────────────────────────────────────────────────── */
  let lat = null, lon = null, acc = null, gpsReady = false;
  let map = null, empMarker = null, accCircle = null;
  let officeMarker = null, officeCircle = null;
  let autoRefreshTimer = null;
  let isRefreshing = false;

  function el(id) { return document.getElementById(id); }


  /* ── Clock ──────────────────────────────────────────────────────── */
  (function () {
    const c = el('att-clock'), d = el('att-date');
    if (!c) return;
    const tick = () => {
      const n = new Date();
      c.textContent = n.toLocaleTimeString(undefined, { hour: '2-digit', minute: '2-digit', second: '2-digit' });
      if (d) d.textContent = n.toLocaleDateString(undefined, { weekday: 'long', year: 'numeric', month: 'long', day: 'numeric' });
    };
    tick(); setInterval(tick, 1000);
  })();

  /* ── UTC → IST converter ──────────────────────────────────────── */
  (function convertUtcToIst() {
    document.querySelectorAll('.utc-to-ist').forEach(function (span) {
      const iso = span.textContent.trim();
      if (!iso) return;
      try {
        const d = new Date(iso);
        if (isNaN(d.getTime())) return;
        const ist = new Date(d.getTime() + 330 * 60 * 1000);
        span.textContent = String(ist.getUTCHours()).padStart(2, '0') + ':' + String(ist.getUTCMinutes()).padStart(2, '0');
      } catch (e) { /* ignore */ }
    });
  })();

  /* ── Map icon factory ───────────────────────────────────────────── */
  function mkIcon(color, size) {
    size = size || 14;
    return L.divIcon({
      html: `<div style="background:${color};width:${size}px;height:${size}px;border-radius:50%;border:3px solid #fff;box-shadow:0 2px 10px rgba(0,0,0,.45)"></div>`,
      className: '', iconAnchor: [size / 2, size / 2]
    });
  }


  /* ── Haversine distance ──────────────────────────────────────────── */
  function haversine(la1, lo1, la2, lo2) {
    const r = Math.PI / 180;
    const a = Math.sin((la2 - la1) * r / 2) ** 2 +
              Math.cos(la1 * r) * Math.cos(la2 * r) * Math.sin((lo2 - lo1) * r / 2) ** 2;
    return R * 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a));
  }

  /* ── Status bar ─────────────────────────────────────────────────── */
  function setGpsStatus(state, msg) {
    // Works with both dashboard.html (gps-indicator) and old index.html (gps-dot)
    const dot  = el('gps-dot') || el('gps-indicator');
    const text = el('gps-text');
    if (dot) {
      // Remove all state classes then add the right one
      dot.classList.remove('acquiring', 'ok', 'found', 'error');
      dot.classList.add(state === 'ok' ? 'ok' : state === 'error' ? 'error' : 'acquiring');
      // Also set the class name for gps-indicator elements in dashboard.html
      if (dot.id === 'gps-dot' && !dot.classList.contains('gps-dot')) {
        dot.className = 'gps-indicator ' + (state === 'ok' ? 'ok' : state === 'error' ? 'error' : 'acquiring');
      }
    }
    if (text) {
      text.textContent = msg;
      text.style.color = state === 'ok' ? '#10b981' : state === 'error' ? '#ef4444' : '#f59e0b';
    }
  }

  /* ── Map init ───────────────────────────────────────────────────── */
  function initMap() {
    const container = el('att-map');
    if (!container) return;
    if (typeof L === 'undefined') return; // Leaflet not loaded

    // Guard against double-init
    if (map) return;

    // Ensure container has explicit dimensions before Leaflet touches it
    container.style.height  = '350px';
    container.style.width   = '100%';
    container.style.display = 'block';

    map = L.map('att-map', { zoomControl: true, attributionControl: true });

    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
      maxZoom: 19,
      attribution: '© <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>'
    }).addTo(map);

    const oLat = OFFICE.lat || 19.014903;
    const oLon = OFFICE.lon || 72.845183;
    const oRad = OFFICE.radius || 100;

    // Office marker
    officeMarker = L.marker([oLat, oLon], { icon: mkIcon('#1a3c6e', 16) })
      .addTo(map)
      .bindPopup(`<strong>${OFFICE.name || 'Office'}</strong><br>Geofence: ${oRad}m`);

    // Office geofence circle (dashed)
    officeCircle = L.circle([oLat, oLon], {
      radius: oRad, color: '#1a3c6e', fillColor: '#1a3c6e',
      fillOpacity: 0.07, weight: 2, dashArray: '6 4'
    }).addTo(map);

    map.setView([oLat, oLon], 17);

    // Force size recalc — critical for maps inside flex/card containers
    setTimeout(() => map && map.invalidateSize(), 100);
    setTimeout(() => map && map.invalidateSize(), 500);
    setTimeout(() => map && map.invalidateSize(), 1500);
  }


  /* ── Update employee marker + accuracy circle ───────────────────── */
  function updateMapLocation(empLat, empLon, empAcc, within) {
    if (!map) return;

    const color = within ? '#10b981' : '#ef4444';

    // Employee position marker
    if (empMarker) {
      empMarker.setLatLng([empLat, empLon]).setIcon(mkIcon(color, 14));
    } else {
      empMarker = L.marker([empLat, empLon], { icon: mkIcon(color, 14) })
        .addTo(map)
        .bindPopup('<strong>Your Location</strong>');
    }

    // Accuracy circle (blue, semi-transparent)
    if (accCircle) {
      accCircle.setLatLng([empLat, empLon]).setRadius(empAcc);
    } else {
      accCircle = L.circle([empLat, empLon], {
        radius: empAcc, color: '#3b82f6', fillColor: '#3b82f6',
        fillOpacity: 0.1, weight: 1.5
      }).addTo(map);
    }

    // Pan map to employee location, keep zoom at 17
    map.setView([empLat, empLon], 17);
    map.invalidateSize();
  }

  /* ── Info panel below map ───────────────────────────────────────── */
  function updateInfoPanel(empLat, empLon, empAcc, dist, within) {
    // gps-coords panel (both templates)
    const coordsEl = el('gps-coords');
    if (coordsEl) coordsEl.style.display = '';

    // dashboard.html uses gps-latlon / gps-dist-text
    const ll = el('gps-latlon');
    if (ll) ll.textContent = `${empLat.toFixed(6)}, ${empLon.toFixed(6)}`;

    const dt = el('gps-dist-text');
    if (dt) { dt.textContent = `${dist.toFixed(0)}m`; dt.style.color = within ? '#10b981' : '#ef4444'; }

    const ab = el('gps-accuracy-label');
    if (ab) ab.textContent = `±${Math.round(empAcc)}m accuracy`;

    const badge = el('gps-dist-badge');
    if (badge) badge.innerHTML = `<span class="dist-badge ${within ? 'inside' : 'outside'}">${dist.toFixed(0)}m ${within ? '✓' : '✗'}</span>`;

    // index.html uses coords-text / distance-text
    const ct = el('coords-text');
    if (ct) ct.textContent = `${empLat.toFixed(6)}, ${empLon.toFixed(6)} (±${Math.round(empAcc)}m)`;
    const dtt = el('distance-text');
    if (dtt) { dtt.textContent = `${dist.toFixed(0)}m from office`; dtt.style.color = within ? '#10b981' : '#ef4444'; }

    // Full info card (new panel injected by this script)
    updateGpsInfoCard(empLat, empLon, empAcc, dist, within);

    // Rejection box (outside zone)
    const rb = el('rejection-box');
    if (rb) {
      if (!within) {
        rb.style.display = '';
        const re = el('rj-emp-dist'); if (re) re.textContent = `${dist.toFixed(0)} m`;
        const ra = el('rj-allowed');  if (ra) ra.textContent = `${OFFICE.radius} m`;
        const rm = el('rj-move-by');  if (rm) rm.textContent = `${Math.max(0, dist - OFFICE.radius).toFixed(0)} m closer`;
      } else {
        rb.style.display = 'none';
      }
    }
  }


  /* ── GPS info card (injected below map) ────────────────────────── */
  function ensureInfoCard() {
    if (el('gps-info-card')) return;
    const mapEl = el('att-map');
    if (!mapEl) return;

    const card = document.createElement('div');
    card.id = 'gps-info-card';
    card.style.cssText = 'background:#f8fafc;border-radius:12px;padding:14px 18px;margin-top:12px;font-size:.82rem;border:1px solid #e2e8f0';
    card.innerHTML = `
      <div style="display:grid;grid-template-columns:repeat(auto-fit,minmax(140px,1fr));gap:10px">
        <div><div style="color:#64748b;font-size:.7rem;text-transform:uppercase;letter-spacing:.05em;margin-bottom:3px">Latitude</div><div style="font-weight:700;color:#0f172a" id="info-lat">—</div></div>
        <div><div style="color:#64748b;font-size:.7rem;text-transform:uppercase;letter-spacing:.05em;margin-bottom:3px">Longitude</div><div style="font-weight:700;color:#0f172a" id="info-lon">—</div></div>
        <div><div style="color:#64748b;font-size:.7rem;text-transform:uppercase;letter-spacing:.05em;margin-bottom:3px">Accuracy</div><div style="font-weight:700;color:#0f172a" id="info-acc">—</div></div>
        <div><div style="color:#64748b;font-size:.7rem;text-transform:uppercase;letter-spacing:.05em;margin-bottom:3px">GPS Status</div><div style="font-weight:700" id="info-status">—</div></div>
        <div><div style="color:#64748b;font-size:.7rem;text-transform:uppercase;letter-spacing:.05em;margin-bottom:3px">Last Updated</div><div style="font-weight:700;color:#0f172a" id="info-time">—</div></div>
      </div>
      <div style="margin-top:12px">
        <button id="btn-refresh-gps" style="background:#1a3c6e;color:#fff;border:none;border-radius:8px;padding:7px 18px;font-size:.8rem;font-weight:600;cursor:pointer;display:inline-flex;align-items:center;gap:7px">
          <i class="bi bi-arrow-clockwise"></i> Refresh Location
        </button>
      </div>`;

    mapEl.insertAdjacentElement('afterend', card);

    el('btn-refresh-gps')?.addEventListener('click', function () {
      if (isRefreshing) return;
      isRefreshing = true;
      this.disabled = true;
      this.innerHTML = '<i class="bi bi-arrow-clockwise" style="animation:spin .65s linear infinite"></i> Refreshing…';
      fetchGPS(true);
    });
  }

  function updateGpsInfoCard(empLat, empLon, empAcc, dist, within) {
    ensureInfoCard();
    const li = el('info-lat');   if (li) li.textContent = empLat.toFixed(7);
    const lo = el('info-lon');   if (lo) lo.textContent = empLon.toFixed(7);
    const la = el('info-acc');   if (la) la.textContent = `±${Math.round(empAcc)} m`;
    const ls = el('info-status');
    if (ls) {
      ls.textContent = within ? '✓ Inside office zone' : '✗ Outside office zone';
      ls.style.color = within ? '#10b981' : '#ef4444';
    }
    const lt = el('info-time');  if (lt) lt.textContent = new Date().toLocaleTimeString();

    // Reset refresh button
    const rb = el('btn-refresh-gps');
    if (rb) { rb.disabled = false; rb.innerHTML = '<i class="bi bi-arrow-clockwise"></i> Refresh Location'; }
    isRefreshing = false;
  }


  /* ── Button enable/disable ──────────────────────────────────────── */
  function enableButtons() {
    const ci = el('btn-checkin');
    const co = el('btn-checkout');
    if (ci && (typeof CAN_CHECKIN === 'undefined' || CAN_CHECKIN)) {
      ci.disabled = false;
      const t = el('ci-text'); if (t) t.textContent = 'Check In';
      const i = el('ci-icon'); if (i) i.className = 'bi bi-box-arrow-in-right';
    }
    if (co && (typeof CAN_CHECKOUT === 'undefined' || CAN_CHECKOUT)) {
      co.disabled = false;
      const t = el('co-text'); if (t) t.textContent = 'Check Out';
      const i = el('co-icon'); if (i) i.className = 'bi bi-box-arrow-right';
    }
  }

  /* ── GPS success handler ────────────────────────────────────────── */
  function onGPSSuccess(pos) {
    lat = pos.coords.latitude;
    lon = pos.coords.longitude;
    acc = pos.coords.accuracy;
    gpsReady = true;
    _permRetries = 0; // reset retry counter

    const oLat   = OFFICE.lat || 19.014903;
    const oLon   = OFFICE.lon || 72.845183;
    const oRad   = OFFICE.radius || 100;
    const dist   = haversine(lat, lon, oLat, oLon);
    const within = dist <= oRad;

    updateMapLocation(lat, lon, acc, within);
    updateInfoPanel(lat, lon, acc, dist, within);
    enableButtons();

    // Status message with exact distance so users can verify the 50/100m boundary
    const distText = dist < 1000
      ? dist.toFixed(1) + 'm'
      : (dist / 1000).toFixed(2) + 'km';
    const accText  = Math.round(acc) + 'm';

    if (within) {
      setGpsStatus('ok',
        `✓ GPS Verified — ${distText} from office (±${accText} accuracy)`
      );
    } else {
      const moveBy = Math.max(0, dist - oRad).toFixed(0);
      setGpsStatus('error',
        `✗ Outside zone — ${distText} from office, need to be within ${oRad}m (move ${moveBy}m closer)`
      );
    }
  }

  /* ── GPS error handler ──────────────────────────────────────────── */
  let _permRetries = 0;

  function onGPSError(err, fallback) {
    // Never handle errors if GPS already succeeded
    if (gpsReady) return;

    // Timeout (code 3) — retry silently, this is normal on first load
    if (err.code === 3) {
      _permRetries++;
      if (_permRetries <= 5) {
        setGpsStatus('acquiring', 'Getting location… (' + _permRetries + '/5)');
        setTimeout(function () {
          if (!gpsReady) fetchGPS(false);
        }, 2000);
        return;
      }
      // After 5 timeouts, enable buttons and show soft message
      setGpsStatus('acquiring', 'GPS slow to respond — buttons enabled. Location still loading…');
      useFallback();
      return;
    }

    // PERMISSION_DENIED (code 1) — Chromium bug: retry up to 3x before showing error
    if (err.code === 1 && _permRetries < 3) {
      _permRetries++;
      setGpsStatus('acquiring', 'Retrying GPS (' + _permRetries + '/3)…');
      setTimeout(function () {
        if (!gpsReady) fetchGPS(false);
      }, 1500 * _permRetries);
      return;
    }

    // Real permission denied or position unavailable
    let msg;
    switch (err.code) {
      case 1:
        msg = 'Location access denied. Click the lock icon → Location → Allow, then reload.';
        break;
      case 2:
        msg = 'Position unavailable. Enable device location services and reload.';
        break;
      default:
        msg = 'GPS error. Please reload the page.';
    }

    setGpsStatus('error', msg);
    useFallback();
    isRefreshing = false;

    const rb = el('btn-refresh-gps');
    if (rb) {
      rb.disabled = false;
      rb.innerHTML = '<i class="bi bi-arrow-clockwise"></i> Refresh Location';
    }
  }

  /* ── Fetch GPS position ─────────────────────────────────────────── */
  let _watchId = null;

  function fetchGPS(isManual) {
    if (!navigator.geolocation) {
      setGpsStatus('error', 'Geolocation not supported by this browser.');
      useFallback();
      return;
    }

    if (isManual) {
      setGpsStatus('acquiring', 'Refreshing location…');
    }

    // Cancel any existing watch
    if (_watchId !== null) {
      navigator.geolocation.clearWatch(_watchId);
      _watchId = null;
    }

    // Use watchPosition — bypasses Chromium's permission state race condition
    // No safety timeout — let it keep trying until it succeeds
    _watchId = navigator.geolocation.watchPosition(
      function (pos) {
        // Got a fix — stop watching (we have position)
        if (_watchId !== null) {
          navigator.geolocation.clearWatch(_watchId);
          _watchId = null;
        }
        onGPSSuccess(pos);
      },
      function (err) {
        // Only treat as error if GPS hasn't already succeeded
        if (!gpsReady) {
          onGPSError(err, true);
        }
      },
      { enableHighAccuracy: true, timeout: 30000, maximumAge: 0 }
    );
  }

  /* ── Fallback: use office coords (buttons-only, doesn't block real GPS) ── */
  function useFallback() {
    // Enable buttons with office coords so UI isn't blocked
    // but do NOT set gpsReady=true so real GPS can still succeed
    if (OFFICE.lat && !gpsReady) {
      lat = OFFICE.lat; lon = OFFICE.lon; acc = 9999;
      updateMapLocation(lat, lon, 9999, true);
    }
    enableButtons();
  }


  /* ── Submit attendance ──────────────────────────────────────────── */
  async function submitAttendance(url, type) {
    if (!gpsReady || lat === null) {
      showToast('Location not ready. Please wait for GPS…', 'warn');
      return;
    }
    setLoading(type, true);
    const fd = new FormData();
    fd.append('latitude',  lat);
    fd.append('longitude', lon);
    fd.append('accuracy',  acc || 0);
    fd.append('timestamp', new Date().toISOString());
    try {
      const res  = await fetch(url, {
        method: 'POST',
        headers: { 'X-CSRFToken': CSRF_TOKEN, 'X-Requested-With': 'XMLHttpRequest' },
        body: fd,
      });
      const data = await res.json();
      if (data.success) {
        let displayTime = data.time || '';
        if (displayTime) {
          try {
            const today = new Date().toISOString().split('T')[0];
            const utcDt = new Date(`${today}T${displayTime}:00Z`);
            const istDt = new Date(utcDt.getTime() + 330 * 60 * 1000);
            displayTime = String(istDt.getUTCHours()).padStart(2,'0') + ':' + String(istDt.getUTCMinutes()).padStart(2,'0') + ' IST';
          } catch (e) { /* use raw time */ }
        }
        const msg = data.message || `Done at ${displayTime}`;
        showToast(msg, 'success');
        setTimeout(() => location.reload(), 1800);
      } else {
        showToast(data.message || 'Action failed.', 'error');
        if (data.gps && !data.gps.within_radius) {
          const rb = el('rejection-box');
          if (rb) {
            rb.style.display = '';
            const d = (data.gps.distance_metres || 0).toFixed(0);
            const a = data.gps.allowed_radius || OFFICE.radius;
            const re = el('rj-emp-dist'); if (re) re.textContent = `${d} m`;
            const ra = el('rj-allowed');  if (ra) ra.textContent = `${a} m`;
            const rm = el('rj-move-by');  if (rm) rm.textContent = `${Math.max(0, d - a).toFixed(0)} m closer`;
          }
        }
        setLoading(type, false);
      }
    } catch (e) {
      showToast('Network error. Check your connection.', 'error');
      setLoading(type, false);
    }
  }

  /* ── Loading state ──────────────────────────────────────────────── */
  function setLoading(type, on) {
    const isCI = type === 'in';
    const btn  = el(isCI ? 'btn-checkin'  : 'btn-checkout');
    const spin = el(isCI ? 'ci-spin'      : 'co-spin');
    const icon = el(isCI ? 'ci-icon'      : 'co-icon');
    const txt  = el(isCI ? 'ci-text'      : 'co-text');
    if (btn)  btn.disabled       = on;
    if (spin) spin.style.display = on ? 'block' : 'none';
    if (icon) icon.style.display = on ? 'none'  : '';
    if (txt)  txt.textContent    = on ? 'Processing…' : (isCI ? 'Check In' : 'Check Out');
  }


  /* ── Photo upload ───────────────────────────────────────────────── */
  function initPhotoUpload() {
    const zone      = el('photo-zone');
    const photoInp  = el('photo-input');
    const btnUpload = el('btn-upload-photo');
    const previewEl = el('photo-preview-img');
    const photoSpin = el('photo-spin');
    const photoTxt  = el('photo-txt');
    if (!zone || !photoInp) return;

    zone.addEventListener('click', () => photoInp.click());
    zone.addEventListener('dragover', e => { e.preventDefault(); zone.classList.add('drag-over'); });
    zone.addEventListener('dragleave', () => zone.classList.remove('drag-over'));
    zone.addEventListener('drop', e => {
      e.preventDefault(); zone.classList.remove('drag-over');
      if (e.dataTransfer.files[0]) handleFile(e.dataTransfer.files[0]);
    });
    photoInp.addEventListener('change', () => { if (photoInp.files[0]) handleFile(photoInp.files[0]); });

    function handleFile(f) {
      if (!['image/jpeg', 'image/png', 'image/webp'].includes(f.type)) { showToast('Only JPG, PNG, WEBP.', 'error'); return; }
      if (f.size > 5 * 1024 * 1024) { showToast('Max 5 MB.', 'error'); return; }
      const r = new FileReader();
      r.onload = e => { if (previewEl) { previewEl.src = e.target.result; previewEl.style.display = 'block'; } };
      r.readAsDataURL(f);
      if (btnUpload) btnUpload.style.display = '';
    }

    btnUpload?.addEventListener('click', async () => {
      const f = photoInp.files[0];
      if (!f) { showToast('Select a photo first.', 'warn'); return; }
      btnUpload.disabled = true;
      if (photoSpin) photoSpin.style.display = 'inline-block';
      if (photoTxt)  photoTxt.textContent = 'Uploading…';
      const fd = new FormData(); fd.append('photo', f);
      try {
        const res = await fetch(PHOTO_URL, { method: 'POST', headers: { 'X-CSRFToken': CSRF_TOKEN, 'X-Requested-With': 'XMLHttpRequest' }, body: fd });
        const d = await res.json();
        if (d.success) { showToast('Photo uploaded.', 'success'); setTimeout(() => location.reload(), 1500); }
        else { showToast(d.message || 'Upload failed.', 'error'); btnUpload.disabled = false; if (photoSpin) photoSpin.style.display = 'none'; if (photoTxt) photoTxt.textContent = 'Upload Photo'; }
      } catch { showToast('Upload error.', 'error'); btnUpload.disabled = false; if (photoSpin) photoSpin.style.display = 'none'; if (photoTxt) photoTxt.textContent = 'Upload Photo'; }
    });
  }

  /* ── Toast ──────────────────────────────────────────────────────── */
  function showToast(msg, type) {
    let c = el('att-toasts') || el('att-toast-container');
    if (!c) {
      c = document.createElement('div');
      c.id = 'att-toasts';
      c.style.cssText = 'position:fixed;top:80px;right:24px;z-index:9999;display:flex;flex-direction:column;gap:10px;min-width:300px';
      document.body.appendChild(c);
    }
    const icons = { success: '✅', error: '❌', warn: '⚠️' };
    const t = document.createElement('div');
    t.className = `att-toast${type === 'error' ? ' error' : type === 'warn' ? ' warn' : ''}`;
    t.innerHTML = `<span class="att-toast-icon">${icons[type] || 'ℹ️'}</span><div class="att-toast-body">${msg}</div><button class="att-toast-close" onclick="this.parentElement.remove()">✕</button>`;
    c.appendChild(t);
    setTimeout(() => { if (t.parentElement) t.remove(); }, 6000);
  }

  /* ── Auto-refresh every 10 seconds ─────────────────────────────── */
  function startAutoRefresh() {
    if (autoRefreshTimer) clearInterval(autoRefreshTimer);
    autoRefreshTimer = setInterval(() => {
      if (!isRefreshing && document.visibilityState === 'visible') {
        fetchGPS(false);
      }
    }, 10000);
  }

  /* ── Boot ───────────────────────────────────────────────────────── */
  // Wire buttons
  el('btn-checkin')?.addEventListener('click',  () => submitAttendance(CI_URL, 'in'));
  el('btn-checkout')?.addEventListener('click', () => submitAttendance(CO_URL, 'out'));

  function startGPS() {
    if (!navigator.geolocation) {
      setGpsStatus('error', 'Geolocation not supported by this browser.');
      useFallback();
      return;
    }

    // Enable buttons immediately with office coords — never block the UI
    // Real GPS will update the marker and status when it resolves
    useFallback();
    setGpsStatus('acquiring', 'Loading GPS…');

    // Call GPS directly — never pre-check permissions (Chromium bug)
    fetchGPS(false);

    // Advisory: watch for permission changes only
    if (navigator.permissions) {
      navigator.permissions.query({ name: 'geolocation' }).then(function (perm) {
        perm.onchange = function () {
          if (perm.state === 'granted' && !gpsReady) {
            _permRetries = 0;
            setGpsStatus('acquiring', 'Permission granted — getting location…');
            fetchGPS(false);
          } else if (perm.state === 'denied' && !gpsReady) {
            setGpsStatus('error', 'Location access denied. Click the lock icon → Allow → reload.');
          }
        };
      }).catch(function () {});
    }
  }

  // Check if Leaflet is loaded; if not inject it dynamically then init
  function bootWhenLeafletReady() {
    initMap();
    startGPS();
    startAutoRefresh();
    initPhotoUpload();
  }

  if (typeof L !== 'undefined') {
    // Leaflet already loaded via <script> tag in template
    if (document.readyState === 'loading') {
      document.addEventListener('DOMContentLoaded', bootWhenLeafletReady);
    } else {
      bootWhenLeafletReady();
    }
  } else {
    // Dynamically inject Leaflet CSS + JS then boot
    const link = document.createElement('link');
    link.rel = 'stylesheet'; link.href = 'https://unpkg.com/leaflet@1.9.4/dist/leaflet.css';
    document.head.appendChild(link);
    const script = document.createElement('script');
    script.src = 'https://unpkg.com/leaflet@1.9.4/dist/leaflet.js';
    script.onload = bootWhenLeafletReady;
    document.head.appendChild(script);
  }

  // Clean up auto-refresh when page is hidden / navigated away
  document.addEventListener('visibilitychange', () => {
    if (document.visibilityState === 'hidden' && autoRefreshTimer) {
      clearInterval(autoRefreshTimer);
    } else if (document.visibilityState === 'visible') {
      startAutoRefresh();
    }
  });

  // Inject spin keyframe for refresh button
  const style = document.createElement('style');
  style.textContent = '@keyframes spin{to{transform:rotate(360deg)}}';
  document.head.appendChild(style);

})();
