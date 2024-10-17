self.addEventListener('install', function(event) {
    event.waitUntil(
        caches.open('my-cache-v1').then(function(cache) {
            return cache.addAll([
                '/_dash-component-suites/dash/dcc/async-dropdown.js',
                '/_dash-component-suites/dash/dcc/async-graph.js',
                '/_dash-component-suites/dash/dcc/async-markdown.js',
                '/_dash-component-suites/dash/dcc/async-datepicker.js',
                '/_dash-component-suites/dash/dcc/async-highlight.js',
            ]);
        })
    );
});

self.addEventListener('fetch', function(event) {
    event.respondWith(
        caches.match(event.request).then(function(response) {
            return response || fetch(event.request);
        })
    );
});
