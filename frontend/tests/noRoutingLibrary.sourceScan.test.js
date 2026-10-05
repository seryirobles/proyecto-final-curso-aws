// R53: src/ imports no routing library.
import { describe, expect, it } from 'vitest';
import { readdirSync, readFileSync } from 'node:fs';
import { dirname, join } from 'node:path';
import { fileURLToPath } from 'node:url';

const SRC_DIR = join(dirname(fileURLToPath(import.meta.url)), '..', 'src');
const ROUTING =
  /from\s*['"](react-router[^'"]*|@remix-run[^'"]*|wouter|history|@tanstack\/[^'"]*router[^'"]*)['"]/;

describe('no routing library', () => {
  it('the pattern detects what it claims to', () => {
    expect(ROUTING.test("import { Link } from 'react-router-dom';")).toBe(true);
    expect(ROUTING.test("import { useState } from 'react';")).toBe(false);
  });

  it('no src file imports a routing library (R53)', () => {
    const offenders = readdirSync(SRC_DIR, { recursive: true })
      .filter((f) => /\.jsx?$/.test(f))
      .filter((f) => ROUTING.test(readFileSync(join(SRC_DIR, f), 'utf8')));
    expect(offenders).toEqual([]);
  });
});
