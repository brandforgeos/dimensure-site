// Dimensure Portal — phone notifications. Shows each portal notification as a phone/desktop notification and
// opens the right page when it is tapped. No caching: the portal always loads fresh.
self.addEventListener('install', () => self.skipWaiting())
self.addEventListener('activate', (e) => e.waitUntil(self.clients.claim()))

self.addEventListener('push', (e) => {
  let d = {}
  try { d = e.data ? e.data.json() : {} } catch { d = { title: 'Dimensure', body: e.data ? e.data.text() : '' } }
  const title = d.title || 'Dimensure'
  e.waitUntil(self.registration.showNotification(title, {
    body: d.body || '', icon: '/icon-192.png', badge: '/badge-72.png', tag: d.tag || undefined,
    data: { url: d.url || '/' }, timestamp: Date.now(),
  }))
})

self.addEventListener('notificationclick', (e) => {
  e.notification.close()
  const url = new URL((e.notification.data && e.notification.data.url) || '/', self.location.origin).href
  e.waitUntil((async () => {
    const wins = await self.clients.matchAll({ type: 'window', includeUncontrolled: true })
    for (const w of wins) {
      if (new URL(w.url).origin === self.location.origin) { await w.focus(); try { await w.navigate(url) } catch { /* older browsers */ } return }
    }
    await self.clients.openWindow(url)
  })())
})
