// Path to Journeyman — the page works with no signal.
//
// An electrician reads this in a basement, a panel room, a lift shaft. The manifest
// invites Add to Home Screen, and without this an installed JMAN with no bars was a
// browser error page. Everything except the videos now works offline: all 169 videos
// are still listed with their pages and sections, and all 135 quizzes and 5,270
// questions can be taken and graded, because they are inside the page itself.
//
// The videos themselves are never cached. They are hours of Mike Holt's footage and
// they are his; they stream when there is signal and say so plainly when there is not.
//
// V is rewritten by build.py on every build, so a new build replaces the old copy.
const V = '2026092219274';
const SHELL = [
  './',
  './index.html',
  './manifest.webmanifest',
  './favicon.ico',
  './icons/icon.svg',
  './icons/logo.png',
  './icons/icon-192.png',
  './icons/icon-512.png',
  './icons/apple-touch-icon.png',
];

self.addEventListener('install', e => {
  e.waitUntil((async () => {
    const c = await caches.open(V);
    // one missing file must not stop the rest being kept
    await Promise.all(SHELL.map(u => c.add(u).catch(() => {})));
    self.skipWaiting();
  })());
});

self.addEventListener('activate', e => {
  e.waitUntil((async () => {
    for (const k of await caches.keys()) if (k !== V) await caches.delete(k);
    await self.clients.claim();
  })());
});

self.addEventListener('fetch', e => {
  const r = e.request;
  if (r.method !== 'GET') return;
  const url = new URL(r.url);

  // Mike Holt's video, and anything else off this site, is left alone entirely
  if (url.origin !== self.location.origin) return;

  // The page itself: take the fresh one when there is signal, so a new build lands,
  // and fall back to the kept copy the moment there is not.
  const isPage = r.mode === 'navigate' || url.pathname.endsWith('/') || url.pathname.endsWith('index.html');
  if (isPage) {
    e.respondWith((async () => {
      try {
        const live = await fetch(r);
        const c = await caches.open(V);
        c.put('./index.html', live.clone());
        return live;
      } catch (err) {
        return (await caches.match('./index.html')) || (await caches.match('./')) || Response.error();
      }
    })());
    return;
  }

  // icons and the manifest: the kept copy first, they never change within a build
  e.respondWith((async () => {
    const hit = await caches.match(r);
    if (hit) return hit;
    try {
      const live = await fetch(r);
      if (live && live.ok) (await caches.open(V)).put(r, live.clone());
      return live;
    } catch (err) {
      return Response.error();
    }
  })());
});
