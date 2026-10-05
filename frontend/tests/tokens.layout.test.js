// R7: viewport thresholds and layout sizes come from tokens (design.md section 2).
import { describe, expect, it } from 'vitest';
import { tokens } from '../src/tokens/index.js';

describe('phase 2 tokens', () => {
  it('breakpoints are 600 / 768 / 1280', () => {
    expect(tokens.breakpoint).toEqual({ tablet: 600, medium: 768, desktop: 1280 });
  });

  it('layout carries the phase 2 sizes', () => {
    expect(tokens.layout).toMatchObject({
      summaryDayMin: '140px',
      contentMax: '1200px',
      tabBarHeight: '56px',
      headerHeight: '56px',
      dayStripHeight: '48px',
      targetMobile: '44px',
      targetDesktop: '24px',
      listRowMobile: '48px',
    });
  });
});
