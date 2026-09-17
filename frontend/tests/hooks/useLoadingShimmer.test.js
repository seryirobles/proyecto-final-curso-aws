// @vitest-environment jsdom
import { act, renderHook } from '@testing-library/react';
import { afterEach, describe, expect, it, vi } from 'vitest';
import { useLoadingShimmer } from '../../src/hooks/useLoadingShimmer.js';

afterEach(() => {
  vi.useRealTimers();
});

describe('useLoadingShimmer', () => {
  it('starts false and flips on each tick', () => {
    vi.useFakeTimers();
    const { result } = renderHook(() => useLoadingShimmer());

    expect(result.current).toBe(false);
    act(() => vi.advanceTimersByTime(600));
    expect(result.current).toBe(true);
    act(() => vi.advanceTimersByTime(600));
    expect(result.current).toBe(false);
  });

  it('clears its interval on unmount', () => {
    vi.useFakeTimers();
    const clearSpy = vi.spyOn(globalThis, 'clearInterval');
    const { unmount, result } = renderHook(() => useLoadingShimmer());

    unmount();
    act(() => vi.advanceTimersByTime(1200));

    expect(clearSpy).toHaveBeenCalledTimes(1);
    expect(result.current).toBe(false);
  });
});
