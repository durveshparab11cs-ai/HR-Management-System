'use strict';

(function() {
  console.log('[ATTENDANCE] Starting...');
  
  const el = id => document.getElementById(id);
  
  let ciReady = false;
  let coReady = false;
  let ciCamera = null;
  let coCamera = null;
  
  // ================== INIT ==================
  
  function init() {
    console.log('[ATTENDANCE] v2 - Initializing event listeners');
    
    // Photo zones
    el('photo-zone')?.addEventListener('click', () => {
      console.log('[ATTENDANCE] photo-zone clicked');
      startCheckInCamera();
    });
    
    el('co-photo-zone')?.addEventListener('click', () => {
      console.log('[ATTENDANCE] co-photo-zone clicked');
      startCheckOutCamera();
    });
    
    // Retake buttons
    el('ci-btn-retake')?.addEventListener('click', () => {
      console.log('[ATTENDANCE] ci retake clicked');
      ciReady = false;
      el('ci-selfie-preview').style.display = 'none';
      el('photo-zone').style.display = 'block';
      startCheckInCamera();
    });
    
    el('co-btn-retake')?.addEventListener('click', () => {
      console.log('[ATTENDANCE] co retake clicked');
      coReady = false;
      el('co-selfie-preview').style.display = 'none';
      el('co-photo-zone').style.display = 'block';
      startCheckOutCamera();
    });
    
    // Check-in button
    el('btn-checkin')?.addEventListener('click', () => {
      console.log('[ATTENDANCE] btn-checkin clicked, ciReady:', ciReady);
      if (!ciReady) {
        alert('Please capture and upload a photo first');
        return;
      }
      doCheckIn();
    });
    
    // Check-out button
    el('btn-checkout')?.addEventListener('click', () => {
      console.log('[ATTENDANCE] btn-checkout clicked, coReady:', coReady);
      if (!coReady) {
        alert('Please capture and upload a photo first');
        return;
      }
      doCheckOut();
    });
    
    console.log('[ATTENDANCE] Event listeners attached');
  }
  
  // ================== CHECK-IN CAMERA ==================
  
  async function startCheckInCamera() {
    try {
      console.log('[ATTENDANCE] Starting check-in camera');
      
      if (!ciCamera) {
        ciCamera = new CameraCapture('ci-video', 'ci-canvas');
      }
      
      el('photo-zone').style.display = 'none';
      el('ci-video-container').style.display = 'block';
      el('ci-btn-capture').style.display = 'block';
      
      await ciCamera.start();
      console.log('[ATTENDANCE] Check-in camera started');
      
      el('ci-btn-capture').onclick = () => captureCheckIn();
      
    } catch (err) {
      console.error('[ATTENDANCE] Camera error:', err.message);
      alert('Camera error: ' + err.message);
    }
  }
  
  async function captureCheckIn() {
    try {
      console.log('[ATTENDANCE] Capturing check-in photo');
      const jpeg = await ciCamera.capture();
      console.log('[ATTENDANCE] Captured, size:', jpeg.length);
      
      await ciCamera.stop();
      
      showCheckInPreview(jpeg);
    } catch (err) {
      console.error('[ATTENDANCE] Capture error:', err.message);
      alert('Capture error: ' + err.message);
    }
  }
  
  function showCheckInPreview(jpeg) {
    console.log('[ATTENDANCE] Showing check-in preview');
    
    el('ci-video-container').style.display = 'none';
    el('ci-selfie-preview').style.display = 'block';
    el('ci-selfie-img').src = jpeg;
    el('ci-btn-capture').style.display = 'none';
    el('ci-btn-retake').style.display = 'block';
    
    uploadCheckInPhoto(jpeg);
  }
  
  async function uploadCheckInPhoto(jpeg) {
    try {
      console.log('[ATTENDANCE] Uploading check-in photo');
      
      const csrf = document.querySelector('meta[name="csrf-token"]')?.getAttribute('content') || '';
      
      const res = await fetch('/attendance/capture-selfie', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-CSRFToken': csrf
        },
        body: JSON.stringify({
          selfie: jpeg,
          type: 'checkin'
        })
      });
      
      console.log('[ATTENDANCE] Upload response status:', res.status);
      
      const data = await res.json();
      console.log('[ATTENDANCE] Upload response:', data);
      
      if (!res.ok || !data.success) {
        console.error('[ATTENDANCE] Upload failed:', data.message);
        alert('Upload failed: ' + (data.message || 'Unknown error'));
        return;
      }
      
      // SUCCESS
      console.log('[ATTENDANCE] Upload successful, enabling check-in button');
      ciReady = true;
      
      el('ci-photo-badge').className = 'badge bg-success-subtle text-success small';
      el('ci-photo-badge').innerHTML = '<i class="bi bi-check-circle me-1"></i>✓ Captured';
      
      el('ci-text').textContent = 'Check In Now';
      
      el('btn-checkin').disabled = false;
      
      alert('✓ Photo uploaded! Check In button is now enabled.');
      
    } catch (err) {
      console.error('[ATTENDANCE] Upload error:', err.message);
      alert('Upload error: ' + err.message);
    }
  }
  
  // ================== CHECK-OUT CAMERA ==================
  
  async function startCheckOutCamera() {
    try {
      console.log('[ATTENDANCE] Starting check-out camera');
      
      if (!coCamera) {
        coCamera = new CameraCapture('co-video', 'co-canvas');
      }
      
      el('co-photo-zone').style.display = 'none';
      el('co-video-container').style.display = 'block';
      el('co-btn-capture').style.display = 'block';
      
      await coCamera.start();
      console.log('[ATTENDANCE] Check-out camera started');
      
      el('co-btn-capture').onclick = () => captureCheckOut();
      
    } catch (err) {
      console.error('[ATTENDANCE] Camera error:', err.message);
      alert('Camera error: ' + err.message);
    }
  }
  
  async function captureCheckOut() {
    try {
      console.log('[ATTENDANCE] Capturing check-out photo');
      const jpeg = await coCamera.capture();
      console.log('[ATTENDANCE] Captured, size:', jpeg.length);
      
      await coCamera.stop();
      
      showCheckOutPreview(jpeg);
    } catch (err) {
      console.error('[ATTENDANCE] Capture error:', err.message);
      alert('Capture error: ' + err.message);
    }
  }
  
  function showCheckOutPreview(jpeg) {
    console.log('[ATTENDANCE] Showing check-out preview');
    
    el('co-video-container').style.display = 'none';
    el('co-selfie-preview').style.display = 'block';
    el('co-selfie-img').src = jpeg;
    el('co-btn-capture').style.display = 'none';
    el('co-btn-retake').style.display = 'block';
    
    uploadCheckOutPhoto(jpeg);
  }
  
  async function uploadCheckOutPhoto(jpeg) {
    try {
      console.log('[ATTENDANCE] Uploading check-out photo');
      
      const csrf = document.querySelector('meta[name="csrf-token"]')?.getAttribute('content') || '';
      
      const res = await fetch('/attendance/capture-selfie', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-CSRFToken': csrf
        },
        body: JSON.stringify({
          selfie: jpeg,
          type: 'checkout'
        })
      });
      
      console.log('[ATTENDANCE] Upload response status:', res.status);
      
      const data = await res.json();
      console.log('[ATTENDANCE] Upload response:', data);
      
      if (!res.ok || !data.success) {
        console.error('[ATTENDANCE] Upload failed:', data.message);
        alert('Upload failed: ' + (data.message || 'Unknown error'));
        return;
      }
      
      // SUCCESS
      console.log('[ATTENDANCE] Upload successful, enabling check-out button');
      coReady = true;
      
      el('co-photo-badge').className = 'badge bg-success-subtle text-success small';
      el('co-photo-badge').innerHTML = '<i class="bi bi-check-circle me-1"></i>✓ Captured';
      
      el('co-text').textContent = 'Check Out Now';
      
      el('btn-checkout').disabled = false;
      
      alert('✓ Photo uploaded! Check Out button is now enabled.');
      
    } catch (err) {
      console.error('[ATTENDANCE] Upload error:', err.message);
      alert('Upload error: ' + err.message);
    }
  }
  
  // ================== CHECK-IN / OUT ==================
  
  function doCheckIn() {
    console.log('[ATTENDANCE] Performing check-in');
    
    const csrf = document.querySelector('meta[name="csrf-token"]')?.getAttribute('content') || '';
    const form = new FormData();
    form.append('latitude', window.lat || 0);
    form.append('longitude', window.lon || 0);
    form.append('accuracy', window.acc || 0);
    
    el('btn-checkin').disabled = true;
    el('ci-text').textContent = 'Processing...';
    
    fetch('/attendance/checkin', {
      method: 'POST',
      headers: { 'X-CSRFToken': csrf },
      body: form
    })
    .then(r => r.json())
    .then(d => {
      console.log('[ATTENDANCE] Check-in response:', d);
      if (d.success) {
        alert('✅ Check-in successful!');
        location.reload();
      } else {
        alert('❌ Check-in failed: ' + d.message);
        el('btn-checkin').disabled = false;
        el('ci-text').textContent = 'Check In Now';
      }
    })
    .catch(e => {
      console.error('[ATTENDANCE] Check-in error:', e);
      alert('❌ Check-in error: ' + e.message);
      el('btn-checkin').disabled = false;
      el('ci-text').textContent = 'Check In Now';
    });
  }
  
  function doCheckOut() {
    console.log('[ATTENDANCE] Performing check-out');
    
    const csrf = document.querySelector('meta[name="csrf-token"]')?.getAttribute('content') || '';
    const form = new FormData();
    form.append('latitude', window.lat || 0);
    form.append('longitude', window.lon || 0);
    form.append('accuracy', window.acc || 0);
    
    el('btn-checkout').disabled = true;
    el('co-text').textContent = 'Processing...';
    
    fetch('/attendance/checkout', {
      method: 'POST',
      headers: { 'X-CSRFToken': csrf },
      body: form
    })
    .then(r => r.json())
    .then(d => {
      console.log('[ATTENDANCE] Check-out response:', d);
      if (d.success) {
        alert('✅ Check-out successful!');
        location.reload();
      } else {
        alert('❌ Check-out failed: ' + d.message);
        el('btn-checkout').disabled = false;
        el('co-text').textContent = 'Check Out Now';
      }
    })
    .catch(e => {
      console.error('[ATTENDANCE] Check-out error:', e);
      alert('❌ Check-out error: ' + e.message);
      el('btn-checkout').disabled = false;
      el('co-text').textContent = 'Check Out Now';
    });
  }
  
  // ================== BOOT ==================
  
  if (document.readyState === 'loading') {
    console.log('[ATTENDANCE] DOM loading, waiting...');
    document.addEventListener('DOMContentLoaded', init);
  } else {
    console.log('[ATTENDANCE] DOM already ready, initializing now');
    init();
  }
  
})();
