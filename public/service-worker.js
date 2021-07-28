var cacheName = 'appCache';

self.addEventListener("activate", event => {
    const cacheKeeplist = [cacheName];
    event.waitUntil(
        caches.keys()
            .then(keyList =>
                Promise.all(keyList.map(key => {
                    if (!cacheKeeplist.includes(key)) {
                        return caches.delete(key);
                    }
                }))
            )
    );
});

self.addEventListener('install', function(event) {
    event.waitUntil(
        caches.open(cacheName).then(function(cache) {
            return cache.addAll(
                [
                    './logo192.png',
                    './logo512.png',
                    "./favicon.ico",
                    '../src/assets/img/logo.png',
                    '../src/assets/img/logo_inverse.png',

                ]
            );
        })
    );
});

self.addEventListener('fetch', function(event) {
    event.respondWith(
        caches.open(cacheName).then(function(cache) {
            return cache.match(event.request).then(function (response) {
                return response || fetch(event.request).then(function(response) {
                    cache.put(event.request, response.clone());
                    return response;
                });
            });
        })
    );
});
