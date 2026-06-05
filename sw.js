const CACHE = 'maraichage-v6';
const FONT_CACHE = 'maraichage-fonts-v6';
const APP_SHELL = [
  '/meteo-rique-maraichage/',
  '/meteo-rique-maraichage/index.html',
  '/meteo-rique-maraichage/offline.html',
];

// Domaines API — jamais mis en cache, réseau uniquement
const API_HOSTS = new Set([
  'api.open-meteo.com',
  'geocoding-api.open-meteo.com',
  'nominatim.openstreetmap.org',
]);

self.addEventListener('install', e => {
  e.waitUntil(
    caches.open(CACHE).then(c => c.addAll(APP_SHELL))
  );
  self.skipWaiting();
});

self.addEventListener('activate', e => {
  e.waitUntil(
    caches.keys()
      .then(keys => Promise.all(
        keys
          .filter(k => k !== CACHE && k !== FONT_CACHE)
          .map(k => caches.delete(k))
      ))
      .then(() => self.clients.claim())
  );
});

// Permet à l'UI de déclencher la mise à jour via postMessage
self.addEventListener('message', e => {
  if (e.data?.type === 'SKIP_WAITING') self.skipWaiting();
});

self.addEventListener('fetch', e => {
  const { request } = e;
  const url = new URL(request.url);

  // Laisser passer les appels API météo — toujours fraîches
  if (API_HOSTS.has(url.hostname)) return;

  // Polices Google Fonts — stale-while-revalidate
  if (url.hostname === 'fonts.googleapis.com' || url.hostname === 'fonts.gstatic.com') {
    e.respondWith(
      caches.open(FONT_CACHE).then(c =>
        c.match(request).then(cached => {
          const network = fetch(request).then(res => {
            if (res.ok) c.put(request, res.clone());
            return res;
          });
          return cached ?? network;
        })
      )
    );
    return;
  }

  // Requêtes de navigation — réseau d'abord, fallback offline
  if (request.mode === 'navigate') {
    e.respondWith(
      fetch(request)
        .then(res => {
          if (res.ok) caches.open(CACHE).then(c => c.put(request, res.clone()));
          return res;
        })
        .catch(() => caches.match('/meteo-rique-maraichage/offline.html'))
    );
    return;
  }

  // Reste (assets statiques) — cache d'abord, réseau en fallback
  e.respondWith(
    caches.match(request).then(cached => {
      if (cached) return cached;
      return fetch(request).then(res => {
        if (res.ok) caches.open(CACHE).then(c => c.put(request, res.clone()));
        return res;
      });
    })
  );
});
