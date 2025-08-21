// NEXORA CRM Service Worker - PWA Offline Functionality
const CACHE_NAME = 'nexora-crm-v1.0';
const urlsToCache = [
  '/',
  '/pages/1_Dashboard.py',
  '/pages/investor_clients.py',
  '/pages/leads.py',
  '/assets/style.css',
  '/assets/logo.png',
  '/manifest.json'
];

// Install event - cache resources
self.addEventListener('install', event => {
  event.waitUntil(
    caches.open(CACHE_NAME)
      .then(cache => {
        console.log('NEXORA CRM cache opened');
        return cache.addAll(urlsToCache);
      })
  );
});

// Fetch event - serve from cache when offline
self.addEventListener('fetch', event => {
  event.respondWith(
    caches.match(event.request)
      .then(response => {
        // Return cached version or fetch from network
        if (response) {
          return response;
        }
        return fetch(event.request);
      }
    )
  );
});

// Activate event - clean up old caches
self.addEventListener('activate', event => {
  event.waitUntil(
    caches.keys().then(cacheNames => {
      return Promise.all(
        cacheNames.map(cacheName => {
          if (cacheName !== CACHE_NAME) {
            console.log('Deleting old cache:', cacheName);
            return caches.delete(cacheName);
          }
        })
      );
    })
  );
});

// Background sync for offline deal submissions
self.addEventListener('sync', event => {
  if (event.tag === 'background-sync-deals') {
    event.waitUntil(doBackgroundSync());
  }
});

function doBackgroundSync() {
  // Sync any offline deal submissions when back online
  return Promise.resolve(); // Implement actual sync logic
}

// Push notifications for deal alerts
self.addEventListener('push', event => {
  const options = {
    body: event.data ? event.data.text() : 'New deal alert from NEXORA CRM!',
    icon: '/assets/logo.png',
    badge: '/assets/logo.png',
    vibrate: [100, 50, 100],
    data: {
      dateOfArrival: Date.now(),
      primaryKey: '1'
    },
    actions: [
      {
        action: 'explore',
        title: 'View Deal',
        icon: '/assets/logo.png'
      },
      {
        action: 'close',
        title: 'Close',
        icon: '/assets/logo.png'
      }
    ]
  };

  event.waitUntil(
    self.registration.showNotification('NEXORA CRM Deal Alert', options)
  );
});

// Handle notification clicks
self.addEventListener('notificationclick', event => {
  event.notification.close();

  if (event.action === 'explore') {
    // Open the app to the deal
    event.waitUntil(
      clients.openWindow('/')
    );
  }
});
