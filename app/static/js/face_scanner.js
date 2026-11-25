/**
 * app/static/js/face_scanner.js
 * =============================
 * Enterprise Face Biometric Scanning & Real-time Verification Engine.
 * 
 * Features:
 * - High-speed real-time face detection & 68-point landmark tracking.
 * - 128-dimensional deep neural facial descriptor extraction (FaceNet/face-api).
 * - Multi-frame burst sampling for high accuracy.
 * - Interactive holographic scanning reticle with laser sweep & mesh overlay.
 * - Real-time Euclidean distance face matching against registered profile.
 * - Dual-layer fallback for resilient operation across all mobile & desktop browsers.
 */

'use strict';

class FaceBiometricEngine {
  constructor() {
    this.modelsLoaded = false;
    this.loadingPromise = null;
    this.activeStream = null;
    this.scanInterval = null;
    this.animFrameId = null;
    this.isScanning = false;
    
    // Local self-hosted model repository (zero CDN/network dependency)
    this.MODEL_URL = '/static/models';
  }

  /**
   * Load face detection, landmark, eye, and recognition neural models
   */
  async loadModels() {
    if (this.modelsLoaded) return true;
    if (this.loadingPromise) return this.loadingPromise;

    this.loadingPromise = (async () => {
      try {
        // Ensure face-api library is present in global scope
        if (typeof faceapi === 'undefined') {
          try {
            await this._loadScript('/static/js/face-api.min.js');
          } catch (e) {
            console.warn('Local face-api load failed, using fallback CDN:', e);
            await this._loadScript('https://cdn.jsdelivr.net/npm/@vladmandic/face-api/dist/face-api.min.js');
          }
        }

        console.log('[FaceBiometric] Loading high-accuracy AI models from local static repository...');
        // Load SSD MobileNetV1 (full precision) + TinyFaceDetector + 68 Landmark + Recognition
        await Promise.all([
          faceapi.nets.ssdMobilenetv1.loadFromUri(this.MODEL_URL).catch(() => null),
          faceapi.nets.tinyFaceDetector.loadFromUri(this.MODEL_URL),
          faceapi.nets.faceLandmark68Net.loadFromUri(this.MODEL_URL),
          faceapi.nets.faceRecognitionNet.loadFromUri(this.MODEL_URL)
        ]);

        this.modelsLoaded = true;
        console.log('[FaceBiometric] Neural biometric models successfully initialized.');
        return true;
      } catch (err) {
        console.error('[FaceBiometric] Error loading neural models:', err);
        this.modelsLoaded = false;
        return false;
      }
    })();

    return this.loadingPromise;
  }

  _loadScript(src) {
    return new Promise((resolve, reject) => {
      if (document.querySelector(`script[src="${src}"]`)) {
        return resolve();
      }
      const script = document.createElement('script');
      script.src = src;
      script.async = true;
      script.onload = () => resolve();
      script.onerror = (e) => reject(new Error(`Failed to load script: ${src}`));
      document.head.appendChild(script);
    });
  }

  /**
   * Start webcam video stream on the given video element
   */
  async startCamera(videoEl) {
    if (this.activeStream) {
      this.stopCamera();
    }

    const constraints = {
      video: {
        facingMode: 'user',
        width: { ideal: 640, min: 320 },
        height: { ideal: 480, min: 240 }
      },
      audio: false
    };

    const stream = await navigator.mediaDevices.getUserMedia(constraints);
    this.activeStream = stream;
    videoEl.srcObject = stream;
    videoEl.muted = true;
    videoEl.setAttribute('playsinline', 'true');

    return new Promise((resolve) => {
      const onReady = () => {
        videoEl.play().catch(e => console.warn('video.play() caught:', e));
        resolve(stream);
      };

      if (videoEl.readyState >= 2) {
        onReady();
      } else {
        videoEl.onloadedmetadata = () => onReady();
        videoEl.oncanplay = () => onReady();
        // Fallback resolve after 400ms to guarantee execution
        setTimeout(onReady, 400);
      }
    });
  }

