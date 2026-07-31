/**
 * Firebase Cloud Messaging Service Worker
 * ========================================
 * This service worker handles background push notifications for Smart HRMS.
 * It runs independently of the main application and can receive notifications
 * even when the HRMS website is not open.
 */

// Import Firebase scripts
importScripts('https://www.gstatic.com/firebasejs/10.7.1/firebase-app-compat.js');
importScripts('https://www.gstatic.com/firebasejs/10.7.1/firebase-messaging-compat.js');

// Firebase configuration
// These values will be replaced with actual Firebase project credentials
const firebaseConfig = {
  apiKey: "YOUR_API_KEY",
  authDomain: "YOUR_AUTH_DOMAIN",
  projectId: "YOUR_PROJECT_ID",
  storageBucket: "YOUR_STORAGE_BUCKET",
  messagingSenderId: "YOUR_MESSAGING_SENDER_ID",
  appId: "YOUR_APP_ID"
};

// Initialize Firebase
firebase.initializeApp(firebaseConfig);

// Get Firebase Messaging instance
const messaging = firebase.messaging();

// Handle background messages
messaging.onBackgroundMessage((payload) => {
  console.log('[firebase-messaging-sw.js] Received background message:', payload);

  // Extract notification data
  const notificationTitle = payload.notification?.title || payload.data?.title || 'Smart HRMS Notification';
  const notificationOptions = {
    body: payload.notification?.body || payload.data?.message || '',
    icon: payload.notification?.icon || '/static/images/hrms-icon.png',
    badge: '/static/images/badge-icon.png',
    tag: payload.data?.tag || 'hrms-notification',
    requireInteraction: false,
    data: {
      url: payload.data?.url || payload.fcmOptions?.link || '/',
      module: payload.data?.module || 'dashboard',
      notificationId: payload.data?.notificationId || null,
      timestamp: Date.now()
    },
    actions: [
      {
        action: 'open',
        title: 'Open',
        icon: '/static/images/open-icon.png'
      },
      {
        action: 'close',
        title: 'Dismiss',
        icon: '/static/images/close-icon.png'
      }
    ]
  };

  // Show notification
  return self.registration.showNotification(notificationTitle, notificationOptions);
});

// Handle notification click
self.addEventListener('notificationclick', (event) => {
  console.log('[Service Worker] Notification click received:', event);

  event.notification.close();

  const urlToOpen = event.notification.data?.url || '/';
  const notificationId = event.notification.data?.notificationId;

  if (event.action === 'close') {
    // User clicked dismiss, do nothing
    return;
  }

  // Default action or 'open' action
  event.waitUntil(
    clients.matchAll({
      type: 'window',
      includeUncontrolled: true
    }).then((clientList) => {
      // Check if HRMS is already open
      for (let i = 0; i < clientList.length; i++) {
        const client = clientList[i];
        if (client.url.includes(urlToOpen) && 'focus' in client) {
          // Window exists, focus it
          return client.focus().then(client => {
            // Send message to mark notification as clicked
            if (notificationId) {
              client.postMessage({
                type: 'NOTIFICATION_CLICKED',
                notificationId: notificationId
              });
            }
            return client;
          });
        }
      }
      // No existing window, open new one
      if (clients.openWindow) {
        return clients.openWindow(urlToOpen).then(client => {
          // Send message to mark notification as clicked
          if (notificationId && client) {
            client.postMessage({
              type: 'NOTIFICATION_CLICKED',
              notificationId: notificationId
            });
          }
          return client;
        });
      }
    })
  );
});

// Handle push event
self.addEventListener('push', (event) => {
  console.log('[Service Worker] Push received:', event);
  
  if (event.data) {
    try {
      const data = event.data.json();
      console.log('[Service Worker] Push data:', data);
      
      // Data is handled by onBackgroundMessage
    } catch (e) {
      console.error('[Service Worker] Error parsing push data:', e);
    }
  }
});

// Service Worker installation
self.addEventListener('install', (event) => {
  console.log('[Service Worker] Installing service worker...');
  self.skipWaiting();
});

// Service Worker activation
self.addEventListener('activate', (event) => {
  console.log('[Service Worker] Activating service worker...');
  event.waitUntil(clients.claim());
});

// Handle messages from the main application
self.addEventListener('message', (event) => {
  console.log('[Service Worker] Message received:', event.data);
  
  if (event.data && event.data.type === 'UPDATE_CONFIG') {
    // Allow dynamic config update from main app
    console.log('[Service Worker] Config update requested');
  }
});
