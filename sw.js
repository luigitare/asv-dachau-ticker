// Minimaler Service Worker: App-Shell cachen,
// Daten/Ticker IMMER live aus dem Netz holen.
const CACHE = "asv-dachau-v44";
const APP_SHELL = ["./", "./index.html", "./manifest.webmanifest", "./logo_c.svg"];

self.addEventListener("install", (event) => {
  event.waitUntil(caches.open(CACHE).then((c) => c.addAll(APP_SHELL)));
  self.skipWaiting();
});

self.addEventListener("activate", (event) => {
  event.waitUntil(
    caches.keys().then((keys) =>
      Promise.all(keys.filter((k) => k !== CACHE).map((k) => caches.delete(k)))
    )
  );
  self.clients.claim();
});

self.addEventListener("fetch", (event) => {
  const url = new URL(event.request.url);
  // BVV-Daten & Live-Ticker: immer live (nie cachen!)
  if (url.hostname.includes("volleyball-bayern.de") || url.hostname.includes("sams-ticker.de")) {
    return;
  }
  // App-Shell: erst Netz, im Hintergrund Cache auffrischen (stale-while-revalidate)
  event.respondWith(
    caches.match(event.request).then((cached) => {
      const fetchPromise = fetch(event.request).then((response) => {
        if (response && response.ok) {
          const copy = response.clone();
          caches.open(CACHE).then((c) => c.put(event.request, copy));
        }
        return response;
      }).catch(() => cached);
      return cached || fetchPromise;
    })
  );
});


