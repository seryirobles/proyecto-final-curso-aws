// R22, design.md section 9 (mirrors backend/core/tests/test_no_ambient_time.py's
// technique): frontend/src/**/*.jsx source text may carry no aria-* attribute,
// no explicit role="...", no tabIndex, and no accessibility-library import.

import { describe, expect, it } from 'vitest';
import { readdirSync, readFileSync } from 'node:fs';
import { dirname, join } from 'node:path';
import { fileURLToPath } from 'node:url';

const TESTS_ROOT = dirname(fileURLToPath(import.meta.url));
const SRC_DIR = join(TESTS_ROOT, '..', 'src');

const ARIA_ATTR = /\baria-[a-zA-Z-]+\s*=/;
const ROLE_ATTR = /\brole\s*=\s*["']/;
const TAB_INDEX = /\btabIndex\s*=/;
const A11Y_IMPORT = /from\s*['"][^'"]*(aria|axe|a11y)[^'"]*['"]/i;

const BANNED = [ARIA_ATTR, ROLE_ATTR, TAB_INDEX, A11Y_IMPORT];

function jsxFiles(dir) {
  return readdirSync(dir, { recursive: true })
    .filter((entry) => entry.endsWith('.jsx'))
    .map((entry) => join(dir, entry));
}

function offendersIn(path) {
  const body = readFileSync(path, 'utf8');
  return BANNED.some((pattern) => pattern.test(body));
}

describe('no extra accessibility', () => {
  it('the banned patterns detect what they claim to', () => {
    expect(ARIA_ATTR.test('<div aria-label="x">')).toBe(true);
    expect(ROLE_ATTR.test('<div role="button">')).toBe(true);
    expect(TAB_INDEX.test('<div tabIndex={0}>')).toBe(true);
    expect(A11Y_IMPORT.test("import { axe } from '@axe-core/react';")).toBe(true);
    expect(A11Y_IMPORT.test("import { render } from '@testing-library/react';")).toBe(false);
  });

  it('no frontend/src/**/*.jsx file adds accessibility affordances beyond browser defaults (R22)', () => {
    const offenders = jsxFiles(SRC_DIR).filter(offendersIn);

    expect(offenders).toEqual([]);
  });
});
