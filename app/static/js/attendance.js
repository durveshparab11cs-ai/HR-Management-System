'use strict';

(function() {
  const el = id => document.getElementById(id);
  
  // State
  let ciReady = false;
  let coReady = false;
  let stream = null;
  
  // ================== SETUP ==================
  
  // Photo zone click -> start camera
  el('photo-zone')?.addEventListener('click', () => openCamera('ci'));
  el('co-photo-zone')?.addEventListener('click', () => openCamera('co'));
  
  // Retake buttons
  el('ci-btn-retake')?.addEventListener('click', () => {
    ciReady = false;
    el('ci-selfie-preview').style.display = 'none';
    el('photo-zone').style.display = 'block';
    openCamera('ci');
  });
  
  el('co-btn-retake')?.addEventListener('click', () => {
    coReady = false;
    el('co-selfie-preview').style.display = 'none';
    el('co-photo-zone').style.display = 'block';
    openCamera('co');
  });
  
  // Check-in button
  el('btn-checkin')?.addEventListener('click', () => {
    if (!ciReady) {
      alert('Please upload a photo first');
      return;
    }
    doCheckIn();
  });
  
  // Check-out button
  el('btn-checkout')?.addEventListener('click', () => {
    if (!coReady) {
      alert('Please upload a photo first');
      return;
    }
    doCheckOut();
  });
  
  // ================== CAMERA ==================
  
  async function openCamera(type) {
    try {
      if (stream) stream.getTracks().forEach(t => t.stop());
      stream = await navigator.mediaDevices.getUserMedia({
        video: { facingMode: 'user' },
        audio: false
      });
      
      const vid = el(type === 'ci' ? 'ci-video' : 'co-video');
      vid.srcObject = stream;
      await vid.play();
      
      el(type === 'ci' ? 'photo-zone' : 'co-photo-zone').style.display = 'none';
      el(type === 'ci' ? 'ci-video-container' : 'co-video-container').style.display = 'block';
      el(type === 'ci' ? 'ci-btn-capture' : 'co-btn-capture').style.display = 'block';
      el(type === 'ci' ? 'ci-btn-capture' : 'co-btn-capture').onclick = () => snap(type, vid);
      
    } catch (e) {
      alert('Camera error: ' + e.message);
    }
  }
  
  function snap(type, vid) {
    const canvas = el(type === 'ci' ? 'ci-canvas' : 'co-canvas');
    const ctx = canvas.getContext('2d');
    canvas.width = vid.videoWidth;
    canvas.height = vid.videoHeight;
    ctx.scale(-1, 1);
    ctx.drawImage(vid, -canvas.width, 0);
    
    const jpeg = canvas.toDataURL('image/jpeg', 0.9);
    
    stream.getTracks().forEach(t => t.stop());
    stream = null;
    
    showPreview(type, jpeg);
  }
  
  function showPreview(type, jpeg) {
    el(type === 'ci' ? 'ci-video-container' : 'co-video-container').style.display = 'none';
    el(type === 'ci' ? 'ci-selfie-preview' : 'co-selfie-preview').style.display = 'block';
    el(type === 'ci' ? 'ci-selfie-img' : 'co-selfie-img').src = jpeg;
    el(type === 'ci' ? 'ci-btn-capture' : 'co-btn-capture').style.display = 'none';
    el(type === 'ci' ? 'ci-btn-retake' : 'co-btn-retake').style.display = 'block';
    
    upload(type, jpeg);
  }
  
  // ================== UPLOAD ==================
  
  async function upload(type, jpeg) {
    try {
      const csrf = document.querySelector('meta[name="csrf-token"]')?.getAttribute('content') || '';
      const res = await fetch('/attendance/capture-selfie', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-CSRFToken': csrf
        },
        body: JSON.stringify({
          selfie: jpeg,
          type: type === 'ci' ? 'checkin' : 'checkout'
        })
      });
      
      const data = await res.json();
      
      if (!res.ok || !data.success) {
        alert('Upload failed: ' + (data.message || 'Unknown error'));
        return;
      }
      
      // SUCCESS - enable button
      if (type === 'ci') {
        ciReady = true;
        el('ci-photo-badge').className = 'badge bg-success-subtle text-success small';
        el('ci-photo-badge').innerHTML = '<i class="bi bi-check-circle me-1"></i>✓ Captured';
        el('ci-text').textContent = 'Check In Now';
        el('btn-checkin').disabled = false;
      } else {
        coReady = true;
        el('co-photo-badge').className = 'badge bg-success-subtle text-success small';
        el('co-photo-badge').innerHTML = '<i class="bi bi-check-circle me-1"></i>✓ Captured';
        el('co-text').textContent = 'Check Out Now';
        el('btn-checkout').disabled = false;
      }
      
      alert('✓ Photo uploaded! Button is enabled.');
      
    } catch (e) {
      alert('Upload error: ' + e.message);
    }
  }
  
  // ================== CHECK-IN / OUT ==================
  
  function doCheckIn() {
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
      if (d.success) {
        alert('✅ Check-in successful!');
        location.reload();
      } else {
        alert('❌ ' + d.message);
        el('btn-checkin').disabled = false;
        el('ci-text').textContent = 'Check In Now';
      }
    })
    .catch(e => {
      alert('❌ ' + e.message);
      el('btn-checkin').disabled = false;
      el('ci-text').textContent = 'Check In Now';
    });
  }
  
  function doCheckOut() {
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
      if (d.success) {
        alert('✅ Check-out successful!');
        location.reload();
      } else {
        alert('❌ ' + d.message);
        el('btn-checkout').disabled = false;
        el('co-text').textContent = 'Check Out Now';
      }
    })
    .catch(e => {
      alert('❌ ' + e.message);
      el('btn-checkout').disabled = false;
      el('co-text').textContent = 'Check Out Now';
    });
  }
  
})();