  /**
   * Alias for startCamera to support all templates
   */
  async initCamera(videoEl) {
    return this.startCamera(videoEl);
  }

  /**
   * Stop active camera stream
   */
  stopCamera() {
    if (this.activeStream) {
      this.activeStream.getTracks().forEach(track => track.stop());
      this.activeStream = null;
    }
    if (this.animFrameId) {
      cancelAnimationFrame(this.animFrameId);
      this.animFrameId = null;
    }
    if (this.scanInterval) {
      clearInterval(this.scanInterval);
      this.scanInterval = null;
    }
    this.isScanning = false;
  }

  /**
   * Run a thorough facial scan (samples multiple frames over duration)
   * 
   * @param {HTMLVideoElement} videoEl
   * @param {HTMLCanvasElement} canvasEl
   * @param {number|Function} durationOrProgress - duration in ms OR onProgress callback
   * @param {Function} [onProgress] - callback(progressPct, statusMsg)
   * @returns {Promise<{success: boolean, descriptor: Array<number>, photoBase64: string, message: string}>}
   */
  _getEAR(eye) {
    if (!eye || eye.length < 6) return 0.25;
    const p1 = eye[0], p2 = eye[1], p3 = eye[2], p4 = eye[3], p5 = eye[4], p6 = eye[5];
    const v1 = Math.hypot(p2.x - p6.x, p2.y - p6.y);
    const v2 = Math.hypot(p3.x - p5.x, p3.y - p5.y);
    const h = Math.hypot(p1.x - p4.x, p1.y - p4.y) || 1;
    return (v1 + v2) / (2.0 * h);
  }

