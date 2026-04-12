// BloodLife - Service Worker for Push Notifications
const CACHE_NAME = 'bloodlife-v1';
const urlsToCache = [
    '/',
    '/static/js/notification-manager.js',
    '/static/js/live-map.js'
];

// Install service worker
self.addEventListener('install', event => {
    event.waitUntil(
        caches.open(CACHE_NAME)
            .then(cache => cache.addAll(urlsToCache))
    );
});

// Fetch handler
self.addEventListener('fetch', event => {
    event.respondWith(
        caches.match(event.request)
            .then(response => {
                if (response) {
                    return response;
                }
                return fetch(event.request);
            })
    );
});

// Push notification handler
self.addEventListener('push', event => {
    const data = event.data ? event.data.json() : {};
    
    const title = data.title || 'BloodLife Notification';
    const options = {
        body: data.message || 'New update',
        icon: '/static/images/notification-icon.png',
        badge: '/static/images/badge-icon.png',
        tag: data.type || 'general',
        requireInteraction: data.urgency === 'critical',
        vibrate: data.vibration || [200, 100, 200],
        actions: [
            {
                action: 'view',
                title: 'View Details',
                icon: '/static/images/view-icon.png'
            },
            {
                action: 'dismiss',
                title: 'Dismiss',
                icon: '/static/images/dismiss-icon.png'
            }
        ],
        data: {
            url: data.action_url || '/requests/track/'
        }
    };
    
    event.waitUntil(
        self.registration.showNotification(title, options)
    );
});

// Notification click handler
self.addEventListener('notificationclick', event => {
    event.notification.close();
    
    if (event.action === 'dismiss') {
        return;
    }
    
    const urlToOpen = event.notification.data.url || '/requests/track/';
    
    event.waitUntil(
        clients.matchAll({ type: 'window' })
            .then(clientList => {
                // Check if window is already open
                for (let client of clientList) {
                    if (client.url === urlToOpen && 'focus' in client) {
                        return client.focus();
                    }
                }
                // Open new window
                if (clients.openWindow) {
                    return clients.openWindow(urlToOpen);
                }
            })
    );
});
