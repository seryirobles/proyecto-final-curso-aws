import { networkInterfaces } from 'node:os';

/** True for loopback and RFC1918 addresses (incl. IPv4-mapped IPv6); false otherwise. */
export function isPrivateAddress(addr) {
  // IPv6 ULA, link-local and zone ids are rejected on purpose: IPv4-only server.
  if (typeof addr !== 'string') return false;
  let a = addr.trim().toLowerCase();
  if (a === '::1') return true;
  if (a.startsWith('::ffff:')) a = a.slice(7);
  const m = /^(\d{1,3})\.(\d{1,3})\.(\d{1,3})\.(\d{1,3})$/.exec(a);
  if (!m) return false;
  const o = m.slice(1).map(Number);
  if (o.some((n) => n > 255)) return false;
  const [a0, a1] = o;
  return (
    a0 === 127 || a0 === 10 || (a0 === 172 && a1 >= 16 && a1 <= 31) || (a0 === 192 && a1 === 168)
  );
}

/** Drops the `Secure` attribute from each Set-Cookie header; other attributes untouched. */
export function stripSecureCookie(setCookieHeaders) {
  if (!Array.isArray(setCookieHeaders)) return setCookieHeaders;
  return setCookieHeaders.map((c) =>
    c
      .split(';')
      .filter((part, i) => i === 0 || part.trim().toLowerCase() !== 'secure')
      .join(';'),
  );
}

function lanUrls(port) {
  return Object.values(networkInterfaces())
    .flat()
    .filter((i) => i && i.family === 'IPv4' && !i.internal && isPrivateAddress(i.address))
    .map((i) => `http://${i.address}:${port}/`);
}

/** DEV ONLY: rejects non-private clients with 403 and prints the LAN URLs. */
export function lanDev() {
  return {
    name: 'lan-dev',
    configureServer(server) {
      // Pre-hook: registered before Vite's own middlewares, so it runs first.
      server.middlewares.use((req, res, next) => {
        if (isPrivateAddress(req.socket?.remoteAddress)) return next();
        res.statusCode = 403;
        res.end('Forbidden');
      });
      // Upgrades bypass connect middleware; run before Vite's own handler.
      server.httpServer?.prependListener('upgrade', (_req, socket) => {
        if (!isPrivateAddress(socket.remoteAddress)) socket.destroy();
      });
      server.httpServer?.once('listening', () => {
        const port = server.config.server.port;
        const urls = lanUrls(port);
        server.config.logger.info(
          [
            '',
            '  LAN dev mode - open on the phone (same Wi-Fi):',
            ...(urls.length ? urls.map((u) => `    ${u}`) : ['    (no private LAN address found)']),
            '  DEV ONLY - never expose this to an untrusted network',
            '',
          ].join('\n'),
        );
      });
    },
  };
}
