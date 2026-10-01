// @vitest-environment jsdom
// R31, R32: same-key calls in one tick run once; keys are independent;
// pending is true while running and false after a resolve or a reject.
import { act, renderHook } from '@testing-library/react';
import { describe, expect, it, vi } from 'vitest';
import { usePendingGuard } from '../../src/hooks/pendingGuard.js';

function deferred() {
  let resolve;
  let reject;
  const promise = new Promise((res, rej) => {
    resolve = res;
    reject = rej;
  });
  return { promise, resolve, reject };
}

describe('usePendingGuard', () => {
  it('two same-tick run(key) calls invoke fn once (R32)', async () => {
    const { result } = renderHook(() => usePendingGuard());
    const gate = deferred();
    const fn = vi.fn(() => gate.promise);

    let second;
    await act(async () => {
      result.current.run('k', fn);
      second = result.current.run('k', fn);
      gate.resolve();
    });

    expect(fn).toHaveBeenCalledTimes(1);
    expect(second).toBeUndefined();
  });

  it('different keys are independent (R32)', async () => {
    const { result } = renderHook(() => usePendingGuard());
    const fn = vi.fn(() => Promise.resolve());

    await act(async () => {
      result.current.run('a', fn);
      result.current.run('b', fn);
    });

    expect(fn).toHaveBeenCalledTimes(2);
  });

  it('exposes pending while running and clears it after a reject (R31)', async () => {
    const { result } = renderHook(() => usePendingGuard());
    const gate = deferred();

    let outcome;
    await act(async () => {
      outcome = result.current.run('k', () => gate.promise).catch(() => 'rejected');
    });
    expect(result.current.isPending('k')).toBe(true);
    expect(result.current.pending.has('k')).toBe(true);
    expect(result.current.isPending('other')).toBe(false);

    await act(async () => {
      gate.reject(new Error('boom'));
      await outcome;
    });
    expect(result.current.isPending('k')).toBe(false);

    const again = vi.fn(() => Promise.resolve());
    await act(async () => {
      result.current.run('k', again);
    });
    expect(again).toHaveBeenCalledTimes(1);
  });
});
