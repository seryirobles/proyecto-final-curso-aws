// DEV ONLY: `npm run dev:lan`, then open the printed URL on a phone (same Wi-Fi).
// Windows Firewall: allow Node on PRIVATE networks (or open TCP 5173 yourself).
import { mergeConfig } from 'vite';
import baseConfig from './vite.config.js';
import { lanDev, stripSecureCookie } from './vite-plugins/lanDev.js';

export default mergeConfig(baseConfig, {
  plugins: [lanDev()],
  server: {
    host: '0.0.0.0',
    port: 5173,
    strictPort: true,
    proxy: {
      '/v1': {
        target: 'http://localhost:8080',
        changeOrigin: true,
        // Secure cookies are not stored over plain http on the LAN.
        configure: (proxy) => {
          proxy.on('proxyRes', (res) => {
            if (res.headers['set-cookie']) {
              res.headers['set-cookie'] = stripSecureCookie(res.headers['set-cookie']);
            }
          });
        },
      },
    },
  },
});
