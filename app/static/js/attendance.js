'use strict';

// ──────────────────────────────────────────────────────────────────────────────
// attendance.js — Attendance dashboard: camera, GPS, check-in/out
//
// Root causes fixed in this version:
//  #2  enableCheckin() now reads data-state attributes instead of textContent
//  #3  ciPhotoReady / coPhotoReady are primed from server-side HAS_CI_PHOTO /
//      HAS_CO_PHOTO constants on page load, so a refresh restores button state
//  #5  upload error now shows data.message (not the absent data.error)
//  #6  alert() + location.reload() replaced with in-page toast + smooth reload
// ──────────────────────────────────────────────────────────────────────────────

(function () {

  // ── helpers ───────────────────────────────────────────────────────────────
  const el = (id) => document.getElementById(id);

  // ── state ─────────────────────────────────────────────────────────────────
  // #3 — prime from server-side flags so page refresh restores state correctly.
  // HAS_CI_PHOTO / HAS_CO_PHOTO are injected by the template as JS consts.
  let ciPhotoReady = (typeof HAS_CI_PHOTO !== 'undefined') ? HAS_CI_PHOTO : false;
  let coPhotoReady = (typeof HAS_CO_PHOTO !== 'undefined') ? HAS_CO_PHOTO : false;
  let gpsWatchId   = null;
  let currentStream = null;

  console.log('[Attendance] Init — ciPhotoReady:', ciPhotoReady, '| coPhotoReady:', coPhotoReady);

  // ── CSRF ──────────────────────────────────────────────────────────────────
  function getCsrf() {
    const meta = document.querySelector('meta[name="csrf-token"]');
    if (meta) return meta.getAttribute('content');
    const script = el('csrf');
    if (script) return script.textContent.trim();
    if (typeof CSRF_TOKEN !== 'undefined') return CSRF_TOKEN;
    return '';
  }

  // ── Toast ─────────────────────────────────────────────────────────────────
  function showToast(msg, type = 'success', duration = 5000) {
    const wrap = el('att-toasts');
    if (!wrap) { console.warn('[Toast] container #att-toasts not found'); return; }

    const iconMap = {
      success: 'bi-check-circle-fill text-success',
      error:   'bi-x-circle-fill text-danger',
      warn:    'bi-exclamation-triangle-fill text-warning',
      info:    'bi-info-circle-fill text-info',
    };
    const icon = iconMap[type] || iconMap.info;

    const toast = document.createElement('div');
    toast.className = `att-toast ${type === 'error' ? 'error' : type === 'warn' ? 'warn' : ''}`;
    toast.innerHTML = `
      <i class="bi ${icon} fs-5 flex-shrink-0"></i>
      <div class="att-toast-body">${msg}</div>
      <button class="att-toast-close" aria-label="Close">&times;</button>
    `;
    toast.querySelector('.att-toast-close').addEventListener('click', () => toast.remove());
    wrap.appendChild(toast);
    if (duration > 0) setTimeout(() => toast.remove(), duration);
    return toast;
  }

  // ── Button enable/disable ─────────────────────────────────────────────────
  // #2 — read data-state="already_checked_in" attribute instead of textContent,
  //       which was unreliable due to icon text being included in textContent.
  function enableCheckin() {
    const btn         = el('btn-checkin');
    const btnCheckout = el('btn-checkout');

    console.log('[enableCheckin] ciPhotoReady:', ciPhotoReady, '| coPhotoReady:', coPhotoReady);

    if (btn && ciPhotoReady) {
      const state = btn.dataset.state || '';
      if (state !== 'already_checked_in') {
        btn.disabled = false;
        console.log('✅ Check-in button ENABLED');
        // Update helper text to confirm readiness
        const txt = el('ci-text');
        if (txt && txt.textContent.trim() === 'Upload Photo + GPS to Enable') {
          txt.textContent = 'Check In Now';
        }
      }
    }

    if (btnCheckout && coPhotoReady) {
      const state = btnCheckout.dataset.state || '';
      if (state !== 'already_checked_out' && state !== 'check_in_first') {
        btnCheckout.disabled = false;
        console.log('✅ Check-out button ENABLED');
        const txt = el('co-text');
        if (txt && txt.textContent.trim() === 'Upload Photo + GPS to Enable') {
          txt.textContent = 'Check Out Now';
        }
      }
    }
  }

  // ── Camera ────────────────────────────────────────────────────────────────
  function setupPhotoClick() {
    const ciZone = el('photo-zone');
    const coZone = el('co-photo-zone');
    if (ciZone) ciZone.addEventListener('click', () => startLiveCamera('ci'));
    if (coZone) coZone.addEventListener('click', () => startLiveCamera('co'));
  }

  async function startLiveCamera(type) {
    const photoZone      = el(type === 'ci' ? 'photo-zone'        : 'co-photo-zone');
    const videoContainer = el(type === 'ci' ? 'ci-video-container': 'co-video-container');
    const video          = el(type === 'ci' ? 'ci-video'          : 'co-video');
    const captureBtn     = el(type === 'ci' ? 'ci-btn-capture'    : 'co-btn-capture');
    const cameraStatus   = el(type === 'ci' ? 'ci-camera-status'  : 'co-camera-status');

    try {
      console.log('[Camera] Requesting access for:', type);

      if (currentStream) {
        currentStream.getTracks().forEach(t => t.stop());
        currentStream = null;
      }

      const stream = await navigator.mediaDevices.getUserMedia({
        video: { facingMode: 'user', width: { ideal: 1280 }, height: { ideal: 720 } },
        audio: false,
      });
      currentStream = stream;

      console.log('[Camera] Access granted');

      if (photoZone)      photoZone.style.display      = 'none';
      if (videoContainer) videoContainer.style.display = 'block';
      video.srcObject = stream;
      await video.play();

      if (cameraStatus) cameraStatus.style.display = 'block';
      if (statusText) statusText.textContent = 'Requesting camera access...';
      if (cameraError) cameraError.style.display = 'none';
      if (cameraDisabled) cameraDisabled.style.display = 'none';
      
      // Initialize camera if not already done
      if (type === 'ci' && !ciCamera) {
        ciCamera = new CameraCapture('ci-video', 'ci-canvas');
      } else if (type === 'co' && !coCamera) {
        coCamera = new CameraCapture('co-video', 'co-canvas');
      }
      
      const camera = type === 'ci' ? ciCamera : coCamera;
      console.log('Camera instance created');
      
      // Start camera with timeout
      console.log('Starting camera stream...');
      await Promise.race([
        camera.start(),
        new Promise((_, reject) => 
          setTimeout(() => reject(new Error('Camera startup timeout')), 8000)
        )
      ]);
      
      console.log('Camera stream started, showing video container');
      
      // Show video container and capture button
      if (videoContainer) {
        videoContainer.style.display = 'block';
        console.log('Video container shown');
      }
      if (captureBtn) {
        captureBtn.style.display = 'block';
        console.log('Capture button shown');
      }
    } catch (err) {
      console.error('[Camera] Error:', err.name, err.message);
      if (photoZone) {
        photoZone.innerHTML = `
          <div style="text-align:center;padding:20px;color:#991b1b">
            <i class="bi bi-exclamation-circle fs-1 d-block mb-2"></i>
            <div class="fw-bold" style="font-size:14px;margin-bottom:8px">Camera Access Required</div>
            <div style="font-size:12px;color:#666;margin-bottom:12px">
              ${err.name === 'NotAllowedError'
                ? 'Permission denied. Please enable camera in your browser settings.'
                : 'Camera unavailable: ' + err.message}
            </div>
            <div style="font-size:11px;background:#fef3c7;padding:8px;border-radius:6px;color:#92400e">
              <strong>Fix:</strong> Click the camera icon in the browser address bar and allow access.
            </div>
          </div>`;
        photoZone.style.display = 'block';
      }
      showToast(
        err.name === 'NotAllowedError'
          ? 'Camera permission denied. Enable camera access in browser settings.'
          : 'Camera unavailable: ' + err.message,
        'error'
      );
    }
  }

  function captureFrame(type, video, stream) {
    const canvas = el(type === 'ci' ? 'ci-canvas' : 'co-canvas');
    const ctx    = canvas.getContext('2d');
    try {
      canvas.width  = video.videoWidth  || 640;
      canvas.height = video.videoHeight || 480;
      console.log('[Camera] Capturing frame:', canvas.width, 'x', canvas.height);

      // Mirror the selfie (matches the CSS scaleX(-1) on the video preview)
      ctx.save();
      ctx.scale(-1, 1);
      ctx.drawImage(video, -canvas.width, 0);
      ctx.restore();

      const dataUrl = canvas.toDataURL('image/jpeg', 0.92);
      console.log('[Camera] Frame captured, data length:', dataUrl.length);

      stream.getTracks().forEach(t => t.stop());
      currentStream = null;

      showPhotoPreview(type, dataUrl);
    } catch (err) {
      console.error('[Camera] Capture error:', err);
      showToast('Failed to capture photo: ' + err.message, 'error');
    }
  }

  function showPhotoPreview(type, dataUrl) {
    const videoContainer  = el(type === 'ci' ? 'ci-video-container' : 'co-video-container');
    const previewContainer= el(type === 'ci' ? 'ci-selfie-preview'  : 'co-selfie-preview');
    const previewImg      = el(type === 'ci' ? 'ci-selfie-img'      : 'co-selfie-img');
    const captureBtn      = el(type === 'ci' ? 'ci-btn-capture'     : 'co-btn-capture');
    const retakeBtn       = el(type === 'ci' ? 'ci-btn-retake'      : 'co-btn-retake');
    const cameraStatus    = el(type === 'ci' ? 'ci-camera-status'   : 'co-camera-status');

    if (videoContainer)   videoContainer.style.display   = 'none';
    if (previewContainer) previewContainer.style.display = 'block';
    if (previewImg)       previewImg.src                 = dataUrl;
    if (captureBtn)       captureBtn.style.display       = 'none';
    if (retakeBtn)        retakeBtn.style.display        = 'block';
    if (cameraStatus)     cameraStatus.style.display     = 'none';

    uploadSelfie(type, dataUrl);
  }

  // ── Upload selfie ─────────────────────────────────────────────────────────
  async function uploadSelfie(type, dataUrl) {
    const uploadLabel = type === 'ci' ? 'check-in' : 'check-out';
    console.log('[Upload] Starting selfie upload for:', uploadLabel);

    // Show uploading indicator on badge
    const badge = el(type === 'ci' ? 'ci-photo-badge' : 'co-photo-badge');
    if (badge) {
      badge.className = 'badge bg-warning-subtle text-warning small';
      badge.innerHTML = '<i class="bi bi-arrow-repeat me-1"></i>Uploading…';
    }

    try {
      const res = await fetch('/attendance/capture-selfie', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-CSRFToken': getCsrf(),
        },
        body: JSON.stringify({
          selfie: dataUrl,
          type:   type === 'ci' ? 'checkin' : 'checkout',
        }),
      });

      // Guard: make sure we got JSON, not an HTML error page
      const contentType = res.headers.get('content-type') || '';
      if (!contentType.includes('application/json')) {
        const text = await res.text();
        console.error('[Upload] Non-JSON response (HTTP', res.status, '):', text.slice(0, 300));
        throw new Error(`Server returned HTTP ${res.status}. Check server logs.`);
      }

      const data = await res.json();
      console.log('[Upload] Server response:', data);

      if (data.success) {
        // ── SUCCESS PATH ──────────────────────────────────────────
        if (type === 'ci') {
          ciPhotoReady = true;
          console.log('✅ ciPhotoReady = true');
        } else {
          coPhotoReady = true;
          console.log('✅ coPhotoReady = true');
        }

        // #2 — enable button via state attribute check (robust)
        enableCheckin();

        // Update badge to success
        if (badge) {
          badge.className = 'badge bg-success-subtle text-success small';
          badge.innerHTML = '<i class="bi bi-check-circle me-1"></i>✓ Photo Uploaded';
        }

        // Update button text if still showing placeholder copy
        const btnText = el(type === 'ci' ? 'ci-text' : 'co-text');
        if (btnText) {
          btnText.textContent = type === 'ci' ? 'Check In Now' : 'Check Out Now';
        }

        // #6 — toast instead of alert()
        showToast(`✓ Photo captured successfully! Ready for ${uploadLabel}.`, 'success');

        // Generate proof image in background (fire-and-forget)
        generateProof(type);

      } else {
        // ── FAILURE PATH ──────────────────────────────────────────
        // #5 — backend sends `message`, not `error`
        const reason = data.message || data.error || 'Upload failed. Please retry.';
        console.error('[Upload] Server-side failure:', reason);

        if (badge) {
          badge.className = 'badge bg-danger-subtle text-danger small';
          badge.innerHTML = '<i class="bi bi-x-circle me-1"></i>Upload Failed';
        }

        showToast('❌ ' + reason, 'error');
      }
    } catch (err) {
      console.error('[Upload] Network/parse error:', err);
      if (badge) {
        badge.className = 'badge bg-danger-subtle text-danger small';
        badge.innerHTML = '<i class="bi bi-x-circle me-1"></i>Upload Failed';
      }
      showToast('❌ Upload failed: ' + err.message, 'error');
    }
  }

  // ── Proof image (fire-and-forget) ─────────────────────────────────────────
  async function generateProof(type) {
    try {
      await fetch('/attendance/generate-proof-image', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-CSRFToken': getCsrf(),
        },
        body: JSON.stringify({
          type:             type === 'ci' ? 'checkin' : 'checkout',
          latitude:         window.lat            || 0,
          longitude:        window.lon            || 0,
          accuracy:         window.acc            || 0,
          distance_metres:  window.distanceMetres || 0,
        }),
      });
      
      console.log('Proof generation response status:', res.status);
      
      if (!res.ok) {
        const text = await res.text();
        console.error('Proof generation HTTP error:', res.status, text);
        throw new Error(`HTTP ${res.status}: Proof generation failed`);
      }
      
      const data = await res.json();
      console.log('Proof generation response:', data);
      
      if (!data.success) {
        console.error('Proof generation failed:', data.message);
      }
    } catch (err) {
      // Non-critical — proof image is cosmetic
      console.warn('[ProofImage] Generation failed (non-critical):', err.message);
    }
  }

  // ── Clock ─────────────────────────────────────────────────────────────────
  function updateClock() {
    const now     = new Date();
    const hh      = String(now.getHours()).padStart(2, '0');
    const mm      = String(now.getMinutes()).padStart(2, '0');
    const ss      = String(now.getSeconds()).padStart(2, '0');
    const clockEl = el('att-clock');
    const dateEl  = el('att-date');
    if (clockEl) clockEl.textContent = `${hh}:${mm}:${ss}`;
    if (dateEl)  dateEl.textContent  = now.toLocaleDateString('en-IN', {
      weekday: 'short', month: 'short', day: 'numeric', year: 'numeric',
    });
  }

  // ── GPS ───────────────────────────────────────────────────────────────────
  function getGPS() {
    if (!navigator.geolocation) {
      const t = el('gps-text');
      if (t) t.textContent = 'Geolocation not supported by this browser';
      return;
    }

    const dot  = el('gps-dot');
    const text = el('gps-text');

    function onPosition(pos) {
      window.lat = pos.coords.latitude;
      window.lon = pos.coords.longitude;
      window.acc = pos.coords.accuracy;
      if (dot)  { dot.classList.remove('acquiring', 'error'); dot.classList.add('ok'); }
      if (text) text.textContent = 'GPS Ready ✓';
      if (window.map && window.OFFICE) window.map.setView([window.lat, window.lon], 17);
    }

    function onError(err) {
      console.warn('[GPS] Error:', err.message);
      if (dot)  { dot.classList.remove('acquiring', 'ok'); dot.classList.add('error'); }
      if (text) text.textContent = 'GPS unavailable — enable location services';
    }

    const opts = { enableHighAccuracy: true, timeout: 10000, maximumAge: 0 };
    navigator.geolocation.getCurrentPosition(onPosition, onError, opts);
    gpsWatchId = navigator.geolocation.watchPosition(onPosition, () => {}, opts);
  }

  // ── Map ───────────────────────────────────────────────────────────────────
  function initMap() {
    const container = el('att-map');
    if (!container || typeof L === 'undefined') {
      console.warn('[Map] Container missing or Leaflet not loaded');
      return;
    }
    container.style.display = 'block';
    container.style.zIndex  = '1';

    window.map = L.map('att-map');
    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
      maxZoom: 19,
      attribution: '© OpenStreetMap',
    }).addTo(window.map);

    const officeData = el('office-data');
    if (officeData) {
      try {
        const d = JSON.parse(officeData.textContent);
        window.OFFICE = d;
        if (d.lat && d.lon) {
          L.marker([d.lat, d.lon], {
            icon: L.divIcon({
              html: '<div style="background:blue;width:14px;height:14px;border-radius:50%;border:2px solid white;box-shadow:0 0 4px blue"></div>',
            }),
          }).addTo(window.map);
          L.circle([d.lat, d.lon], {
            radius: Math.max(d.radius || 100, 25),
            color: 'blue', weight: 2, fillColor: 'blue', fillOpacity: 0.1,
          }).addTo(window.map);
          window.map.setView([d.lat, d.lon], 17);
          console.log('[Map] Initialized at office:', d.lat, d.lon, 'radius:', d.radius);
        }
      } catch (e) {
        console.warn('[Map] Failed to parse office-data:', e);
      }
    }
  }

  // ── Check-In submit ───────────────────────────────────────────────────────
  function submitCheckin() {
    if (!ciPhotoReady) {
      showToast('Please capture your selfie first.', 'warn');
      return;
    }

    const btn     = el('btn-checkin');
    const btnText = el('ci-text');
    const spinner = el('ci-spin');

    if (btn)     btn.disabled              = true;
    if (spinner) spinner.style.display     = 'inline-block';
    if (btnText) btnText.textContent       = 'Processing…';

    console.log('[CheckIn] GPS:', window.lat, window.lon, window.acc);

    const form = new FormData();
    form.append('latitude',  window.lat || 0);
    form.append('longitude', window.lon || 0);
    form.append('accuracy',  window.acc || 0);

    fetch('/attendance/checkin', {
      method: 'POST',
      headers: { 'X-CSRFToken': getCsrf() },
      body: form,
    })
    .then(r => r.json())
    .then(data => {
      console.log('[CheckIn] Response:', data);
      if (data.success) {
        // #6 — toast, then reload so server-rendered tiles show correct time
        showToast('✅ Checked in at ' + (data.time || '') + ' IST!', 'success', 3000);
        setTimeout(() => location.reload(), 1800);
      } else {
        showToast('❌ ' + (data.message || 'Check-in failed'), 'error');
        // Re-enable button so user can retry
        if (btn)     btn.disabled          = false;
        if (spinner) spinner.style.display = 'none';
        if (btnText) btnText.textContent   = 'Check In Now';
      }
    })
    .catch(err => {
      console.error('[CheckIn] Network error:', err);
      showToast('❌ Check-in failed: ' + err.message, 'error');
      if (btn)     btn.disabled          = false;
      if (spinner) spinner.style.display = 'none';
      if (btnText) btnText.textContent   = 'Check In Now';
    });
  }

  // ── Check-Out submit ──────────────────────────────────────────────────────
  function submitCheckout() {
    if (!coPhotoReady) {
      showToast('Please capture your check-out selfie first.', 'warn');
      return;
    }

    const btn     = el('btn-checkout');
    const btnText = el('co-text');
    const spinner = el('co-spin');

    if (btn)     btn.disabled              = true;
    if (spinner) spinner.style.display     = 'inline-block';
    if (btnText) btnText.textContent       = 'Processing…';

    console.log('[CheckOut] GPS:', window.lat, window.lon, window.acc);

    const form = new FormData();
    form.append('latitude',  window.lat || 0);
    form.append('longitude', window.lon || 0);
    form.append('accuracy',  window.acc || 0);

    fetch('/attendance/checkout', {
      method: 'POST',
      headers: { 'X-CSRFToken': getCsrf() },
      body: form,
    })
    .then(r => r.json())
    .then(data => {
      console.log('[CheckOut] Response:', data);
      if (data.success) {
        showToast(
          '✅ Checked out! Worked: ' + (data.working || '—'),
          'success', 3000
        );
        setTimeout(() => location.reload(), 1800);
      } else {
        showToast('❌ ' + (data.message || 'Check-out failed'), 'error');
        if (btn)     btn.disabled          = false;
        if (spinner) spinner.style.display = 'none';
        if (btnText) btnText.textContent   = 'Check Out Now';
      }
    })
    .catch(err => {
      console.error('[CheckOut] Network error:', err);
      showToast('❌ Check-out failed: ' + err.message, 'error');
      if (btn)     btn.disabled          = false;
      if (spinner) spinner.style.display = 'none';
      if (btnText) btnText.textContent   = 'Check Out Now';
    });
  }

  // ── Boot ──────────────────────────────────────────────────────────────────
  function boot() {
    console.log('[Attendance] Booting…');

    updateClock();
    setInterval(updateClock, 1000);

    // Camera click zones
    setupPhotoClick();

    // Retake — reset flag and restart camera
    el('ci-btn-retake')?.addEventListener('click', () => {
      ciPhotoReady = false;
      el('ci-selfie-preview').style.display = 'none';
      el('photo-zone').style.display        = 'block';
      el('ci-btn-retake').style.display     = 'none';
      // Reset badge
      const badge = el('ci-photo-badge');
      if (badge) {
        badge.className = 'badge bg-danger-subtle text-danger small';
        badge.innerHTML = 'Required';
      }
      startLiveCamera('ci');
    });

    el('co-btn-retake')?.addEventListener('click', () => {
      coPhotoReady = false;
      el('co-selfie-preview').style.display = 'none';
      el('co-photo-zone').style.display     = 'block';
      el('co-btn-retake').style.display     = 'none';
      const badge = el('co-photo-badge');
      if (badge) {
        badge.className = 'badge bg-danger-subtle text-danger small';
        badge.innerHTML = 'Required';
      }
      startLiveCamera('co');
    });

    // Check-in / Check-out buttons
    el('btn-checkin')?.addEventListener('click',  submitCheckin);
    el('btn-checkout')?.addEventListener('click', submitCheckout);

    // #3 — If photo was already uploaded before this page load (server flag),
    //       enable the button immediately without requiring a new capture.
    if (ciPhotoReady || coPhotoReady) {
      console.log('[Boot] Restoring button state from server flags');
      enableCheckin();
    }

    // Map first, then GPS
    initMap();
    getGPS();

    console.log('[Attendance] Ready');
  }

  // Wait for DOM
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', boot);
  } else {
    boot();
  }

})();
