// Asserts every button under `root` carries the min height and width `px`.

import { expect } from 'vitest';

export function expectTargets(root, px, count) {
  const buttons = [...root.querySelectorAll('button')];
  if (count !== undefined) expect(buttons).toHaveLength(count);
  expect(buttons.length).toBeGreaterThan(0);
  buttons.forEach((b) => {
    expect([b.textContent, b.style.minHeight, b.style.minWidth]).toEqual([b.textContent, px, px]);
  });
}