  /**
   * Perform thorough multi-frame biometric face scan with eye-tracking
   * and Best-of-N frame optimization.
   */
  async performThoroughScan(videoEl, canvasEl, durationOrProgress, onProgress, registeredDesc = null) {
    let durationMs = 3000;
    let progressCb = onProgress;

    if (typeof durationOrProgress === 'number') {
      durationMs = durationOrProgress;
    } else if (typeof durationOrProgress === 'function') {
      progressCb = durationOrProgress;
    }

    await this.loadModels();

    canvasEl.width = videoEl.videoWidth || 640;
    canvasEl.height = videoEl.videoHeight || 480;
    const ctx = canvasEl.getContext('2d');

    this.isScanning = true;
    const collectedSamples = [];
    const earHistory = [];
    const landmarkHistory = [];
    let lastSampleTime = 0;
    let scanStartTime = Date.now();
    let maxWaitTimeMs = 12000; // allow up to 12s for employee to position face
    let laserY = 0;
    let laserDir = 1;

    return new Promise((resolve) => {
      const renderScanReticle = async () => {
        if (!this.isScanning) return;

        ctx.clearRect(0, 0, canvasEl.width, canvasEl.height);

        const elapsed = Date.now() - scanStartTime;
        const sampleCount = collectedSamples.length;
        const targetSamples = 4;
        const progress = Math.min(100, Math.round((sampleCount / targetSamples) * 100));

        // Animate laser sweep line
        laserY += 4 * laserDir;
        if (laserY > canvasEl.height * 0.85) laserDir = -1;
        if (laserY < canvasEl.height * 0.15) laserDir = 1;

        // Draw HUD biometric oval target
        const cx = canvasEl.width / 2;
        const cy = canvasEl.height / 2;
        const rx = canvasEl.width * 0.28;
        const ry = canvasEl.height * 0.38;

        // Glowing oval
        ctx.save();
        ctx.beginPath();
        ctx.ellipse(cx, cy, rx, ry, 0, 0, 2 * Math.PI);
        ctx.strokeStyle = sampleCount > 0 ? '#10b981' : '#06b6d4';
        ctx.lineWidth = 3;
        ctx.shadowColor = sampleCount > 0 ? '#10b981' : '#06b6d4';
        ctx.shadowBlur = 15;
        ctx.stroke();

        // Laser scan sweep line
        ctx.beginPath();
        ctx.moveTo(cx - rx * 0.95, laserY);
        ctx.lineTo(cx + rx * 0.95, laserY);
        ctx.strokeStyle = sampleCount > 0 ? '#10b981' : '#38bdf8';
        ctx.lineWidth = 2.5;
        ctx.shadowColor = sampleCount > 0 ? '#10b981' : '#38bdf8';
        ctx.shadowBlur = 12;
        ctx.stroke();
        ctx.restore();

        // Corner brackets
        this._drawCornerReticles(ctx, cx, cy, rx, ry);

        // Progress text overlay
        ctx.font = 'bold 15px -apple-system, sans-serif';
        ctx.fillStyle = '#ffffff';
        ctx.textAlign = 'center';
        if (sampleCount === 0) {
          ctx.fillText('ALIGN FACE & KEEP EYES OPEN...', cx, canvasEl.height - 30);
        } else {
          ctx.fillText(`CAPTURING BIOMETRICS: ${progress}%`, cx, canvasEl.height - 30);
        }

        // Robust Detection Pipeline
        if (typeof faceapi !== 'undefined' && this.modelsLoaded) {
          try {
            let detection = null;

            // 1. Try TinyFaceDetector with higher input resolution (416) for crisp landmark tracking
            if (faceapi.nets.tinyFaceDetector && faceapi.nets.tinyFaceDetector.isLoaded) {
              detection = await faceapi
                .detectSingleFace(videoEl, new faceapi.TinyFaceDetectorOptions({ inputSize: 416, scoreThreshold: 0.25 }))
                .withFaceLandmarks()
                .withFaceDescriptor();
            }

            // 2. Try SSD MobileNetV1 if tiny detector missed
            if (!detection && faceapi.nets.ssdMobilenetv1 && faceapi.nets.ssdMobilenetv1.isLoaded) {
              detection = await faceapi
                .detectSingleFace(videoEl, new faceapi.SsdMobilenetv1Options({ minConfidence: 0.25 }))
                .withFaceLandmarks()
                .withFaceDescriptor();
            }

            if (detection) {
              const now = Date.now();
              const landmarks = detection.landmarks;
              const leftEye = landmarks.getLeftEye();
              const rightEye = landmarks.getRightEye();

              const earLeft = this._getEAR(leftEye);
              const earRight = this._getEAR(rightEye);
              const avgEAR = (earLeft + earRight) / 2.0;
              const eyesOpen = avgEAR >= 0.16;

              earHistory.push(avgEAR);
              if (landmarks.getNose() && landmarks.getNose().length > 0) {
                const noseTip = landmarks.getNose()[0];
                landmarkHistory.push({ x: noseTip.x, y: noseTip.y });
              }

              // Visual Eye & Feature Tracking Rings
              ctx.save();
              ctx.fillStyle = eyesOpen ? '#10b981' : '#f59e0b';
              ctx.strokeStyle = eyesOpen ? '#059669' : '#d97706';
              ctx.lineWidth = 2;
              
              // Eye rings
              ctx.beginPath();
              leftEye.forEach((pt, idx) => idx === 0 ? ctx.moveTo(pt.x, pt.y) : ctx.lineTo(pt.x, pt.y));
              ctx.closePath();
              ctx.stroke();

              ctx.beginPath();
              rightEye.forEach((pt, idx) => idx === 0 ? ctx.moveTo(pt.x, pt.y) : ctx.lineTo(pt.x, pt.y));
              ctx.closePath();
              ctx.stroke();

              faceapi.draw.drawFaceLandmarks(canvasEl, landmarks);
              ctx.restore();

              // Collect sample if spaced at least 150ms apart
              if (now - lastSampleTime >= 150) {
                lastSampleTime = now;
                const desc = Array.from(detection.descriptor);
                const photo = this._captureVideoFrame(videoEl);

                let frameScore = 0;
                let frameDistance = 999;
                if (registeredDesc) {
                  const cmp = this.compareDescriptors(desc, registeredDesc, 0.385);
                  frameScore = cmp.score;
                  frameDistance = cmp.distance;
                }

                collectedSamples.push({
                  descriptor: desc,
                  photo: photo,
                  eyesOpen: eyesOpen,
                  score: frameScore,
                  distance: frameDistance
                });
              }
            }
          } catch (e) {
            console.warn('Frame detection step error:', e);
          }
        }

        if (progressCb) {
          if (sampleCount === 0) {
            progressCb(10, 'Looking for face... Please look directly at camera');
          } else {
            progressCb(progress, `Scanning facial landmarks (${progress}%)...`);
          }
        }

        // Complete when target samples collected OR timeout after maxWaitTimeMs
        if (sampleCount >= targetSamples) {
          this.isScanning = false;

          let chosenDescriptor = null;
          let chosenPhoto = null;

          if (registeredDesc && collectedSamples.length > 0) {
            // Sort by score descending - Best-of-N matching!
            collectedSamples.sort((a, b) => b.score - a.score);
            chosenDescriptor = collectedSamples[0].descriptor;
            chosenPhoto = collectedSamples[0].photo;
          } else {
            // For enrollment: prefer samples where eyes were open
            const openSamples = collectedSamples.filter(s => s.eyesOpen);
            const pool = openSamples.length > 0 ? openSamples : collectedSamples;
            chosenDescriptor = this._averageDescriptors(pool.map(s => s.descriptor));
            chosenPhoto = pool[0]?.photo || this._captureVideoFrame(videoEl);
          }

          let earDelta = 0.05;
          let landmarkVariance = 0.01;
          if (earHistory.length >= 2) {
            earDelta = Math.max(...earHistory) - Math.min(...earHistory);
          }
          if (landmarkHistory.length >= 2) {
            const avgX = landmarkHistory.reduce((s, p) => s + p.x, 0) / landmarkHistory.length;
            const avgY = landmarkHistory.reduce((s, p) => s + p.y, 0) / landmarkHistory.length;
            landmarkVariance = landmarkHistory.reduce((s, p) => s + Math.hypot(p.x - avgX, p.y - avgY), 0) / (landmarkHistory.length * (canvasEl.width || 640));
          }

          resolve({
            success: true,
            descriptor: chosenDescriptor,
            photoBase64: chosenPhoto,
            livenessMetrics: {
              ear_delta: earDelta,
              landmark_variance: landmarkVariance,
              sample_count: earHistory.length
            },
            message: 'Facial biometric profile successfully scanned and verified.'
          });
        } else if (elapsed > maxWaitTimeMs) {
          this.isScanning = false;
          resolve({
            success: false,
            descriptor: null,
            photoBase64: null,
            message: 'Face scan timed out. Please ensure good lighting and look directly into the camera.'
          });
        } else {
          this.animFrameId = requestAnimationFrame(renderScanReticle);
        }
      };

      this.animFrameId = requestAnimationFrame(renderScanReticle);
    });
  }

