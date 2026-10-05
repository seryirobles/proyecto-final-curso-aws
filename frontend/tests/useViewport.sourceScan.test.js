// R6: `useViewport(` is called once, in App.jsx (design.md section 5).
import { readdirSync, readFileSync, statSync } from 'node:fs';
import { join, sep } from 'node:path';
import { describe, expect, it } from 'vitest';

function sources(dir) {
  return readdirSync(dir).flatMap((name) => {
    const path = join(dir, name);
    return statSync(path).isDirectory() ? sources(path) : [path];
  });
}

describe('useViewport call sites', () => {
  it('appears only in App.jsx and its own file', () => {
    const hits = sources('src')
      .filter((file) => /\buseViewport\(/.test(readFileSync(file, 'utf8')))
      .map((file) => file.split(sep).join('/'));
    expect(hits.sort()).toEqual(['src/components/App.jsx', 'src/hooks/useViewport.js']);
  });
});
