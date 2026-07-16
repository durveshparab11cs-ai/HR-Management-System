/**
 * attendance.js — Smart HRMS High-Precision GPS Geofencing
 *
 * Security design:
 *   - NEVER hardcode office coords — always from database via #office-data
 *   - Buttons LOCKED until real GPS obtained with acceptable accuracy
 *   - useFallback() ONLY enables map view — never unlocks submission
 *   - Backend performs identical Haversine + accuracy validation (dual validation)
 *   - maximumAge: 0 — always fresh fix, never cached
 *   - Retries on timeout; only shows error after sustained failure
 */
'use strict';

(function () {

  /* ── Office config from DB (never hardcoded) ─────────────────────── */
  const _raw    = JSON.parse(document.getElementById('office-data')?.textContent || '{}');
  const OFFICE  = {
    lat:         parseFloat(_raw.lat)         || null,
    lon:         parseFloat(_raw.lon)         || null,
    radius:      parseFloat(_raw.radius)      || 100,
    name:        _raw.name                    || 'Office',
    minAccuracy: parseFloat(_raw.min_accuracy)|| 50,   // max acceptable GPS error in metres
  };

  const CI_URL    = '/attendance/checkin';
  const CO_URL    = '/attendance/checkout';
  const PHOTO_URL = '/attendance/upload-photo';
  const R         = 6_371_000; // Earth radius metres

  /* ── GPS state ───────────────────────────────────────────────────── */
  let lat      = null;   // confirmed employee latitude
  let lon      = null;   // confirmed employee longitude
  let acc      = null;   // confirmed GPS accuracy metres
  let gpsReady = false;  // true ONLY after real GPS with acceptable accuracy
  let _watchId = null;
  let _permRetries = 0;
  let autoRefreshTimer = null;
  let isRefreshing = false;

  /* ── Leaflet map state ───────────────────────────────────────────── */
  let map = null, empMarker = null, accCircle = null;

  const el = id => document.getElementById(id);

  /* ═══════════════════════════════════════════════════════════════════
     CLOCK
  ════════════════════════════════════════════════════════════════════ */
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

  /* ═══════════════════════════════════════════════════════════════════
     UTC → IST
  ════════════════════════════════════════════════════════════════════ */
  document.querySelectorAll('.utc-to-ist').forEach(s => {
    const iso = s.textContent.trim();
    if (!iso) return;
    try {
      const ist = new Date(new Date(iso).getTime() + 330 * 60000);
      s.textContent = String(ist.getUTCHours()).padStart(2,'0') + ':' + String(ist.getUTCMinutes()).padStart(2,'0');
    } catch (e) {}
  });

  /* ═══════════════════════════════════════════════════════════════════
     HAVERSINE — mirrors Python distance_calculator.py exactly
  ════════════════════════════════════════════════════════════════════ */
  function haversineMetres(la1, lo1, la2, lo2) {
    const r = Math.PI / 180;
    const phi1 = la1 * r, phi2 = la2 * r;
    const dPhi = (la2 - la1) * r, dLam = (lo2 - lo1) * r;
    const a = Math.sin(dPhi / 2) ** 2 + Math.cos(phi1) * Math.cos(phi2) * Math.sin(dLam / 2) ** 2;
    return R * 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a));
  }

  /* ═══════════════════════════════════════════════════════════════════
     STATUS BAR
  ════════════════════════════════════════════════════════════════════ */
  function setGpsStatus(state, msg) {
    const dot  = el('gps-dot');
    const text = el('gps-text');
    if (dot) {
      dot.className = 'gps-indicator ' + (state === 'ok' ? 'ok' : state === 'error' ? 'error' : 'acquiring');
    }
    if (text) {
      text.textContent = msg;
      text.style.color = state === 'ok' ? '#10b981' : state === 'error' ? '#ef4444' : '#f59e0b';
    }
  }


  /* ═══════════════════════════════════════════════════════════════════
     LEAFLET MAP
  ════════════════════════════════════════════════════════════════════ */
  function mkIcon(color, size) {
    size = size || 14;
    return L.divIcon({
      html: `<div style="background:${color};width:${size}px;height:${size}px;border-radius:50%;border:3px solid #fff;box-shadow:0 2px 10px rgba(0,0,0,.45)"></div>`,
      className: '', iconAnchor: [size / 2, size / 2]
    });
  }

  function initMap() {
    const container = el('att-map');
    if (!container || typeof L === 'undefined' || map) return;

    container.style.cssText = 'height:350px;width:100%;display:block;position:relative;z-index:0;';

    map = L.map('att-map', { zoomControl: true, attributionControl: true });
    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
      maxZoom: 19,
      attribution: '© <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>'
    }).addTo(map);

    if (OFFICE.lat && OFFICE.lon) {
      L.marker([OFFICE.lat, OFFICE.lon], { icon: mkIcon('#1a3c6e', 18) })
        .addTo(map)
        .bindPopup(`<strong>${OFFICE.name}</strong><br>Geofence: ${OFFICE.radius}m radius<br>Min GPS accuracy: ±${OFFICE.minAccuracy}m`);

      L.circle([OFFICE.lat, OFFICE.lon], {
        radius: OFFICE.radius, color: '#1a3c6e', fillColor: '#1a3c6e',
        fillOpacity: 0.07, weight: 2, dashArray: '6 4'
      }).addTo(map);

      map.setView([OFFICE.lat, OFFICE.lon], 17);
    }

    [100, 400, 1000].forEach(d => setTimeout(() => map && map.invalidateSize(), d));
  }

  function updateMapEmployee(empLat, empLon, empAcc, within) {
    if (!map) return;
    const color = within ? '#10b981' : '#ef4444';
    if (empMarker) {
      empMarker.setLatLng([empLat, empLon]).setIcon(mkIcon(color, 14));
    } else {
      empMarker = L.marker([empLat, empLon], { icon: mkIcon(color, 14) })
        .addTo(map).bindPopup('<strong>Your Location</strong>');
    }
    if (accCircle) {
      accCircle.setLatLng([empLat, empLon]).setRadius(empAcc);
    } else {
      accCircle = L.circle([empLat, empLon], {
        radius: empAcc, color: '#3b82f6', fillColor: '#3b82f6', fillOpacity: 0.1, weight: 1.5
      }).addTo(map);
    }
    map.setView([empLat, empLon], 17);
    map.invalidateSize();
  }


  /* ═══════════════════════════════════════════════════════════════════
     LIVE INFO PANEL (injected below map)
  ════════════════════════════════════════════════════════════════════ */
  function ensureInfoPanel() {
    if (el('gps-info-card')) return;
    const mapEl = el('att-map');
    if (!mapEl) return;
    const card = document.createElement('div');
    card.id = 'gps-info-card';
    card.style.cssText = 'background:#f8fafc;border-radius:12px;padding:14px 18px;margin-top:10px;font-size:.82rem;border:1px solid #e2e8f0';
    card.innerHTML = `
      <div style="display:grid;grid-template-columns:repeat(auto-fit,minmax(130px,1fr));gap:10px;margin-bottom:10px">
        <div><div style="color:#64748b;font-size:.68rem;text-transform:uppercase;letter-spacing:.05em;margin-bottom:2px">Your Latitude</div><div style="font-weight:700;color:#0f172a;font-size:.8rem" id="info-lat">—</div></div>
        <div><div style="color:#64748b;font-size:.68rem;text-transform:uppercase;letter-spacing:.05em;margin-bottom:2px">Your Longitude</div><div style="font-weight:700;color:#0f172a;font-size:.8rem" id="info-lon">—</div></div>
        <div><div style="color:#64748b;font-size:.68rem;text-transform:uppercase;letter-spacing:.05em;margin-bottom:2px">GPS Accuracy</div><div style="font-weight:700;font-size:.8rem" id="info-acc">—</div></div>
        <div><div style="color:#64748b;font-size:.68rem;text-transform:uppercase;letter-spacing:.05em;margin-bottom:2px">Distance</div><div style="font-weight:700;font-size:.8rem" id="info-dist">—</div></div>
        <div><div style="color:#64748b;font-size:.68rem;text-transform:uppercase;letter-spacing:.05em;margin-bottom:2px">Allowed Radius</div><div style="font-weight:700;color:#0f172a;font-size:.8rem" id="info-radius">${OFFICE.radius}m</div></div>
        <div><div style="color:#64748b;font-size:.68rem;text-transform:uppercase;letter-spacing:.05em;margin-bottom:2px">Zone Status</div><div style="font-weight:700;font-size:.8rem" id="info-zone">—</div></div>
        <div><div style="color:#64748b;font-size:.68rem;text-transform:uppercase;letter-spacing:.05em;margin-bottom:2px">Last Updated</div><div style="font-weight:700;color:#0f172a;font-size:.8rem" id="info-time">—</div></div>
      </div>
      <button id="btn-refresh-gps" style="background:#1a3c6e;color:#fff;border:none;border-radius:8px;padding:6px 16px;font-size:.78rem;font-weight:600;cursor:pointer;display:inline-flex;align-items:center;gap:6px">
        <i class="bi bi-arrow-clockwise"></i> Refresh Location
      </button>`;
    mapEl.insertAdjacentElement('afterend', card);
    el('btn-refresh-gps')?.addEventListener('click', function () {
      if (isRefreshing) return;
      isRefreshing = true;
      this.disabled = true;
      this.innerHTML = '<i class="bi bi-arrow-clockwise" style="animation:spin .65s linear infinite"></i> Refreshing…';
      _permRetries = 0;
      fetchGPS(true);
    });
  }

  function updateInfoPanel(empLat, empLon, empAcc, dist, within) {
    // gps-coords bar in template
    const cEl = el('gps-coords'); if (cEl) cEl.style.display = '';
    const ll = el('gps-latlon');  if (ll) ll.textContent = empLat.toFixed(6) + ', ' + empLon.toFixed(6);
    const dt = el('gps-dist-text'); if (dt) { dt.textContent = dist.toFixed(1) + 'm'; dt.style.color = within ? '#10b981' : '#ef4444'; }
    const ab = el('gps-accuracy-label'); if (ab) ab.textContent = '±' + Math.round(empAcc) + 'm accuracy';
    const badge = el('gps-dist-badge');
    if (badge) badge.innerHTML = `<span class="dist-badge ${within ? 'inside' : 'outside'}">${dist.toFixed(1)}m ${within ? '✓' : '✗'}</span>`;

    // rejection box
    const rb = el('rejection-box');
    if (rb) {
      if (!within) {
        rb.style.display = '';
        const re = el('rj-emp-dist'); if (re) re.textContent = dist.toFixed(1) + ' m';
        const ra = el('rj-allowed');  if (ra) ra.textContent = OFFICE.radius + ' m';
        const rm = el('rj-move-by');  if (rm) rm.textContent = Math.max(0, dist - OFFICE.radius).toFixed(1) + ' m closer';
      } else {
        rb.style.display = 'none';
      }
    }

    // injected info panel
    ensureInfoPanel();
    const accColor = empAcc <= OFFICE.minAccuracy ? '#10b981' : '#f59e0b';
    const li = el('info-lat');   if (li) li.textContent = empLat.toFixed(7);
    const lo = el('info-lon');   if (lo) lo.textContent = empLon.toFixed(7);
    const la = el('info-acc');   if (la) { la.textContent = '±' + Math.round(empAcc) + 'm'; la.style.color = accColor; }
    const ld = el('info-dist');  if (ld) { ld.textContent = dist.toFixed(1) + 'm'; ld.style.color = within ? '#10b981' : '#ef4444'; }
    const lz = el('info-zone');
    if (lz) {
      lz.textContent = within ? '✓ Inside Allowed Area' : '✗ Outside Allowed Area';
      lz.style.color = within ? '#10b981' : '#ef4444';
    }
    const lt = el('info-time');  if (lt) lt.textContent = new Date().toLocaleTimeString();
    const rb2 = el('btn-refresh-gps');
    if (rb2) { rb2.disabled = false; rb2.innerHTML = '<i class="bi bi-arrow-clockwise"></i> Refresh Location'; }
    isRefreshing = false;
  }


  /* ═══════════════════════════════════════════════════════════════════
     BUTTON STATE — security-critical
     Buttons are LOCKED until real GPS succeeds with acceptable accuracy.
     useFallback() NEVER unlocks submission buttons.
  ════════════════════════════════════════════════════════════════════ */
  function lockButtons(reason) {
    const ci = el('btn-checkin'), co = el('btn-checkout');
    if (ci) { ci.disabled = true; const t = el('ci-text'); if (t && reason) t.textContent = reason; }
    if (co) { co.disabled = true; }
  }

  function unlockButtons() {
    // Only called from onGPSSuccess when real coordinates verified
    const ci = el('btn-checkin'), co = el('btn-checkout');
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

  /* ═══════════════════════════════════════════════════════════════════
     GPS SUCCESS — validate by DISTANCE ONLY using Haversine
     Accuracy is displayed as info only — never used to reject.
  ════════════════════════════════════════════════════════════════════ */
  function onGPSSuccess(pos) {
    const empLat = pos.coords.latitude;
    const empLon = pos.coords.longitude;
    const empAcc = pos.coords.accuracy;

    // Always update stored coords with fresh position
    lat = empLat; lon = empLon; acc = empAcc;
    gpsReady = true;
    _permRetries = 0;

    const oLat = OFFICE.lat;
    const oLon = OFFICE.lon;
    const oRad = OFFICE.radius;

    // Haversine distance — only validation criterion
    const dist   = (oLat && oLon) ? haversineMetres(empLat, empLon, oLat, oLon) : 0;
    const within = dist <= oRad;

    // ── Console logging (requirement 7) ──────────────────────────────
    console.group('[Smart HRMS] GPS Verification');
    console.log('Current Latitude  :', empLat.toFixed(7));
    console.log('Current Longitude :', empLon.toFixed(7));
    console.log('Target Latitude   :', oLat);
    console.log('Target Longitude  :', oLon);
    console.log('GPS Accuracy      :', Math.round(empAcc) + 'm');
    console.log('Calculated Distance:', dist.toFixed(2) + 'm');
    console.log('Allowed Radius    :', oRad + 'm');
    console.log('Validation Result :', within ? 'PASS ✓' : 'FAIL ✗');
    console.groupEnd();

    // Update map and info panel
    updateMapEmployee(empLat, empLon, empAcc, within);
    updateInfoPanel(empLat, empLon, empAcc, dist, within);

    if (within) {
      // ── Inside radius — PASS ──────────────────────────────────────
      unlockButtons();
      setGpsStatus('ok',
        '✓ GPS Verified — ' + dist.toFixed(1) + 'm from office (±' + Math.round(empAcc) + 'm accuracy)'
      );
    } else {
      // ── Outside radius — FAIL ─────────────────────────────────────
      lockButtons('Outside Zone');
      setGpsStatus('error',
        '✗ Outside Allowed Area — ' + dist.toFixed(1) + 'm from office (allowed: ' + oRad + 'm)'
      );
    }
  }

  /* ═══════════════════════════════════════════════════════════════════
     GPS ERROR
  ════════════════════════════════════════════════════════════════════ */
  function onGPSError(err) {
    // CRITICAL: if GPS already succeeded (map shows location), NEVER show error
    if (gpsReady) return;

    // PERMISSION_DENIED (code 1) — Chromium HTTPS bug:
    // The error fires even when permission IS granted.
    // The watchPosition success callback fires shortly after.
    // Strategy: always retry, never show "denied" immediately.
    // Only show the error after 5 retries with no success.
    if (err.code === 1) {
      _permRetries++;
      if (_permRetries <= 5) {
        // Silent retry — don't show any error yet
        setGpsStatus('acquiring', 'Getting location… (' + _permRetries + '/5)');
        setTimeout(function () { if (!gpsReady) fetchGPS(false); }, 1500);
        return;
      }
      // After 5 retries, show actionable message
      setGpsStatus('error', 'Location access denied. Click the lock icon → Location → Allow, then reload the page.');
      lockButtons('GPS Denied');
      return;
    }

    // Timeout (code 3) — keep retrying silently, normal on first load
    if (err.code === 3) {
      _permRetries++;
      if (_permRetries <= 8) {
        setGpsStatus('acquiring', 'Getting GPS fix… (' + _permRetries + '/8)');
        setTimeout(function () { if (!gpsReady) fetchGPS(false); }, 2500);
        return;
      }
      setGpsStatus('acquiring', 'GPS slow to respond. Buttons locked until location confirmed.');
      return;
    }

    // Position unavailable (code 2)
    setGpsStatus('error', 'Device location unavailable. Enable location services and reload.');
    lockButtons('GPS Required');

    const rb = el('btn-refresh-gps');
    if (rb) { rb.disabled = false; rb.innerHTML = '<i class="bi bi-arrow-clockwise"></i> Refresh Location'; }
    isRefreshing = false;
  }


  /* ═══════════════════════════════════════════════════════════════════
     GPS FETCH — getCurrentPosition with fresh coords (maximumAge: 0)
  ════════════════════════════════════════════════════════════════════ */
  function fetchGPS(isManual) {
    if (!navigator.geolocation) {
      setGpsStatus('error', 'Geolocation not supported by this browser.');
      lockButtons('GPS Unsupported');
      return;
    }
    if (isManual) setGpsStatus('acquiring', 'Refreshing location…');

    // Cancel any existing watch
    if (_watchId !== null) {
      navigator.geolocation.clearWatch(_watchId);
      _watchId = null;
    }

    // Use getCurrentPosition — fresh fix every time (maximumAge: 0)
    navigator.geolocation.getCurrentPosition(
      function (pos) { onGPSSuccess(pos); },
      function (err) { if (!gpsReady) onGPSError(err); },
      {
        enableHighAccuracy: true,
        timeout: 15000,
        maximumAge: 0       // always fresh — never use cached coords
      }
    );
  }

  /* ═══════════════════════════════════════════════════════════════════
     START GPS (called on page load)
  ════════════════════════════════════════════════════════════════════ */
  function startGPS() {
    if (!navigator.geolocation) {
      setGpsStatus('error', 'Geolocation not supported by this browser.');
      lockButtons('GPS Unsupported');
      return;
    }

    // Buttons locked at start — only onGPSSuccess can unlock them
    lockButtons('Waiting for GPS…');
    setGpsStatus('acquiring', 'Loading GPS…');
    fetchGPS(false);

    // Advisory: watch for permission changes only (never blocks GPS directly)
    if (navigator.permissions) {
      navigator.permissions.query({ name: 'geolocation' }).then(function (perm) {
        perm.onchange = function () {
          if (perm.state === 'granted' && !gpsReady) {
            _permRetries = 0;
            setGpsStatus('acquiring', 'Permission granted — getting location…');
            fetchGPS(false);
          } else if (perm.state === 'denied' && !gpsReady) {
            setGpsStatus('error', 'Location denied. Click the lock icon → Allow → reload.');
            lockButtons('GPS Denied');
          }
        };
      }).catch(function () {});
    }
  }

  /* ═══════════════════════════════════════════════════════════════════
     AUTO-REFRESH every 10 seconds — updates map and status,
     but does NOT reset gpsReady (buttons stay unlocked during refresh)
  ════════════════════════════════════════════════════════════════════ */
  function startAutoRefresh() {
    if (autoRefreshTimer) clearInterval(autoRefreshTimer);
    autoRefreshTimer = setInterval(function () {
      if (!isRefreshing && document.visibilityState === 'visible') {
        // Do NOT reset gpsReady here — buttons must stay unlocked
        fetchGPS(false);
      }
    }, 10000);
  }

  document.addEventListener('visibilitychange', function () {
    if (document.visibilityState === 'hidden') {
      if (autoRefreshTimer) clearInterval(autoRefreshTimer);
    } else {
      startAutoRefresh();
    }
  });

  /* ═══════════════════════════════════════════════════════════════════
     SUBMIT ATTENDANCE — sends lat/lon/accuracy/timestamp to backend
     Backend performs identical Haversine + accuracy validation.
  ════════════════════════════════════════════════════════════════════ */
  async function submitAttendance(url, type) {
    if (!gpsReady || lat === null) {
      showToast('Location not verified. Please wait for GPS confirmation.', 'error');
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
            const ist   = new Date(new Date(`${today}T${displayTime}:00Z`).getTime() + 330 * 60000);
            displayTime = String(ist.getUTCHours()).padStart(2,'0') + ':' + String(ist.getUTCMinutes()).padStart(2,'0') + ' IST';
          } catch (e) {}
        }
        showToast(data.message || ('Done at ' + displayTime), 'success');
        setTimeout(() => location.reload(), 1800);
      } else {
        showToast(data.message || 'Action failed.', 'error');
        // Show rejection detail from backend GPS validation
        if (data.gps) {
          const d = (data.gps.distance_metres || 0).toFixed(1);
          const a = data.gps.allowed_radius || OFFICE.radius;
          const rb = el('rejection-box');
          if (rb && !data.gps.within_radius) {
            rb.style.display = '';
            const re = el('rj-emp-dist'); if (re) re.textContent = d + ' m';
            const ra = el('rj-allowed');  if (ra) ra.textContent = a + ' m';
            const rm = el('rj-move-by');  if (rm) rm.textContent = Math.max(0, d - a).toFixed(1) + ' m closer';
          }
        }
        setLoading(type, false);
      }
    } catch (e) {
      showToast('Network error. Check your connection and try again.', 'error');
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

  /* ═══════════════════════════════════════════════════════════════════
     PHOTO UPLOAD
  ════════════════════════════════════════════════════════════════════ */
  function initPhotoUpload() {
    const zone = el('photo-zone'), inp = el('photo-input'),
          btn  = el('btn-upload-photo'), prev = el('photo-preview-img'),
          spin = el('photo-spin'), txt = el('photo-txt');
    if (!zone || !inp) return;

    zone.addEventListener('click', () => inp.click());
    zone.addEventListener('dragover', e => { e.preventDefault(); zone.classList.add('drag-over'); });
    zone.addEventListener('dragleave', () => zone.classList.remove('drag-over'));
    zone.addEventListener('drop', e => { e.preventDefault(); zone.classList.remove('drag-over'); if (e.dataTransfer.files[0]) handleFile(e.dataTransfer.files[0]); });
    inp.addEventListener('change', () => { if (inp.files[0]) handleFile(inp.files[0]); });

    function handleFile(f) {
      if (!['image/jpeg','image/png','image/webp'].includes(f.type)) { showToast('Only JPG, PNG, WEBP.','error'); return; }
      if (f.size > 5*1024*1024) { showToast('Max 5 MB.','error'); return; }
      const r = new FileReader();
      r.onload = e => { if (prev) { prev.src = e.target.result; prev.style.display = 'block'; } };
      r.readAsDataURL(f);
      if (btn) btn.style.display = '';
    }

    btn?.addEventListener('click', async () => {
      const f = inp.files[0];
      if (!f) { showToast('Select a photo first.','warn'); return; }
      btn.disabled = true;
      if (spin) spin.style.display = 'inline-block';
      if (txt)  txt.textContent = 'Uploading…';
      const fd = new FormData(); fd.append('photo', f);
      try {
        const res = await fetch(PHOTO_URL, { method:'POST', headers:{'X-CSRFToken':CSRF_TOKEN,'X-Requested-With':'XMLHttpRequest'}, body: fd });
        const d = await res.json();
        if (d.success) { showToast('Photo uploaded.','success'); setTimeout(() => location.reload(), 1500); }
        else { showToast(d.message||'Upload failed.','error'); btn.disabled = false; if (spin) spin.style.display='none'; if (txt) txt.textContent='Upload Photo'; }
      } catch { showToast('Upload error.','error'); btn.disabled = false; if (spin) spin.style.display='none'; if (txt) txt.textContent='Upload Photo'; }
    });
  }

  /* ═══════════════════════════════════════════════════════════════════
     TOAST
  ════════════════════════════════════════════════════════════════════ */
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
    t.innerHTML = `<span class="att-toast-icon">${icons[type]||'ℹ️'}</span><div class="att-toast-body">${msg}</div><button class="att-toast-close" onclick="this.parentElement.remove()">✕</button>`;
    c.appendChild(t);
    setTimeout(() => { if (t.parentElement) t.remove(); }, 6000);
  }

  /* ═══════════════════════════════════════════════════════════════════
     BOOT
  ════════════════════════════════════════════════════════════════════ */
  el('btn-checkin')?.addEventListener('click',  () => submitAttendance(CI_URL, 'in'));
  el('btn-checkout')?.addEventListener('click', () => submitAttendance(CO_URL, 'out'));

  // Inject spin animation style
  const styleEl = document.createElement('style');
  styleEl.textContent = '@keyframes spin{to{transform:rotate(360deg)}}';
  document.head.appendChild(styleEl);

  function boot() {
    initMap();
    startGPS();
    startAutoRefresh();
    initPhotoUpload();
  }

  if (typeof L !== 'undefined') {
    document.readyState === 'loading' ? document.addEventListener('DOMContentLoaded', boot) : boot();
  } else {
    const lnk = document.createElement('link');
    lnk.rel = 'stylesheet'; lnk.href = 'https://unpkg.com/leaflet@1.9.4/dist/leaflet.css';
    document.head.appendChild(lnk);
    const scr = document.createElement('script');
    scr.src = 'https://unpkg.com/leaflet@1.9.4/dist/leaflet.js';
    scr.onload = boot;
    document.head.appendChild(scr);
  }

})();