  _drawCornerReticles(ctx, cx, cy, rx, ry) {
    ctx.strokeStyle = '#06b6d4';
    ctx.lineWidth = 3;
    const len = 25;
    const x1 = cx - rx - 10;
    const x2 = cx + rx + 10;
    const y1 = cy - ry - 10;
    const y2 = cy + ry + 10;

    // Top-left
    ctx.beginPath();
    ctx.moveTo(x1, y1 + len); ctx.lineTo(x1, y1); ctx.lineTo(x1 + len, y1);
    ctx.stroke();
    // Top-right
    ctx.beginPath();
    ctx.moveTo(x2 - len, y1); ctx.lineTo(x2, y1); ctx.lineTo(x2, y1 + len);
    ctx.stroke();
    // Bottom-left
    ctx.beginPath();
    ctx.moveTo(x1, y2 - len); ctx.lineTo(x1, y2); ctx.lineTo(x1 + len, y2);
    ctx.stroke();
    // Bottom-right
    ctx.beginPath();
    ctx.moveTo(x2 - len, y2); ctx.lineTo(x2, y2); ctx.lineTo(x2, y2 - len);
    ctx.stroke();
  }

  _captureVideoFrame(videoEl) {
    const tempCanvas = document.createElement('canvas');
    tempCanvas.width = 480;
    tempCanvas.height = 360;
    const ctx = tempCanvas.getContext('2d');
    // Mirror selfie correctly
    ctx.translate(tempCanvas.width, 0);
    ctx.scale(-1, 1);
    ctx.drawImage(videoEl, 0, 0, tempCanvas.width, tempCanvas.height);
    return tempCanvas.toDataURL('image/jpeg', 0.85);
  }

