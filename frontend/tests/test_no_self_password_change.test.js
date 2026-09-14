// R28, design.md section 9: no *.jsx file other than SetPasswordView.jsx may
// call apiFetch against /v1/session/password. Named *.test.js, not test_*.js
// (vite.config.js's glob) - see progress/impl_frontend_spa.md, deviation 3.

import { describe, expect, it } from 'vitest';
import { readdirSync, readFileSync } from 'node:fs';
import { dirname, join } from 'node:path';
import { fileURLToPath } from 'node:url';

const TESTS_ROOT = dirname(fileURLToPath(import.meta.url));
const COMPONENTS_DIR = join(TESTS_ROOT, '..', 'src', 'components');
const EXEMPT_FILE = 'SetPasswordView.jsx';
const SESSION_PASSWORD_CALL = /apiFetch\([^)]*\/v1\/session\/password/;

function jsxFiles(dir) {
  return readdirSync(dir, { recursive: true })
    .filter((entry) => entry.endsWith('.jsx'))
    .map((entry) => join(dir, entry));
}

describe('no self password change', () => {
  it('no component other than SetPasswordView.jsx calls apiFetch against /v1/session/password (R28)', () => {
    const offenders = jsxFiles(COMPONENTS_DIR)
      .filter((path) => !path.endsWith(EXEMPT_FILE))
      .filter((path) => SESSION_PASSWORD_CALL.test(readFileSync(path, 'utf8')));

    expect(offenders).toEqual([]);
  });
});
