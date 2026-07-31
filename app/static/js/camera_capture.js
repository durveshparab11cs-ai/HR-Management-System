/**
 * camera_capture.js — Live Camera Capture Module
 * 
 * Provides CameraCapture class for getUserMedia API integration:
 * - Live preview with automatic permission handling
 * - Selfie mirror effect (CSS transform)
 * - Frame capture to canvas
 * - Automatic compression to 75% JPEG quality
 * - Automatic camera track stoppage after capture
 * - Permission status checking and change detection
 * - Cross-browser support (Chrome, Edge, Firefox, Android, iPhone Safari)
 * 
 * Usage:
 *   const cam = new CameraCapture('video-id', 'canvas-id');
 *   await cam.start();  // Request permission + show preview
 *   const base64 = await cam.capture();  // Capture + compress to 75% JPEG
 *   await cam.stop();  // Stop all tracks
 */

'use strict';

class CameraCapture {
  constructor(videoElementId, canvasElementId) {
    this.videoElementId = videoElementId;
    this.canvasElementId = canvasElementId;
    this.videoElement = document.getElementById(videoElementId);
    this.canvasElement = document.getElementById(canvasElementId);
    this.stream = null;
    this.isRunning = false;
    this.permissionStatus = null;
    this.onPermissionChangeCallback = null;

    if (!this.videoElement) {
      throw new Error(`Video element with ID "${videoElementId}" not found`);
    }
    if (!this.canvasElement) {
      throw new Error(`Canvas element with ID "${canvasElementId}" not found`);
    }

    // Apply mirror effect to video (selfie mode)
    this.videoElement.style.transform = 'scaleX(-1)';
    this.videoElement.style.WebkitTransform = 'scaleX(-1)';

    this._watchPermissionChanges();
  }

