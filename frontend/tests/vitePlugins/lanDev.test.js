import { EventEmitter } from 'node:events';
import { describe, expect, it, vi } from 'vitest';
import { readFileSync, readdirSync, statSync } from 'node:fs';
import { join } from 'node:path';
import { isPrivateAddress, stripSecureCookie, lanDev } from '../../vite-plugins/lanDev.js';
import lanConfig from '../../vite.config.lan.js';
import baseConfig from '../../vite.config.js';

const root = join(import.meta.dirname, '..', '..');

describe('isPrivateAddress', () => {
  it.each([
    '127.0.0.1',
    '127.5.5.5',
    '::1',
    '10.0.0.1',
    '172.16.0.1',
    '172.31.255.255',
    '192.168.1.20',
    '::ffff:192.168.1.20',
    '::ffff:127.0.0.1',
    '::FFFF:10.1.2.3',
  ])('accepts %s', (a) => expect(isPrivateAddress(a)).toBe(true));

  it.each([
    '8.8.8.8',
    '172.15.0.1',
    '172.32.0.1',
    '192.169.0.1',
    '11.0.0.1',
    '::ffff:8.8.8.8',
    '2001:db8::1',
    '999.1.1.1',
    // IPv6 ULA, link-local and zone ids are rejected on purpose: IPv4-only server.
    'fd00::1',
    'fc00::1',
    'fe80::1',
    'fe80::1%eth0',
    '::1%lo',
    '10.0.0',
    '10.0.0.1.5',
    '',
    'garbage',
    undefined,
    null,
    42,
  ])('rejects %s', (a) => expect(isPrivateAddress(a)).toBe(false));
});

describe('stripSecureCookie', () => {
  it('removes Secure from every cookie, case-insensitively', () => {
    const out = stripSecureCookie([
      'a=1; Path=/; HttpOnly; Secure; SameSite=Lax',
      'b=2; secure; Max-Age=5',
      'c=3; SECURE',
    ]);
    expect(out).toEqual(['a=1; Path=/; HttpOnly; SameSite=Lax', 'b=2; Max-Age=5', 'c=3']);
  });

  it('leaves other attributes and lookalikes untouched', () => {
    const c = 'insecure=Secure; Path=/; HttpOnly; SameSite=Lax';
    expect(stripSecureCookie([c])).toEqual(['insecure=Secure; Path=/; HttpOnly; SameSite=Lax']);
  });

  it('passes through undefined', () => {
    expect(stripSecureCookie(undefined)).toBeUndefined();
  });
});

describe('lanDev middleware', () => {
  function setup() {
    const stack = [];
    const server = {
      middlewares: { use: (fn) => stack.unshift(fn) },
      httpServer: null,
      config: { server: { port: 5173 }, logger: { info: vi.fn() } },
    };
    lanDev().configureServer(server);
    return stack[0];
  }
  const call = (mw, addr) => {
    const res = { statusCode: 0, end: vi.fn(), setHeader: vi.fn() };
    const next = vi.fn();
    mw({ socket: { remoteAddress: addr } }, res, next);
    return { res, next };
  };

  it('403s a public address without calling next', () => {
    const { res, next } = call(setup(), '8.8.8.8');
    expect(res.statusCode).toBe(403);
    expect(next).not.toHaveBeenCalled();
  });

  it.each(['192.168.1.5', '127.0.0.1', '::1', '::ffff:10.0.0.2'])('passes %s', (a) => {
    const { res, next } = call(setup(), a);
    expect(next).toHaveBeenCalledOnce();
    expect(res.end).not.toHaveBeenCalled();
  });

  it('ignores X-Forwarded-For and Host; only the socket address counts', () => {
    const mw = setup();
    const res = { statusCode: 0, end: vi.fn() };
    const next = vi.fn();
    const headers = { 'x-forwarded-for': '192.168.1.5', host: '192.168.1.5' };
    mw({ socket: { remoteAddress: '8.8.8.8' }, headers }, res, next);
    expect(res.statusCode).toBe(403);
    expect(next).not.toHaveBeenCalled();
  });
});

describe('lanDev upgrade guard', () => {
  function setup() {
    const order = [];
    const httpServer = new EventEmitter();
    httpServer.on('upgrade', () => order.push('vite'));
    const server = {
      middlewares: { use: vi.fn() },
      httpServer,
      config: { server: { port: 5173 }, logger: { info: vi.fn() } },
    };
    lanDev().configureServer(server);
    return { httpServer, order };
  }
  const upgrade = (addr) => {
    const { httpServer, order } = setup();
    const socket = {
      remoteAddress: addr,
      destroy: vi.fn(() => order.push('destroy')),
    };
    httpServer.emit('upgrade', {}, socket, new Uint8Array(0));
    return { socket, order };
  };

  it('destroys a non-private socket before Vite sees it', () => {
    const { socket, order } = upgrade('8.8.8.8');
    expect(socket.destroy).toHaveBeenCalledOnce();
    expect(order[0]).toBe('destroy');
  });

  it.each(['192.168.1.5', '::1'])('leaves %s alone', (a) => {
    const { socket } = upgrade(a);
    expect(socket.destroy).not.toHaveBeenCalled();
  });

  it('tolerates a null httpServer (middleware mode)', () => {
    const server = {
      middlewares: { use: vi.fn() },
      httpServer: null,
      config: { server: { port: 5173 }, logger: { info: vi.fn() } },
    };
    expect(() => lanDev().configureServer(server)).not.toThrow();
  });
});

describe('production guarantee', () => {
  const base = readFileSync(join(root, 'vite.config.js'), 'utf8');

  it('base config has no host, cookie rewriting or LAN import', () => {
    expect(base).not.toMatch(/\bhost\b/);
    expect(base).not.toMatch(/set-cookie|proxyRes|stripSecure/i);
    expect(base).not.toMatch(/lanDev|vite\.config\.lan/);
    expect(baseConfig.server.host).toBeUndefined();
  });

  it('nothing in src/ or index.html references the LAN tooling', () => {
    const walk = (d) =>
      readdirSync(d).flatMap((f) => {
        const p = join(d, f);
        return statSync(p).isDirectory() ? walk(p) : [p];
      });
    const files = [...walk(join(root, 'src')), join(root, 'index.html')];
    for (const f of files) {
      expect(readFileSync(f, 'utf8'), f).not.toMatch(/lanDev|vite\.config\.lan/);
    }
  });

  it('LAN config proxies only to http://localhost:8080 and strips cookies', () => {
    const proxy = lanConfig.server.proxy['/v1'];
    expect(proxy.target).toBe('http://localhost:8080');
    expect(Object.keys(lanConfig.server.proxy)).toEqual(['/v1']);
    expect(lanConfig.server.host).toBe('0.0.0.0');
    expect(lanConfig.server.port).toBe(5173);
    expect(lanConfig.server.strictPort).toBe(true);
    expect(typeof proxy.configure).toBe('function');
  });

  it('proxy hook rewrites Set-Cookie on proxy responses', () => {
    const proxy = lanConfig.server.proxy['/v1'];
    let handler;
    proxy.configure({ on: (ev, fn) => ev === 'proxyRes' && (handler = fn) });
    const res = { headers: { 'set-cookie': ['s=1; Secure; HttpOnly'] } };
    handler(res);
    expect(res.headers['set-cookie']).toEqual(['s=1; HttpOnly']);
  });
});
