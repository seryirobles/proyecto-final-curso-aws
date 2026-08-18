import { defineConfig } from 'vitest/config';
import react from '@vitejs/plugin-react';
import { htmlMessages } from './vite-plugins/htmlMessages.js';

// This toolchain root never reaches backend/ or prototypes/ (docs/architecture.md
// section 3). Root stays pinned to this directory so no build can escape it.
export default defineConfig({
  root: import.meta.dirname,
  plugins: [react(), htmlMessages()],
  build: {
    outDir: 'dist',
  },
  test: {
    include: ['tests/**/*.test.{js,jsx}'],
    environment: 'node',
    globals: false,
  },
});
