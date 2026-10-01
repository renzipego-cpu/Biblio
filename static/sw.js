// Service worker mínimo: habilita la instalación como app.
// No guarda nada en caché para que los pedidos siempre usen datos frescos.
self.addEventListener('install', () => self.skipWaiting());

self.addEventListener('activate', (e) => e.waitUntil(self.clients.claim()));

self.addEventListener('fetch', (e) => {
  // Pasamanos: la red siempre gana.
});
