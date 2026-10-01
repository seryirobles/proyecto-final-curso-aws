// R1: no outline override on controls; keep the browser-default focus ring.

import { describe, expect, it } from 'vitest';
import { readdirSync, readFileSync } from 'node:fs';
import { dirname, join } from 'node:path';
import { fileURLToPath } from 'node:url';

const SRC_DIR = join(dirname(fileURLToPath(import.meta.url)), '..', 'src');
const OUTLINE_NONE = /outline\s*:\s*['"]none/;

function sourceFiles(dir) {
  return readdirSync(dir, { recursive: true })
    .filter((entry) => /\.(js|jsx)$/.test(entry))
    .map((entry) => join(dir, entry));
}

describe('no outline override', () => {
  it('the pattern detects what it claims to', () => {
    expect(OUTLINE_NONE.test("outline: 'none',")).toBe(true);
    expect(OUTLINE_NONE.test('outline:"none"')).toBe(true);
    expect(OUTLINE_NONE.test("outline: '2px solid'")).toBe(false);
  });

  it('no src file sets outline to none (R1)', () => {
    const offenders = sourceFiles(SRC_DIR).filter((p) =>
      OUTLINE_NONE.test(readFileSync(p, 'utf8')),
    );

    expect(offenders).toEqual([]);
  });
});
