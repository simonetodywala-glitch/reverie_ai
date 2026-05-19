const CACHE = 'reverie-v1';

const SHELL = [
  '/index.html',
  '/pages/onboarding.html',
  '/pages/journal.html',
  '/pages/dream.html',
  '/pages/dreams.html',
  '/pages/insights.html',
  '/pages/winddown.html',
  '/pages/lucid.html',
  '/pages/profile.html',
  '/js/api.js',
  '/js/app.js',
  '/js/auth.js',
  '/js/firebase.js',
  '/js/sleepEngine.js',
  '/js/soundscapes.js',
  '/offline.html',
];

// Cache shell on install
self.addEventListener('install', e => {
  e.waitUntil(
    caches.open(CACHE).then(c => c.addAll(SHELL)).then(() => self.skipWaiting())
  );
});

// Take over immediately
self.addEventListener('activate', e => {
  e.waitUntil(
    caches.keys().then(keys =>
      Promise.all(keys.filter(k => k !== CACHE).map(k => caches.delete(k)))
    ).then(() => self.clients.claim())
  );
});

// Network first for API calls, cache first for shell, offline page for failed navigation
self.addEventListener('fetch', e => {
  const { request } = e;
  const url = new URL(request.url);

  // Skip non-GET and cross-origin API/Firebase calls
  if (request.method !== 'GET') return;
  if (!url.origin.includes(self.location.origin)) return;

  // Navigation: try network, fall back to cached page, then offline
  if (request.mode === 'navigate') {
    e.respondWith(
      fetch(request)
        .catch(() => caches.match(request).then(r => r || caches.match('/offline.html')))
    );
    return;
  }

  // Everything else: cache first, then network
  e.respondWith(
    caches.match(request).then(cached => {
      const networkFetch = fetch(request).then(res => {
        if (res.ok) {
          const clone = res.clone();
          caches.open(CACHE).then(c => c.put(request, clone));
        }
        return res;
      });
      return cached || networkFetch;
    })
  );
});
