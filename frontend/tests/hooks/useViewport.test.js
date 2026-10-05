// @vitest-environment jsdom
// R1-R5: tier from `min-width` media queries (frontend_ux_phase2 design.md section 3).

import { useEffect } from 'react';
import { act, renderHook } from '@testing-library/react';
import { afterEach, describe, expect, it, vi } from 'vitest';
import { useViewport, VIEWPORT } from '../../src/hooks/useViewport.js';

// Fake matchMedia that evaluates `(min-width: Npx)` against a mutable width.
function installViewport(initialWidth) {
  const state = { width: initialWidth, entries: [] };
  window.matchMedia = vi.fn((query) => {
    const min = Number(/min-width:\s*(\d+)px/.exec(query)[1]);
    const listeners = new Set();
    const mql = {
      get matches() {
        return state.width >= min;
      },
      addEventListener: (_t, l) => listeners.add(l),
      removeEventListener: (_t, l) => listeners.delete(l),
    };
    state.entries.push(listeners);
    return mql;
  });
  state.resize = (width) => {
    state.width = width;
    state.entries.forEach((set) => set.forEach((l) => l()));
  };
  return state;
}

afterEach(() => vi.restoreAllMocks());

describe('useViewport', () => {
  it.each([
    [320, VIEWPORT.COMPACT],
    [599, VIEWPORT.COMPACT],
    [600, VIEWPORT.NARROW],
    [767, VIEWPORT.NARROW],
    [768, VIEWPORT.MEDIUM],
    [1279, VIEWPORT.MEDIUM],
    [1280, VIEWPORT.WIDE],
    [1920, VIEWPORT.WIDE],
  ])('width %i -> %s', (width, tier) => {
    installViewport(width);
    const { result } = renderHook(() => useViewport());
    expect(result.current).toBe(tier);
  });

  it('exposes the tier names', () => {
    expect(VIEWPORT).toEqual({
      COMPACT: 'compact',
      NARROW: 'narrow',
      MEDIUM: 'medium',
      WIDE: 'wide',
    });
  });

  it('updates on a threshold crossing without remounting', () => {
    const state = installViewport(500);
    let mounts = 0;
    const { result } = renderHook(() => {
      useEffect(() => {
        mounts += 1;
      }, []);
      return useViewport();
    });
    expect(result.current).toBe('compact');

    act(() => state.resize(800));
    expect(result.current).toBe('medium');
    act(() => state.resize(1300));
    expect(result.current).toBe('wide');
    expect(mounts).toBe(1);
  });
});
