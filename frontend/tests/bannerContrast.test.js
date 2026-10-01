// R35: ink on honeySoft meets WCAG 1.4.3 (>= 4.5:1); computed, not assumed.
import { describe, expect, it } from 'vitest';
import { tokens } from '../src/tokens/index.js';

function channel(hex, offset) {
  const c = parseInt(hex.slice(offset, offset + 2), 16) / 255;
  return c <= 0.03928 ? c / 12.92 : ((c + 0.055) / 1.055) ** 2.4;
}

function luminance(hex) {
  return 0.2126 * channel(hex, 1) + 0.7152 * channel(hex, 3) + 0.0722 * channel(hex, 5);
}

function ratio(a, b) {
  const [hi, lo] = [luminance(a), luminance(b)].sort((x, y) => y - x);
  return (hi + 0.05) / (lo + 0.05);
}

describe('banner colour contrast', () => {
  it('ink on honeySoft is at least 4.5:1 (R35)', () => {
    const value = ratio(tokens.color.ink, tokens.color.honeySoft);

    expect(value).toBeGreaterThanOrEqual(4.5);
    expect(value).toBeCloseTo(11.03, 1);
  });
});
