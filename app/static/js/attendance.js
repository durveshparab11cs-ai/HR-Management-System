'use strict';

(function () {
  const el = (id) => document.getElementById(id);
  let ciPhotoReady = false;
  let coPhotoReady = false;
  let currentStream = null;
  
  // ─────────────────────────────────────────────────────────────────
  // CAMERA SETUP
  // ─────────────────────────────────────────────────────────────────
  
  async function startCamera(type) {
    console.log('[CAMERA] Starting camera for:', type);
    
    const photoZone = el(type === 'ci' ? 'photo-zone' : 'co-photo-zone');
    const videoContainer = el(type === 'ci' ? 'ci-video-container' : 'co-video-container');
    const video = el(type === 'ci' ? 'ci-video' : 'co-video');
    const captureBtn = el(type === 'ci' ? 'ci-btn-capture' : 'co-btn-capture');
    
    try {
      // Stop old stream
      if (currentStream) {
        currentStream.getTracks().forEach(t => t.stop());
      }
      
      // Get camera stream
      const stream = await navigator.mediaDevices.getUserMedia({
        video: { facingMode: 'user', width: { ideal: 1280 }, height: { ideal: 720 } },
        audio: false
      });
      
      currentStream = stream;
      console.log('[CAMERA] Stream acquired');
      
      // Hide zone, show video
      photoZone.style.display = 'none';
      videoContainer.style.display = 'block';
      
      // Attach to video
      video.srcObject = stream;
      await video.play();
      console.log('[CAMERA] Video playing');
      
      // Show capture button
      captureBtn.style.display = 'block';
      captureBtn.onclick = () => capturePhoto(type, video);
      
    } catch (err) {
      console.error('[CAMERA] Error:', err.message);
      photoZone.innerHTML = `
        <div style="text-align:center;padding:20px;color:#991b1b">
          <i class="bi bi-exclamation-circle fs-1 d-block mb-2"></i>
          <div class="fw-bold">Camera Error</div>
          <div style="font-size:12px">${err.message}</div>
        </div>
      `;
      photoZone.style.display = 'block';
    }
  }
  
  function capturePhoto(type, video) {
    console.log('[CAPTURE] Capturing photo for:', type);
    
    const canvas = el(type === 'ci' ? 'ci-canvas' : 'co-canvas');
    const ctx = canvas.getContext('2d');
    
    // Set size
    canvas.width = video.videoWidth;
    canvas.height = video.videoHeight;
    console.log('[CAPTURE] Canvas size:', canvas.width, 'x', canvas.height);
    
    // Mirror + draw
    ctx.scale(-1, 1);
    ctx.drawImage(video, -canvas.width, 0);
    
    // Get JPEG
    const jpeg = canvas.toDataURL('image/jpeg', 0.95);
    console.log('[CAPTURE] JPEG size:', jpeg.length, 'bytes');
    
    // Stop stream
    currentStream.getTracks().forEach(t => t.stop());
    currentStream = null;
    
    // Show preview and upload
    showPreview(type, jpeg);
  }
  
  function showPreview(type, jpeg) {
    console.log('[PREVIEW] Showing preview for:', type);
    
    const videoContainer = el(type === 'ci' ? 'ci-video-container' : 'co-video-container');
    const previewContainer = el(type === 'ci' ? 'ci-selfie-preview' : 'co-selfie-preview');
    const previewImg = el(type === 'ci' ? 'ci-selfie-img' : 'co-selfie-img');
    const captureBtn = el(type === 'ci' ? 'ci-btn-capture' : 'co-btn-capture');
    const retakeBtn = el(type === 'ci' ? 'ci-btn-retake' : 'co-btn-retake');
    
    videoContainer.style.display = 'none';
    previewContainer.style.display = 'block';
    previewImg.src = jpeg;
    captureBtn.style.display = 'none';
    retakeBtn.style.display = 'block';
    retakeBtn.onclick = () => {
      ciPhotoReady = false;
      coPhotoReady = false;
      previewContainer.style.display = 'none';
      el(type === 'ci' ? 'photo-zone' : 'co-photo-zone').style.display = 'block';
      startCamera(type);
    };
    
    // AUTO UPLOAD
    uploadPhoto(type, jpeg);
  }
  
  // ─────────────────────────────────────────────────────────────────
  // PHOTO UPLOAD
  // ─────────────────────────────────────────────────────────────────
  
  async function uploadPhoto(type, jpeg) {
    console.log('[UPLOAD] Starting upload for:', type);
    
    try {
      // Get CSRF
      let csrf = '';
      const metaTag = document.querySelector('meta[name="csrf-token"]');
      if (metaTag) csrf = metaTag.getAttribute('content');
      console.log('[UPLOAD] CSRF token:', csrf ? 'found' : 'NOT FOUND');
      
      // Build payload
      const payload = {
        selfie: jpeg,
        type: type === 'ci' ? 'checkin' : 'checkout'
      };
      
      console.log('[UPLOAD] Payload size:', JSON.stringify(payload).length, 'bytes');
      console.log('[UPLOAD] Posting to: /attendance/capture-selfie');
      
      // POST
      const res = await fetch('/attendance/capture-selfie', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-CSRFToken': csrf || ''
        },
        body: JSON.stringify(payload)
      });
      
      console.log('[UPLOAD] Response status:', res.status);
      
      const data = await res.json();
      console.log('[UPLOAD] Response:', data);
      
      if (res.ok && data.success) {
        console.log('[UPLOAD] ✅ SUCCESS');
        
        // Set flag
        if (type === 'ci') {
          ciPhotoReady = true;
        } else {
          coPhotoReady = true;
        }
        
        // Update UI
        updateUI(type);
        
        // Alert
        alert('✓ Photo uploaded! Check In button is now enabled.');
      } else {
        console.error('[UPLOAD] ❌ FAILED:', data.message);
        alert('❌ Upload failed: ' + (data.message || 'Unknown error'));
      }
    } catch (err) {
      console.error('[UPLOAD] ❌ ERROR:', err.message);
      alert('❌ Upload error: ' + err.message);
    }
  }
  
  function updateUI(type) {
    console.log('[UI] Updating UI for:', type);
    
    // Badge
    const badge = el(type === 'ci' ? 'ci-photo-badge' : 'co-photo-badge');
    if (badge) {
      badge.className = 'badge bg-success-subtle text-success small';
      badge.innerHTML = '<i class="bi bi-check-circle me-1"></i>✓ Captured';
      console.log('[UI] Badge updated');
    }
    
    // Button text
    const btnText = el(type === 'ci' ? 'ci-text' : 'co-text');
    if (btnText) {
      btnText.textContent = type === 'ci' ? 'Check In Now' : 'Check Out Now';
      console.log('[UI] Button text updated');
    }
    
    // Enable button
    const btn = el(type === 'ci' ? 'btn-checkin' : 'btn-checkout');
    if (btn) {
      btn.disabled = false;
      console.log('[UI] Button ENABLED');
    }
  }
  
  // ─────────────────────────────────────────────────────────────────
  // CLICK HANDLERS
  // ─────────────────────────────────────────────────────────────────
  
  function setupPhotoClick() {
    const ciZone = el('photo-zone');
    const coZone = el('co-photo-zone');
    
    if (ciZone) {
      ciZone.addEventListener('click', () => {
        console.log('[CLICK] Photo zone clicked (check-in)');
        startCamera('ci');
      });
    }
    
    if (coZone) {
      coZone.addEventListener('click', () => {
        console.log('[CLICK] Photo zone clicked (check-out)');
        startCamera('co');
      });
    }
  }
  
  // ─────────────────────────────────────────────────────────────────
  // CHECK-IN / CHECK-OUT
  // ─────────────────────────────────────────────────────────────────
  
  function setupCheckInButton() {
    el('btn-checkin')?.addEventListener('click', () => {
      if (!ciPhotoReady) {
        alert('⚠️ Please capture and upload a photo first');
        return;
      }
      
      console.log('[CHECKIN] Submitting check-in with GPS:', window.lat, window.lon);
      
      const csrf = document.querySelector('meta[name="csrf-token"]')?.getAttribute('content') || '';
      const formData = new FormData();
      formData.append('latitude', window.lat || 0);
      formData.append('longitude', window.lon || 0);
      formData.append('accuracy', window.acc || 0);
      
      const btn = el('btn-checkin');
      const btnText = el('ci-text');
      btn.disabled = true;
      btnText.textContent = 'Processing...';
      
      fetch('/attendance/checkin', {
        method: 'POST',
        headers: { 'X-CSRFToken': csrf },
        body: formData
      })
      .then(r => r.json())
      .then(d => {
        console.log('[CHECKIN] Response:', d);
        if (d.success) {
          alert('✅ Check-in successful!');
          location.reload();
        } else {
          alert('❌ ' + d.message);
          btn.disabled = false;
          btnText.textContent = 'Check In Now';
        }
      })
      .catch(e => {
        console.error('[CHECKIN] Error:', e);
        alert('❌ ' + e.message);
        btn.disabled = false;
        btnText.textContent = 'Check In Now';
      });
    });
  }
  
  function setupCheckOutButton() {
    el('btn-checkout')?.addEventListener('click', () => {
      if (!coPhotoReady) {
        alert('⚠️ Please capture and upload a photo first');
        return;
      }
      
      console.log('[CHECKOUT] Submitting check-out with GPS:', window.lat, window.lon);
      
      const csrf = document.querySelector('meta[name="csrf-token"]')?.getAttribute('content') || '';
      const formData = new FormData();
      formData.append('latitude', window.lat || 0);
      formData.append('longitude', window.lon || 0);
      formData.append('accuracy', window.acc || 0);
      
      const btn = el('btn-checkout');
      const btnText = el('co-text');
      btn.disabled = true;
      btnText.textContent = 'Processing...';
      
      fetch('/attendance/checkout', {
        method: 'POST',
        headers: { 'X-CSRFToken': csrf },
        body: formData
      })
      .then(r => r.json())
      .then(d => {
        console.log('[CHECKOUT] Response:', d);
        if (d.success) {
          alert('✅ Check-out successful!');
          location.reload();
        } else {
          alert('❌ ' + d.message);
          btn.disabled = false;
          btnText.textContent = 'Check Out Now';
        }
      })
      .catch(e => {
        console.error('[CHECKOUT] Error:', e);
        alert('❌ ' + e.message);
        btn.disabled = false;
        btnText.textContent = 'Check Out Now';
      });
    });
  }
  
  // ─────────────────────────────────────────────────────────────────
  // GPS
  // ─────────────────────────────────────────────────────────────────
  
  function startGPS() {
    if (!navigator.geolocation) {
      console.warn('[GPS] Geolocation not available');
      return;
    }
    
    navigator.geolocation.getCurrentPosition(
      (pos) => {
        window.lat = pos.coords.latitude;
        window.lon = pos.coords.longitude;
        window.acc = pos.coords.accuracy;
        console.log('[GPS] Position updated:', window.lat, window.lon);
        
        const dot = el('gps-dot');
        if (dot) {
          dot.classList.remove('acquiring', 'error');
          dot.classList.add('ok');
        }
        
        const text = el('gps-text');
        if (text) text.textContent = 'GPS Ready ✓';
      },
      (err) => console.warn('[GPS] Error:', err.message),
      { enableHighAccuracy: true, timeout: 10000, maximumAge: 0 }
    );
  }
  
  // ─────────────────────────────────────────────────────────────────
  // BOOT
  // ─────────────────────────────────────────────────────────────────
  
  function boot() {
    console.log('[BOOT] Attendance system starting');
    
    setupPhotoClick();
    setupCheckInButton();
    setupCheckOutButton();
    startGPS();
    
    console.log('[BOOT] Ready');
  }
  
  // Start on DOM ready
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', boot);
  } else {
    boot();
  }
  
})();
