// Service Worker for Elson Wealth Management PWA
const CACHE_NAME = 'elson-pwa-v1.0.0';

// Assets to cache on install
const STATIC_ASSETS = [
  '/',
  '/index.html',
  '/manifest.json',
  '/assets/icons/icon-192x192.png',
  '/assets/icons/icon-512x512.png',
  '/assets/images/logo.png'
];

// Install handler: cache static assets
self.addEventListener('install', (event) => {
  event.waitUntil(
    caches.open(CACHE_NAME)
      .then((cache) => {
        return cache.addAll(STATIC_ASSETS);
      })
      .then(() => {
        // Skip waiting forces the waiting service worker to become active
        return self.skipWaiting();
      })
  );
});

// Activate handler: clean up old caches
self.addEventListener('activate', (event) => {
  event.waitUntil(
    caches.keys().then((cacheNames) => {
      return Promise.all(
        cacheNames.filter((cacheName) => {
          return cacheName !== CACHE_NAME;
        }).map((cacheName) => {
          return caches.delete(cacheName);
        })
      );
    }).then(() => {
      // Claims control over all clients within scope
      return self.clients.claim();
    })
  );
});

// Fetch handler: serve from cache, falling back to network
self.addEventListener('fetch', (event) => {
  // Skip cross-origin requests
  if (!event.request.url.startsWith(self.location.origin)) {
    return;
  }
  
  // Skip API requests (should not be cached)
  if (event.request.url.includes('/api/')) {
    return;
  }
  
  // Network first strategy for HTML requests (always get fresh document)
  if (event.request.mode === 'navigate' || 
      (event.request.method === 'GET' && 
       event.request.headers.get('accept').includes('text/html'))) {
    event.respondWith(
      fetch(event.request)
        .catch(() => {
          return caches.match(event.request)
            .then((cachedResponse) => {
              if (cachedResponse) {
                return cachedResponse;
              }
              // If no cached HTML, return the offline page
              return caches.match('/offline.html');
            });
        })
    );
    return;
  }
  
  // Cache first, network fallback for other assets
  event.respondWith(
    caches.match(event.request)
      .then((cachedResponse) => {
        if (cachedResponse) {
          return cachedResponse;
        }
        
        return fetch(event.request)
          .then((response) => {
            // Don't cache non-successful responses
            if (!response || response.status !== 200 || response.type !== 'basic') {
              return response;
            }
            
            // Clone the response as it can only be consumed once
            const responseToCache = response.clone();
            
            caches.open(CACHE_NAME)
              .then((cache) => {
                cache.put(event.request, responseToCache);
              });
              
            return response;
          })
          .catch(() => {
            // Fallback for image requests
            if (event.request.url.match(/\.(jpg|jpeg|png|gif|svg)$/)) {
              return caches.match('/assets/images/offline-image.svg');
            }
            
            return new Response('Network error', {
              status: 408,
              headers: { 'Content-Type': 'text/plain' }
            });
          });
      })
  );
});

// Listen for push notifications
self.addEventListener('push', (event) => {
  if (!event.data) return;
  
  const data = event.data.json();
  
  const title = data.title || 'Elson Wealth';
  const options = {
    body: data.body || 'New notification',
    icon: '/assets/icons/icon-192x192.png',
    badge: '/assets/icons/badge-72x72.png',
    data: {
      url: data.url || '/'
    },
    actions: data.actions || []
  };
  
  event.waitUntil(
    self.registration.showNotification(title, options)
  );
});

// Handle notification click
self.addEventListener('notificationclick', (event) => {
  event.notification.close();
  
  // Open the URL from the notification data if available
  if (event.notification.data && event.notification.data.url) {
    event.waitUntil(
      clients.openWindow(event.notification.data.url)
    );
  }
});

// Handle the "sync" event for background sync
self.addEventListener('sync', (event) => {
  if (event.tag === 'elson-sync-transactions') {
    event.waitUntil(syncTransactions());
  }
});

// Example background sync function
async function syncTransactions() {
  try {
    // Fetch pending transactions from IndexedDB
    const db = await openTransactionsDatabase();
    const pendingTransactions = await getPendingTransactions(db);
    
    // Process each pending transaction
    for (const transaction of pendingTransactions) {
      await sendTransactionToServer(transaction);
      await markTransactionAsSynced(db, transaction.id);
    }
    
    // Show success notification
    if (pendingTransactions.length > 0) {
      self.registration.showNotification('Elson Wealth', {
        body: `${pendingTransactions.length} transactions synced successfully`,
        icon: '/assets/icons/icon-192x192.png'
      });
    }
  } catch (error) {
    console.error('Transaction sync failed:', error);
  }
}

// These functions would be implemented in a real app
function openTransactionsDatabase() {
  return Promise.resolve({});
}

function getPendingTransactions(db) {
  return Promise.resolve([]);
}

function sendTransactionToServer(transaction) {
  return Promise.resolve();
}

function markTransactionAsSynced(db, id) {
  return Promise.resolve();
}