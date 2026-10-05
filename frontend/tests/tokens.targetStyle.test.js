// targetStyle(viewport): 44 px below 768 px, 24 px from 768 px (frontend_ux_phase2 R41-R43).
import { describe, expect, it } from 'vitest';
import { targetStyle } from '../src/tokens/controlStyles.js';

describe('targetStyle', () => {
  it.each(['compact', 'narrow'])('is 44 px when %s', (viewport) => {
    expect(targetStyle(viewport)).toEqual({ minHeight: '44px', minWidth: '44px' });
  });

  it.each(['medium', 'wide'])('is 24 px when %s', (viewport) => {
    expect(targetStyle(viewport)).toEqual({ minHeight: '24px', minWidth: '24px' });
  });
});
