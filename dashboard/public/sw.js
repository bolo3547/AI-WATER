const CACHE_NAME = 'lwsc-nrw-v2';
const OFFLINE_URL = '/offline.html';

// Assets to cache immediately
const PRECACHE_ASSETS = [
  '/',
  '/login',
  '/manifest.json',
  '/lwsc-logo.png',
  '/icons/icon-192.png',
  '/icons/icon-512.png',
  '/offline.html'
];

// Install event - cache essential assets
self.addEventListener('install', (event) => {
  event.waitUntil(
    caches.open(CACHE_NAME).then((cache) => {
      console.log('LWSC NRW: Caching essential assets');
      return cache.addAll(PRECACHE_ASSETS);
    })
  );
  self.skipWaiting();
});

// Activate event - clean up old caches
self.addEventListener('activate', (event) => {
  event.waitUntil(
    caches.keys().then((cacheNames) => {
      return Promise.all(
        cacheNames
          .filter((name) => name !== CACHE_NAME)
          .map((name) => caches.delete(name))
      );
    })
  );
  self.clients.claim();
});

// Fetch event - network first, fallback to cache
self.addEventListener('fetch', (event) => {
  // Skip non-GET requests
  if (event.request.method !== 'GET') return;

  // Skip chrome-extension and other non-http(s) URLs
  const url = new URL(event.request.url);
  if (!url.protocol.startsWith('http')) {
    return;
  }

  // Skip API calls - always go to network
  if (event.request.url.includes('/api/')) {
    return;
  }

  event.respondWith(
    fetch(event.request)
      .then((response) => {
        // Clone response for caching
        const responseClone = response.clone();
        caches.open(CACHE_NAME).then((cache) => {
          cache.put(event.request, responseClone);
        });
        return response;
      })
      .catch(() => {
        // Network failed, try cache
        return caches.match(event.request).then((cachedResponse) => {
          if (cachedResponse) {
            return cachedResponse;
          }
          // Return offline page for navigation requests
          if (event.request.mode === 'navigate') {
            return caches.match(OFFLINE_URL);
          }
          return new Response('Offline', { status: 503 });
        });
      })
  );
});

// Handle push notifications with enhanced options
self.addEventListener('push', (event) => {
  const data = event.data?.json() || {};
  
  // Determine notification priority and styling
  const priority = data.priority || 'medium';
  const type = data.type || 'info';
  
  // Different vibration patterns for different priorities
  const vibrationPatterns = {
    high: [200, 100, 200, 100, 200], // Urgent triple buzz
    medium: [100, 50, 100],          // Standard double buzz  
    low: [100]                        // Single soft buzz
  };
  
  // Notification icons based on type
  const iconMap = {
    alert: '/icons/alert-icon.png',
    warning: '/icons/warning-icon.png', 
    success: '/icons/success-icon.png',
    info: '/icons/icon-192.png'
  };
  
  const options = {
    body: data.body || 'New notification from LWSC NRW System',
    icon: iconMap[type] || '/icons/icon-192.png',
    badge: '/lwsc-logo.png',
    vibrate: vibrationPatterns[priority] || vibrationPatterns.medium,
    tag: data.tag || `lwsc-${Date.now()}`, // Prevents duplicate notifications
    renotify: data.renotify || false,
    requireInteraction: priority === 'high', // High priority stays until dismissed
    silent: data.silent || false,
    data: {
      url: data.url || '/notifications',
      type: type,
      priority: priority,
      id: data.id,
      source: data.source
    },
    actions: data.actions || [
      { action: 'view', title: '👁️ View Details', icon: '/icons/view.png' },
      { action: 'action', title: '⚡ Take Action', icon: '/icons/action.png' },
      { action: 'dismiss', title: '✖️ Dismiss', icon: '/icons/dismiss.png' }
    ]
  };
  
  // For critical alerts, add extra emphasis
  if (priority === 'high' && type === 'alert') {
    options.body = `🚨 CRITICAL: ${data.body}`;
    options.requireInteraction = true;
  }

  event.waitUntil(
    self.registration.showNotification(data.title || 'LWSC NRW Alert', options)
  );
});

// Handle notification click with action routing
self.addEventListener('notificationclick', (event) => {
  event.notification.close();
  
  const notificationData = event.notification.data || {};
  
  // Handle different actions
  if (event.action === 'dismiss') return;
  
  let targetUrl = '/notifications';
  
  if (event.action === 'view' || event.action === '') {
    targetUrl = notificationData.url || '/notifications';
  } else if (event.action === 'action') {
    // Route to actions page for the specific alert
    targetUrl = `/actions?id=${notificationData.id || ''}`;
  }

  event.waitUntil(
    clients.matchAll({ type: 'window', includeUncontrolled: true })
      .then((windowClients) => {
        // Check if a window is already open
        for (const client of windowClients) {
          if (client.url.includes(self.location.origin)) {
            client.focus();
            return client.navigate(targetUrl);
          }
        }
        // No window open, open new one
        return clients.openWindow(targetUrl);
      })
  );
});

// Background sync for offline notifications
self.addEventListener('sync', (event) => {
  if (event.tag === 'sync-notifications') {
    event.waitUntil(syncNotifications());
  }
});

async function syncNotifications() {
  try {
    const response = await fetch('/api/notifications/pending');
    const data = await response.json();
    
    if (data.notifications && data.notifications.length > 0) {
      // Show batch notification for multiple pending alerts
      if (data.notifications.length > 3) {
        await self.registration.showNotification('LWSC NRW - Multiple Alerts', {
          body: `You have ${data.notifications.length} pending notifications`,
          icon: '/icons/icon-192.png',
          badge: '/lwsc-logo.png',
          data: { url: '/notifications' }
        });
      } else {
        // Show individual notifications
        for (const notification of data.notifications) {
          await self.registration.showNotification(notification.title, {
            body: notification.message,
            icon: '/icons/icon-192.png',
            badge: '/lwsc-logo.png',
            data: { url: notification.actionUrl || '/notifications' }
          });
        }
      }
    }
  } catch (error) {
    console.log('Background sync failed:', error);
  }
}