  /**
   * Start camera and show live preview
   * @returns {Promise<void>}
   */
  async start() {
    if (this.isRunning) {
      console.log('[CameraCapture] Camera already running');
      return;
    }

    try {
      console.log('[CameraCapture] Checking getUserMedia availability...');
      
      // Check if getUserMedia is available and accessible
      if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
        throw new Error('getUserMedia not available - browser does not support camera API');
      }

      console.log('[CameraCapture] Requesting camera access...');

      // Request camera with selfie preference
      const constraints = {
        video: {
          facingMode: 'user',  // Selfie camera
          width: { ideal: 1280 },
          height: { ideal: 720 }
        },
        audio: false
      };

      // Add detailed error logging
      console.log('[CameraCapture] Calling getUserMedia with constraints:', constraints);
      
      this.stream = await navigator.mediaDevices.getUserMedia(constraints);
      console.log('[CameraCapture] Stream obtained, tracks:', this.stream.getTracks().length);

      // Attach stream to video element
      this.videoElement.srcObject = this.stream;
      console.log('[CameraCapture] Stream attached to video element');

      // Wait for video to load with timeout
      await new Promise((resolve, reject) => {
        const timeout = setTimeout(() => {
          reject(new Error('Video metadata load timeout (5 seconds)'));
        }, 5000);
        
        this.videoElement.onloadedmetadata = () => {
          clearTimeout(timeout);
          console.log('[CameraCapture] Video metadata loaded, dimensions:', 
            this.videoElement.videoWidth, 'x', this.videoElement.videoHeight);
          
          this.videoElement.play().then(() => {
            console.log('[CameraCapture] Video playback started');
            resolve();
          }).catch((playErr) => {
            console.error('[CameraCapture] Video play error:', playErr);
            reject(playErr);
          });
        };
        
        this.videoElement.onerror = (err) => {
          clearTimeout(timeout);
          console.error('[CameraCapture] Video element error:', err);
          reject(new Error('Video element error: ' + (err?.message || 'Unknown')));
        };
      });

      this.isRunning = true;
      console.log('[CameraCapture] Camera started successfully');
    } catch (err) {
      console.error('[CameraCapture] Error starting camera:', err.name, err.message);
      console.error('[CameraCapture] Full error:', err);
      
      // Cleanup on error
      if (this.stream) {
        this.stream.getTracks().forEach(track => {
          console.log('[CameraCapture] Stopping track on error:', track.kind);
          track.stop();
        });
        this.stream = null;
      }
      
      throw err;
    }
  }

  /**
   * Capture frame from video and compress to base64 JPEG (75% quality)
   * @returns {Promise<string>} Base64 data URL of compressed JPEG
   */
  async capture() {
    if (!this.isRunning || !this.videoElement.srcObject) {
      throw new Error('Camera is not running. Call start() first.');
    }

    try {
      console.log('[CameraCapture] Capturing frame...');

      const ctx = this.canvasElement.getContext('2d', { willReadFrequently: true });

      // Set canvas size to match video dimensions
      const videoWidth = this.videoElement.videoWidth;
      const videoHeight = this.videoElement.videoHeight;

      if (videoWidth === 0 || videoHeight === 0) {
        throw new Error('Video dimensions not available. Wait for video to load.');
      }

      this.canvasElement.width = videoWidth;
      this.canvasElement.height = videoHeight;

      // Draw video frame with mirror effect (canvas space)
      ctx.save();
      ctx.scale(-1, 1);  // Mirror horizontally
      ctx.drawImage(this.videoElement, -videoWidth, 0, videoWidth, videoHeight);
      ctx.restore();

      // Compress to JPEG with 75% quality
      const base64 = this.canvasElement.toDataURL('image/jpeg', 0.75);

      console.log('[CameraCapture] Frame captured and compressed');
      console.log('[CameraCapture] Base64 length:', base64.length, 'bytes');

      return base64;
    } catch (err) {
      console.error('[CameraCapture] Error capturing frame:', err);
      throw err;
    }
  }

  /**
   * Stop camera and release all resources
   * @returns {Promise<void>}
   */
  async stop() {
    if (!this.stream) {
      console.log('[CameraCapture] No stream to stop');
      return;
    }

    try {
      console.log('[CameraCapture] Stopping camera...');

      // Stop all tracks
      this.stream.getTracks().forEach(track => {
        console.log('[CameraCapture] Stopping track:', track.kind, track.readyState);
        track.stop();
      });

      // Clear video element
      this.videoElement.srcObject = null;
      this.stream = null;
      this.isRunning = false;

      console.log('[CameraCapture] Camera stopped successfully');
    } catch (err) {
      console.error('[CameraCapture] Error stopping camera:', err);
      throw err;
    }
  }

  /**
   * Check if camera is currently running
   * @returns {boolean}
   */
  getIsRunning() {
    return this.isRunning;
  }

  /**
   * Get current permission status
   * @returns {Promise<string>} 'granted', 'denied', 'prompt', or 'unknown'
   */
  async getPermissionStatus() {
    if (!navigator.permissions) {
      console.warn('[CameraCapture] Permissions API not available');
      return 'unknown';
    }

    try {
      const permissionStatus = await navigator.permissions.query({ name: 'camera' });
      this.permissionStatus = permissionStatus.state;
      console.log('[CameraCapture] Permission status:', this.permissionStatus);
      return this.permissionStatus;
    } catch (err) {
      console.error('[CameraCapture] Error checking permission status:', err);
      return 'unknown';
    }
  }

  /**
   * Register callback for permission state changes
   * @param {Function} callback Function to call when permission state changes
   */
  onPermissionChange(callback) {
    this.onPermissionChangeCallback = callback;
  }

  /**
   * Watch for permission changes (private method)
   * @private
   */
  _watchPermissionChanges() {
    if (!navigator.permissions) {
      console.warn('[CameraCapture] Permissions API not available - cannot watch for changes');
      return;
    }

    navigator.permissions.query({ name: 'camera' }).then((permissionStatus) => {
      this.permissionStatus = permissionStatus.state;
      console.log('[CameraCapture] Initial permission status:', this.permissionStatus);

      permissionStatus.addEventListener('change', () => {
        this.permissionStatus = permissionStatus.state;
        console.log('[CameraCapture] Permission status changed:', this.permissionStatus);

        if (this.onPermissionChangeCallback) {
          this.onPermissionChangeCallback(this.permissionStatus);
        }
      });
    }).catch((err) => {
      console.warn('[CameraCapture] Could not watch permission changes:', err);
    });
  }
}

// Export for use in modules
if (typeof module !== 'undefined' && module.exports) {
  module.exports = CameraCapture;
}
