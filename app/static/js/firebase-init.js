/**
 * Firebase Cloud Messaging Initialization
 * ========================================
 * Handles FCM token registration, permission requests, and foreground notifications.
 */

// Firebase configuration (will be populated from backend)
let firebaseConfig = null;
let messaging = null;
let currentToken = null;

/**
 * Initialize Firebase with configuration from backend
 */
async function initializeFirebase() {
    try {
        // Fetch Firebase config from backend
        const response = await fetch('/api/notifications/firebase-config');
        if (!response.ok) {
            console.error('Failed to fetch Firebase config');
            return false;
        }

        firebaseConfig = await response.json();
        
        // Initialize Firebase
        if (!firebase.apps.length) {
            firebase.initializeApp(firebaseConfig);
        }

        // Get messaging instance
        messaging = firebase.messaging();
        
        console.log('Firebase initialized successfully');
        return true;
    } catch (error) {
        console.error('Error initializing Firebase:', error);
        return false;
    }
}

/**
 * Request notification permission and register FCM token
 */
async function requestNotificationPermission() {
    try {
        // Check if notifications are supported
        if (!('Notification' in window)) {
            console.warn('This browser does not support notifications');
            return false;
        }

        // Check current permission
        if (Notification.permission === 'granted') {
            console.log('Notification permission already granted');
            return await registerFCMToken();
        }

        if (Notification.permission === 'denied') {
            console.warn('Notification permission denied');
            return false;
        }

        // Request permission
        const permission = await Notification.requestPermission();
        
        if (permission === 'granted') {
            console.log('Notification permission granted');
            return await registerFCMToken();
        } else {
            console.warn('Notification permission denied by user');
            return false;
        }
    } catch (error) {
        console.error('Error requesting notification permission:', error);
        return false;
    }
}

/**
 * Register FCM token with backend
 */
async function registerFCMToken() {
    try {
        if (!messaging) {
            console.error('Firebase Messaging not initialized');
            return false;
        }

        // Get FCM token
        currentToken = await messaging.getToken({
            vapidKey: firebaseConfig.vapidKey
        });

        if (currentToken) {
            console.log('FCM Token:', currentToken);

            // Send token to backend
            const response = await fetch('/api/notifications/register-token', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    token: currentToken,
                    device_type: getBrowserName(),
                    user_agent: navigator.userAgent
                })
            });

            if (response.ok) {
                console.log('FCM token registered successfully');
                // Store in localStorage to avoid asking again
                localStorage.setItem('fcm_token_registered', 'true');
                localStorage.setItem('fcm_token', currentToken);
                return true;
            } else {
                console.error('Failed to register FCM token with backend');
                return false;
            }
        } else {
            console.warn('No FCM token available');
            return false;
        }
    } catch (error) {
        console.error('Error registering FCM token:', error);
        return false;
    }
}

/**
 * Handle foreground messages (when app is open)
 */
function setupForegroundMessageHandler() {
    if (!messaging) return;

    messaging.onMessage((payload) => {
        console.log('Foreground message received:', payload);

        const title = payload.notification?.title || payload.data?.title || 'Smart HRMS';
        const body = payload.notification?.body || payload.data?.message || '';
        const icon = payload.notification?.icon || '/static/images/hrms-icon.png';
        const url = payload.data?.url || payload.fcmOptions?.link || null;
        const notificationId = payload.data?.notificationId || null;

        // Show toast notification
        showToastNotification(title, body, icon, url, notificationId);

        // Update notification bell
        updateNotificationBell();

        // Play notification sound (optional)
        playNotificationSound();
    });
}

/**
 * Show toast notification (in-app)
 */
function showToastNotification(title, body, icon, url, notificationId) {
    // Create toast element
    const toastHtml = `
        <div class="toast align-items-center border-0 shadow-lg" role="alert" aria-live="assertive" aria-atomic="true" 
             data-notification-id="${notificationId || ''}" data-url="${url || ''}">
            <div class="d-flex">
                <div class="toast-body d-flex align-items-center gap-3">
                    <img src="${icon}" alt="" width="32" height="32" class="rounded">
                    <div class="flex-grow-1">
                        <div class="fw-bold small">${title}</div>
                        <div class="text-muted small">${body}</div>
                    </div>
                </div>
                <button type="button" class="btn-close me-2 m-auto" data-bs-dismiss="toast" aria-label="Close"></button>
            </div>
        </div>
    `;

    // Add to toast container
    let toastContainer = document.getElementById('toast-container');
    if (!toastContainer) {
        toastContainer = document.createElement('div');
        toastContainer.id = 'toast-container';
        toastContainer.className = 'toast-container position-fixed top-0 end-0 p-3';
        toastContainer.style.zIndex = '9999';
        document.body.appendChild(toastContainer);
    }

    const toastElement = document.createElement('div');
    toastElement.innerHTML = toastHtml;
    const toast = toastElement.firstElementChild;
    toastContainer.appendChild(toast);

    // Initialize Bootstrap toast
    const bsToast = new bootstrap.Toast(toast, {
        autohide: true,
        delay: 5000
    });

    // Add click handler
    toast.addEventListener('click', function(e) {
        if (!e.target.classList.contains('btn-close')) {
            const url = this.dataset.url;
            const notifId = this.dataset.notificationId;
            
            if (notifId) {
                markNotificationAsClicked(notifId);
            }
            
            if (url && url !== 'null' && url !== '') {
                window.location.href = url;
            }
        }
    });

    // Show toast
    bsToast.show();

    // Remove from DOM after hidden
    toast.addEventListener('hidden.bs.toast', function() {
        this.remove();
    });
}

