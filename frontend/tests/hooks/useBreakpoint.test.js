// @vitest-environment jsdom
//
// Proves the hook's real matchMedia wiring, same technique as
// usePolling.test.js (design.md section 9).

import { act, renderHook } from '@testing-library/react';
import { afterEach, describe, expect, it, vi } from 'vitest';
import { useBreakpoint } from '../../src/hooks/useBreakpoint.js';

function fakeMatchMedia(initialMatches) {
  const listeners = new Set();
  return {
    matches: initialMatches,
    addEventListener: vi.fn((_type, listener) => listeners.add(listener)),
    removeEventListener: vi.fn((_type, listener) => listeners.delete(listener)),
    emit(matches) {
      this.matches = matches;
      listeners.forEach((listener) => listener());
    },
  };
}

describe('useBreakpoint', () => {
  afterEach(() => {
    vi.restoreAllMocks();
  });

  // jsdom has no real matchMedia implementation - assign it directly rather
  // than vi.spyOn, which requires the property to already be a function.

  it('returns the initial matchMedia value', () => {
    const mql = fakeMatchMedia(true);
    window.matchMedia = vi.fn(() => mql);

    const { result } = renderHook(() => useBreakpoint('(min-width: 600px)'));

    expect(result.current).toBe(true);
  });

  it('flips when matchMedia fires a change event', () => {
    const mql = fakeMatchMedia(false);
    window.matchMedia = vi.fn(() => mql);
    const { result } = renderHook(() => useBreakpoint('(min-width: 600px)'));

    act(() => mql.emit(true));

    expect(result.current).toBe(true);
  });

  it('removes its listener on unmount', () => {
    const mql = fakeMatchMedia(false);
    window.matchMedia = vi.fn(() => mql);
    const { unmount } = renderHook(() => useBreakpoint('(min-width: 600px)'));

    unmount();

    expect(mql.removeEventListener).toHaveBeenCalledTimes(1);
  });
});
