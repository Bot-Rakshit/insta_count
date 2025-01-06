self.addEventListener('push', function(event) {
    const options = {
        body: event.data.text(),
        icon: 'icon.png',
        badge: 'badge.png'
    };

    event.waitUntil(
        self.registration.showNotification('Instagram Monitor', options)
    );
});

self.addEventListener('install', (event) => {
    event.waitUntil(
        caches.open('v1').then((cache) => {
            return cache.addAll([
                '/',
                '/static/app.js',
                '/static/styles.css'
            ]);
        })
    );
}); 