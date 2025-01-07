self.addEventListener('install', (event) => {
    event.waitUntil(
        caches.open('v1').then((cache) => {
            return cache.addAll([
                '/amishi/',
                '/static/manifest.json',
                '/static/icon-192x192.png',
                '/static/icon-512x512.png',
                '/static/maskable_icon.png'
            ]);
        })
    );
});

self.addEventListener('fetch', (event) => {
    if (event.request.url.endsWith('/amishi')) {
        event.respondWith(Response.redirect('/amishi/'));
        return;
    }

    event.respondWith(
        caches.match(event.request).then((response) => {
            return response || fetch(event.request);
        })
    );
}); 