/**
 * Play notification sound
 */
function playNotificationSound() {
    try {
        const audio = new Audio('/static/sounds/notification.mp3');
        audio.volume = 0.5;
        audio.play().catch(e => console.log('Could not play notification sound:', e));
    } catch (error) {
        // Silently fail if sound cannot be played
    }
}

/**
 * Update notification bell with latest count
 */
async function updateNotificationBell() {
    try {
        const response = await fetch('/api/notifications/unread-count');
        if (response.ok) {
            const data = await response.json();
            const badge = document.querySelector('.notification-badge');
            if (badge) {
                badge.textContent = data.count;
                badge.style.display = data.count > 0 ? 'inline-block' : 'none';
            }
        }
    } catch (error) {
        console.error('Error updating notification bell:', error);
    }
}

/**
 * Mark notification as clicked
 */
async function markNotificationAsClicked(notificationId) {
    try {
        await fetch(`/api/notifications/${notificationId}/clicked`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            }
        });
    } catch (error) {
        console.error('Error marking notification as clicked:', error);
    }
}

/**
 * Get browser name
 */
function getBrowserName() {
    const userAgent = navigator.userAgent;
    if (userAgent.includes('Chrome')) return 'chrome';
    if (userAgent.includes('Firefox')) return 'firefox';
    if (userAgent.includes('Safari')) return 'safari';
    if (userAgent.includes('Edge')) return 'edge';
    return 'unknown';
}

/**
 * Check if user has granted permission before
 */
function hasGrantedPermission() {
    return localStorage.getItem('fcm_token_registered') === 'true';
}

/**
 * Show permission prompt modal
 */
function showPermissionPrompt() {
    // Check if already granted or denied
    if (Notification.permission === 'granted') {
        registerFCMToken();
        return;
    }

    if (Notification.permission === 'denied') {
        console.warn('Notifications blocked by user');
        return;
    }

    // Check if we've already asked
    if (hasGrantedPermission()) {
        return;
    }

    // Show custom modal
    const modalHtml = `
        <div class="modal fade" id="notificationPermissionModal" tabindex="-1" aria-hidden="true">
            <div class="modal-dialog modal-dialog-centered">
                <div class="modal-content">
                    <div class="modal-header border-0">
                        <h5 class="modal-title fw-bold">
                            <i class="bi bi-bell text-primary me-2"></i>
                            Enable Notifications
                        </h5>
                        <button type="button" class="btn-close" data-bs-dismiss="modal" aria-label="Close"></button>
                    </div>
                    <div class="modal-body">
                        <p class="mb-3">Stay updated with important events:</p>
                        <ul class="text-muted small">
                            <li>Leave request approvals</li>
                            <li>Attendance updates</li>
                            <li>Shift changes</li>
                            <li>Payroll notifications</li>
                            <li>Company announcements</li>
                        </ul>
                        <p class="text-muted small mb-0">You can change this anytime in your browser settings.</p>
                    </div>
                    <div class="modal-footer border-0">
                        <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Not Now</button>
                        <button type="button" class="btn btn-primary" id="enableNotificationsBtn">
                            <i class="bi bi-bell-fill me-1"></i>Enable Notifications
                        </button>
                    </div>
                </div>
            </div>
        </div>
    `;

    // Add modal to page
    const modalContainer = document.createElement('div');
    modalContainer.innerHTML = modalHtml;
    document.body.appendChild(modalContainer);

    // Show modal
    const modal = new bootstrap.Modal(document.getElementById('notificationPermissionModal'));
    modal.show();

    // Handle enable button click
    document.getElementById('enableNotificationsBtn').addEventListener('click', async function() {
        modal.hide();
        const granted = await requestNotificationPermission();
        if (granted) {
            showToastNotification(
                'Notifications Enabled',
                'You will now receive push notifications',
                '/static/images/hrms-icon.png',
                null,
                null
            );
        }
    });

    // Mark that we've shown the prompt
    localStorage.setItem('notification_prompt_shown', 'true');
}

// Initialize on page load
document.addEventListener('DOMContentLoaded', async function() {
    // Initialize Firebase
    const initialized = await initializeFirebase();
    
    if (initialized) {
        // Setup foreground message handler
        setupForegroundMessageHandler();

        // Check URL parameter for first login flag
        const urlParams = new URLSearchParams(window.location.search);
        const showPrompt = urlParams.get('show_notification_prompt') === '1';
        
        // Check sessionStorage for first login flag
        const isFirstLogin = sessionStorage.getItem('first_login') === 'true';
        const hasAskedBefore = localStorage.getItem('notification_prompt_shown') === 'true';
        
        // Show permission prompt if first login or URL parameter present
        if ((showPrompt || isFirstLogin) && !hasAskedBefore && Notification.permission === 'default') {
            // Clear URL parameter
            if (showPrompt) {
                window.history.replaceState({}, document.title, window.location.pathname);
            }
            setTimeout(showPermissionPrompt, 2000);
        } else if (Notification.permission === 'granted' && !hasGrantedPermission()) {
            // Auto-register if permission already granted
            registerFCMToken();
        }
    }
});

// Listen for messages from service worker
navigator.serviceWorker?.addEventListener('message', (event) => {
    if (event.data && event.data.type === 'NOTIFICATION_CLICKED') {
        const notificationId = event.data.notificationId;
        if (notificationId) {
            markNotificationAsClicked(notificationId);
            updateNotificationBell();
        }
    }
});
