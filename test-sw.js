'use strict';
importScripts('./test-environment.js');

if (!isMuskelTestOrigin(self.location)) {
  throw new Error('TESTVERSION: eigener Test-Origin erforderlich');
}

const scope = self.registration.scope;
const section = 'muskel-coach-test:' + scope + ':';
const cacheName = section + 'v2';
const appFiles = [
  './', 'test-environment.js', 'test-bootstrap.js', 'test-app.js',
  'manifest.webmanifest', 'icon-180.png', 'icon-192.png', 'icon-512.png',
];
const staticUrls = new Set(appFiles.map(file => new URL(file, scope).href));

self.addEventListener('install', event => {
  event.waitUntil((async () => {
    const cache = await caches.open(cacheName);
    await cache.addAll(appFiles.map(file => new Request(new URL(file, scope), { cache: 'reload' })));
    await self.skipWaiting();
  })());
});

self.addEventListener('activate', event => {
  event.waitUntil((async () => {
    const names = await caches.keys();
    await Promise.all(names
      .filter(name => name.startsWith(section) && name !== cacheName)
      .map(name => caches.delete(name)));
    await self.clients.claim();
  })());
});

self.addEventListener('fetch', event => {
  const { request } = event;
  if (request.method !== 'GET') return;
  const url = new URL(request.url);
  const key = new URL(url.href);
  key.search = '';
  key.hash = '';
  // Pages redirects index.html to the directory URL.
  if (key.href === new URL('index.html', scope).href) key.href = scope;
  if (!staticUrls.has(key.href)) return;

  event.respondWith(fetch(request).catch(async () =>
    (await caches.match(key.href, { cacheName })) || Response.error()
  ));
});
