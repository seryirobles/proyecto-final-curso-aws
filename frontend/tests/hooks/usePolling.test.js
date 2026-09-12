// @vitest-environment jsdom
//
// The project's only jsdom test (design.md section 7, section 9, owner's gate
// ruling 2026-09-11): proves the hook's real-DOM wiring, not R12-R26's
// decision logic, which stays proven at pollingEngine.test.js.

import { act, renderHook } from '@testing-library/react';
import { afterEach, describe, expect, it, vi } from 'vitest';
import { usePolling } from '../../src/hooks/usePolling.js';

function fakeEngine() {
  // A stable snapshot reference, mutated only via setSnapshot - mirrors the
  // real engine's contract (useSyncExternalStore needs Object.is stability).
  let snapshot = { data: null, marker: null, connectionLost: false };
  const listeners = new Set();
  return {
    start: vi.fn(),
    dispose: vi.fn(),
    applyMutationMarker: vi.fn(),
    subscribe: vi.fn((listener) => {
      listeners.add(listener);
      return () => listeners.delete(listener);
    }),
    getSnapshot: vi.fn(() => snapshot),
    setSnapshot(next) {
      snapshot = next;
    },
    emit() {
      for (const listener of listeners) listener();
    },
  };
}

describe('usePolling', () => {
  afterEach(() => {
    vi.restoreAllMocks();
  });

  it('starts the injected engine on mount', () => {
    const engine = fakeEngine();
    const createEngine = vi.fn(() => engine);

    renderHook(() => usePolling('/v1/shopping-list', { some: 'config' }, { createEngine }));

    expect(engine.start).toHaveBeenCalledTimes(1);
  });

  it('reaches the hook default visibilitySource on a real visibilitychange event', () => {
    let capturedVisibilitySource;
    const engine = fakeEngine();
    const createEngine = vi.fn((_config, deps) => {
      capturedVisibilitySource = deps.visibilitySource;
      return engine;
    });
    const spy = vi.fn();

    renderHook(() => usePolling('/v1/shopping-list', {}, { createEngine }));
    capturedVisibilitySource.subscribe(spy);
    document.dispatchEvent(new Event('visibilitychange'));

    expect(spy).toHaveBeenCalledTimes(1);
  });

  it('reaches the hook default visibilitySource on real blur and focus events', () => {
    // R17/R18 depend on `window` blur/focus, not just `document` visibilitychange
    // (M-B, fix round 1) - proves domVisibilitySource wires both listeners.
    let capturedVisibilitySource;
    const engine = fakeEngine();
    const createEngine = vi.fn((_config, deps) => {
      capturedVisibilitySource = deps.visibilitySource;
      return engine;
    });
    const spy = vi.fn();

    renderHook(() => usePolling('/v1/shopping-list', {}, { createEngine }));
    capturedVisibilitySource.subscribe(spy);
    window.dispatchEvent(new Event('blur'));
    window.dispatchEvent(new Event('focus'));

    expect(spy).toHaveBeenCalledTimes(2);
  });

  it('re-renders with the engine snapshot when it notifies', () => {
    const engine = fakeEngine();
    const createEngine = vi.fn(() => engine);

    const { result } = renderHook(() => usePolling('/v1/shopping-list', {}, { createEngine }));
    expect(result.current.marker).toBe(null);

    act(() => {
      engine.setSnapshot({ data: { items: [] }, marker: 4, connectionLost: false });
      engine.emit();
    });

    expect(result.current.marker).toBe(4);
    expect(result.current.data).toEqual({ items: [] });
  });

  it('disposes the injected engine exactly once on unmount', () => {
    const engine = fakeEngine();
    const createEngine = vi.fn(() => engine);

    const { unmount } = renderHook(() => usePolling('/v1/shopping-list', {}, { createEngine }));
    unmount();

    expect(engine.dispose).toHaveBeenCalledTimes(1);
  });
});