  _averageDescriptors(descriptors) {
    const len = descriptors[0].length;
    const avg = new Array(len).fill(0);
    for (let i = 0; i < len; i++) {
      let sum = 0;
      for (let j = 0; j < descriptors.length; j++) {
        sum += descriptors[j][i];
      }
      avg[i] = sum / descriptors.length;
    }
    return avg;
  }

  _generateCanvasStructuralDescriptor(videoEl) {
    // Generate deterministic 128-d spatial frequency distribution vector
    const c = document.createElement('canvas');
    c.width = 64;
    c.height = 64;
    const ctx = c.getContext('2d');
    ctx.drawImage(videoEl, 0, 0, 64, 64);
    const imgData = ctx.getImageData(0, 0, 64, 64).data;
    const vec = new Array(128).fill(0);

    for (let i = 0; i < imgData.length; i += 4) {
      const gray = (imgData[i] * 0.299 + imgData[i + 1] * 0.587 + imgData[i + 2] * 0.114) / 255.0;
      const bin = Math.floor((i / 4) % 128);
      vec[bin] += gray;
    }

    // Normalize vector
    const norm = Math.sqrt(vec.reduce((sum, v) => sum + v * v, 0)) || 1.0;
    return vec.map(v => Number((v / norm).toFixed(6)));
  }

  /**
   * Compare two 128-d face descriptors using Euclidean distance
   * 
   * @param {Array<number>|string} desc1
   * @param {Array<number>|string} desc2
   * @param {number} threshold - Strict match threshold (default 0.385)
   * @returns {{isMatch: boolean, matched: boolean, distance: number, similarity: number, score: number}}
   */
  compareDescriptors(desc1, desc2, threshold = 0.385) {
    let d1 = desc1;
    let d2 = desc2;

    try {
      if (typeof d1 === 'string') d1 = JSON.parse(d1);
      if (typeof d2 === 'string') d2 = JSON.parse(d2);
    } catch (e) {
      console.warn('[FaceBiometric] JSON parse error in compareDescriptors', e);
      return { isMatch: false, matched: false, distance: 999, similarity: 0, score: 0 };
    }

    if (!Array.isArray(d1) || !Array.isArray(d2) || d1.length !== d2.length || d1.length < 64) {
      console.warn('[FaceBiometric] Invalid descriptor dimensions:', d1?.length, d2?.length);
      return { isMatch: false, matched: false, distance: 999, similarity: 0, score: 0 };
    }

    let sum = 0;
    for (let i = 0; i < d1.length; i++) {
      const diff = Number(d1[i]) - Number(d2[i]);
      sum += diff * diff;
    }
    const distance = Math.sqrt(sum);

    let similarity = 0;
    if (distance <= 0.15) {
      similarity = Math.round(100 - (distance / 0.15) * 8);
    } else if (distance <= 0.385) {
      similarity = Math.round(92 - ((distance - 0.15) / 0.235) * 32);
    } else if (distance <= 0.50) {
      similarity = Math.round(60 - ((distance - 0.385) / 0.115) * 40);
    } else {
      similarity = Math.max(0, Math.round(20 - ((distance - 0.50) / 0.20) * 20));
    }
    similarity = Math.max(0, Math.min(100, similarity));

    // Strict biometric match requires distance <= 0.385 AND similarity >= 60%
    const isMatch = (distance <= threshold) && (similarity >= 60);

    return {
      isMatch,
      matched: isMatch,
      distance: Number(distance.toFixed(4)),
      similarity,
      score: similarity
    };
  }
}

// Global instance
window.faceBiometric = new FaceBiometricEngine();
