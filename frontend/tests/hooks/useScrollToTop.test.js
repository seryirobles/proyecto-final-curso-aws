// @vitest-environment jsdom
// R17: scroll to top on a view change, not on mount.

import { renderHook } from '@testing-library/react';
import { beforeEach, describe, expect, it, vi } from 'vitest';
import { useScrollToTop } from '../../src/hooks/useScrollToTop.js';

beforeEach(() => {
  window.scrollTo = vi.fn();
});

describe('useScrollToTop', () => {
  it('does not scroll on mount', () => {
    renderHook(() => useScrollToTop('week'));
    expect(window.scrollTo).not.toHaveBeenCalled();
  });

  it('scrolls once per view change', () => {
    const { rerender } = renderHook(({ view }) => useScrollToTop(view), {
      initialProps: { view: 'week' },
    });
    rerender({ view: 'rules' });
    rerender({ view: 'rules' });
    expect(window.scrollTo).toHaveBeenCalledTimes(1);
    expect(window.scrollTo).toHaveBeenCalledWith(0, 0);
  });
});
