const CACHE_NAME = 'bloodlife-v1';
const urlsToCache = [
  '/',
  '/static/css/home.css',
  '/static/js/home.js',
  '/static/js/animations.js',
  '/static/js/app.js',
];

self.addEventListener('install', function(event) {
  // Perform install steps
  event.waitUntil(
    caches.open(CACHE_NAME)
      .then(function(cache) {
        console.log('Opened cache');
        return cache.addAll(urlsToCache);
      })
  );
});

self.addEventListener('fetch', function(event) {
  event.respondWith(
    caches.match(event.request)
      .then(function(response) {
        // Return cached response or fetch from network
        if (response) {
          return response;
        }
        return fetch(event.request);
      }
    )
  );
});