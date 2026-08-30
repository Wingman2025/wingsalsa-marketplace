const CACHE_NAME = "wingsalsa-public-v1";
const OFFLINE_URL = "/offline/";
const APP_SHELL = [
    "/",
    "/actividades/",
    OFFLINE_URL,
    "/static/css/style.css",
    "/static/icons/icon-192.png",
    "/static/icons/icon-512.png",
    "/static/js/pwa.js"
];

self.addEventListener("install", event => {
    event.waitUntil(caches.open(CACHE_NAME).then(cache => cache.addAll(APP_SHELL)));
    self.skipWaiting();
});

self.addEventListener("activate", event => {
    event.waitUntil(
        caches.keys().then(keys => Promise.all(
            keys.filter(key => key !== CACHE_NAME).map(key => caches.delete(key))
        ))
    );
    self.clients.claim();
});

self.addEventListener("fetch", event => {
    const request = event.request;
    const url = new URL(request.url);

    if (request.method !== "GET" || url.origin !== self.location.origin || url.pathname.startsWith("/health/") || url.pathname.startsWith("/gestion/") || url.pathname.startsWith("/admin/") || url.pathname.startsWith("/solicitud/")) {
        return;
    }

    if (request.mode === "navigate") {
        event.respondWith(
            fetch(request)
                .then(async response => {
                    if (response.ok) {
                        const cache = await caches.open(CACHE_NAME);
                        await cache.put(request, response.clone());
                    }
                    return response;
                })
                .catch(async () => (await caches.match(request)) || caches.match(OFFLINE_URL))
        );
        return;
    }

    if (url.pathname.startsWith("/static/")) {
        event.respondWith(
            caches.match(request).then(cached => cached || fetch(request).then(async response => {
                if (response.ok) {
                    const cache = await caches.open(CACHE_NAME);
                    await cache.put(request, response.clone());
                }
                return response;
            }))
        );
    }
});