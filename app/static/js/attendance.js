'use strict';

(function () {
  // Minimal attendance system - camera + GPS proof
  
  const el = (id) => document.getElementById(id);
  let ciPhotoReady = false;
  let coPhotoReady = false;
  
  // Photo upload handler
  function setupPhotoClick() {
    const ciZone = el('photo-zone');
    const coZone = el('co-photo-zone');
    
    if (ciZone) {
      ciZone.addEventListener('click', () => openCamera('ci'));
    }
    
    if (coZone) {
      coZone.addEventListener('click', () => openCamera('co'));
    }
  }
  
  // Open camera
  async function openCamera(type) {
    console.log('Opening', type, 'camera');
    const videoContainer = el(type === 'ci' ? 'ci-video-container' : 'co-video-container');
    const video = el(type === 'ci' ? 'ci-video' : 'co-video');
    const captureBtn = el(type === 'ci' ? 'ci-btn-capture' : 'co-btn-capture');
    
    if (!videoContainer || !video) return;
    
    try {
      const stream = await navigator.mediaDevices.getUserMedia({
        video: { facingMode: 'user' },
        audio: false
      });
      
      video.srcObject = stream;
      video.play();
      videoContainer.style.display = 'block';
      if (captureBtn) captureBtn.style.display = 'inline-flex';
      
      // Store stream for later
      window.currentStream = stream;
      window.currentType = type;
      
    } catch (err) {
      alert('Camera access denied or not available: ' + err.message);
    }
  }
  
  // Capture selfie
  function captureSelfie(type) {
    const video = el(type === 'ci' ? 'ci-video' : 'co-video');
    const canvas = el(type === 'ci' ? 'ci-canvas' : 'co-canvas');
    
    if (!video || !canvas) return;
    
    const ctx = canvas.getContext('2d');
    canvas.width = video.videoWidth;
    canvas.height = video.videoHeight;
    
    // Draw mirrored
    ctx.save();
    ctx.scale(-1, 1);
    ctx.drawImage(video, -canvas.width, 0, canvas.width, canvas.height);
    ctx.restore();
    
    const dataUrl = canvas.toDataURL('image/jpeg', 0.75);
    
    // Stop camera
    if (window.currentStream) {
      window.currentStream.getTracks().forEach(t => t.stop());
    }
    
    // Show preview
    const preview = el(type === 'ci' ? 'ci-selfie-img' : 'co-selfie-img');
    const previewContainer = el(type === 'ci' ? 'ci-selfie-preview' : 'co-selfie-preview');
    const videoContainer = el(type === 'ci' ? 'ci-video-container' : 'co-video-container');
    
    if (preview) preview.src = dataUrl;
    if (previewContainer) previewContainer.style.display = 'block';
    if (videoContainer) videoContainer.style.display = 'none';
    
    // Upload
    uploadSelfie(type, dataUrl);
  }
  
  // Upload selfie
  async function uploadSelfie(type, dataUrl) {
    try {
      const res = await fetch('/attendance/capture-selfie', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-CSRFToken': document.querySelector('script#csrf')?.textContent || ''
        },
        body: JSON.stringify({
          selfie: dataUrl,
          type: type === 'ci' ? 'checkin' : 'checkout'
        })
      });
      
      const data = await res.json();
      
      if (data.success) {
        if (type === 'ci') ciPhotoReady = true;
        else coPhotoReady = true;
        
        // Generate proof image
        generateProof(type);
        enableCheckin();
      }
    } catch (err) {
      console.error('Upload error:', err);
      alert('Upload failed: ' + err.message);
    }
  }
  
  // Generate proof image
  async function generateProof(type) {
    try {
      await fetch('/attendance/generate-proof-image', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-CSRFToken': document.querySelector('script#csrf')?.textContent || ''
        },
        body: JSON.stringify({
          type: type === 'ci' ? 'checkin' : 'checkout',
          latitude: window.lat || 0,
          longitude: window.lon || 0,
          accuracy: window.acc || 0
        })
      });
    } catch (err) {
      console.error('Proof generation error:', err);
    }
  }
  
  // Enable check-in
  function enableCheckin() {
    const btn = el('btn-checkin');
    if (btn && ciPhotoReady) {
      btn.disabled = false;
    }
  }
  
  // Get GPS (background, doesn't block)
  function getGPS() {
    if (!navigator.geolocation) return;
    
    navigator.geolocation.watchPosition(
      (pos) => {
        window.lat = pos.coords.latitude;
        window.lon = pos.coords.longitude;
        window.acc = pos.coords.accuracy;
        
        // Update map if available
        if (window.map && window.OFFICE) {
          window.map.setView([window.lat, window.lon], 17);
        }
        
        const gpsStatus = el('gps-dot');
        if (gpsStatus) {
          gpsStatus.classList.remove('acquiring');
          gpsStatus.classList.add('ok');
        }
        
        const gpsText = el('gps-text');
        if (gpsText) gpsText.textContent = 'GPS Ready ✓';
      },
      () => {
        // Ignore errors
      },
      {
        enableHighAccuracy: true,
        timeout: 30000,
        maximumAge: 0
      }
    );
  }
  
  // Init map
  function initMap() {
    const container = el('att-map');
    if (!container || typeof L === 'undefined') return;
    
    window.map = L.map('att-map');
    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
      maxZoom: 19,
      attribution: '© OpenStreetMap'
    }).addTo(window.map);
    
    const officeData = document.getElementById('office-data');
    if (officeData) {
      const data = JSON.parse(officeData.textContent);
      window.OFFICE = data;
      
      if (data.lat && data.lon) {
        L.marker([data.lat, data.lon], {
          icon: L.divIcon({
            html: '<div style="background:blue;width:14px;height:14px;border-radius:50%;border:2px solid white"></div>'
          })
        }).addTo(window.map);
        
        L.circle([data.lat, data.lon], {
          radius: data.radius || 100,
          color: 'blue',
          fillOpacity: 0.1
        }).addTo(window.map);
        
        window.map.setView([data.lat, data.lon], 17);
      }
    }
  }
  
  // Boot
  function boot() {
    console.log('Attendance system starting...');
    
    // Setup events
    setupPhotoClick();
    
    // Setup capture buttons
    el('ci-btn-capture')?.addEventListener('click', () => captureSelfie('ci'));
    el('co-btn-capture')?.addEventListener('click', () => captureSelfie('co'));
    
    el('ci-btn-retake')?.addEventListener('click', () => {
      el('ci-selfie-preview').style.display = 'none';
      el('ci-video-container').style.display = 'block';
      openCamera('ci');
    });
    
    el('co-btn-retake')?.addEventListener('click', () => {
      el('co-selfie-preview').style.display = 'none';
      el('co-video-container').style.display = 'block';
      openCamera('co');
    });
    
    // Setup check-in/out
    el('btn-checkin')?.addEventListener('click', () => {
      if (ciPhotoReady) {
        fetch('/attendance/checkin', {
          method: 'POST',
          headers: {
            'X-CSRFToken': document.querySelector('script#csrf')?.textContent || ''
          }
        }).then(() => location.reload());
      }
    });
    
    el('btn-checkout')?.addEventListener('click', () => {
      if (coPhotoReady) {
        fetch('/attendance/checkout', {
          method: 'POST',
          headers: {
            'X-CSRFToken': document.querySelector('script#csrf')?.textContent || ''
          }
        }).then(() => location.reload());
      }
    });
    
    // Init map
    initMap();
    
    // Get GPS (non-blocking)
    getGPS();
    
    console.log('Attendance system ready');
  }
  
  // Wait for DOM
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', boot);
  } else {
    boot();
  }
  
})();
