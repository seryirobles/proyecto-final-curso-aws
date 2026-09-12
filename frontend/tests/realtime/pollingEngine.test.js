import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import {
  DEFAULT_CONFIG,
  computeDelay,
  createPollingEngine,
  resolveMutationMarker,
} from '../../src/realtime/pollingEngine.js';

// --- part 1: pure decision functions (R16, R17, R21, R22, R25, R26) ---

describe('computeDelay', () => {
  it('uses the active interval in the foreground with no failures', () => {
    const delay = computeDelay(
      { isBackgrounded: false, consecutiveFailures: 0, config: DEFAULT_CONFIG },
      () => 0.5,
    );
    expect(delay).toBe(DEFAULT_CONFIG.activeIntervalMs);
  });

  it('uses the background interval while backgrounded with no failures', () => {
    const delay = computeDelay(
      { isBackgrounded: true, consecutiveFailures: 0, config: DEFAULT_CONFIG },
      () => 0.5,
    );
    expect(delay).toBe(DEFAULT_CONFIG.backgroundIntervalMs);
  });

  it('doubles the base delay once per consecutive failure, deterministic random', () => {
    // random() = 0.5 -> jitterFactor = 1 (no drift), isolates the doubling math.
    const oneFailure = computeDelay(
      { isBackgrounded: false, consecutiveFailures: 1, config: DEFAULT_CONFIG },
      () => 0.5,
    );
    const twoFailures = computeDelay(
      { isBackgrounded: false, consecutiveFailures: 2, config: DEFAULT_CONFIG },
      () => 0.5,
    );
    expect(oneFailure).toBe(DEFAULT_CONFIG.activeIntervalMs * 2);
    expect(twoFailures).toBe(DEFAULT_CONFIG.activeIntervalMs * 4);
  });

  it('caps the backoff at backoffCapMs before jitter', () => {
    const delay = computeDelay(
      { isBackgrounded: false, consecutiveFailures: 10, config: DEFAULT_CONFIG },
      () => 0.5,
    );
    expect(delay).toBe(DEFAULT_CONFIG.backoffCapMs);
  });

  it('applies jitter within the configured ratio around the capped delay', () => {
    const capped = DEFAULT_CONFIG.backoffCapMs;
    const low = computeDelay(
      { isBackgrounded: false, consecutiveFailures: 10, config: DEFAULT_CONFIG },
      () => 0,
    );
    const high = computeDelay(
      { isBackgrounded: false, consecutiveFailures: 10, config: DEFAULT_CONFIG },
      () => 1,
    );
    expect(low).toBeCloseTo(capped * (1 - DEFAULT_CONFIG.jitterRatio));
    expect(high).toBeCloseTo(capped * (1 + DEFAULT_CONFIG.jitterRatio));
  });
});

describe('resolveMutationMarker', () => {
  it('stores the returned marker when it equals held + 1', () => {
    expect(resolveMutationMarker(5, 6)).toEqual({ marker: 6, refetch: false });
  });

  it('discards the returned marker and asks for a refetch otherwise', () => {
    expect(resolveMutationMarker(5, 8)).toEqual({ marker: 5, refetch: true });
    expect(resolveMutationMarker(5, 5)).toEqual({ marker: 5, refetch: true });
  });
});

// --- part 2: createPollingEngine (R12-R15, R18-R20, R23-R26) ---

// Flushes the microtask queue so an unawaited `poll()` continuation (started
// directly by `start()`/`applyMutationMarker`, not through a fake timer) runs
// before the next assertion.
async function flush() {
  await Promise.resolve();
  await Promise.resolve();
}

function fakeVisibilitySource(initiallyBackgrounded = false) {
  let backgrounded = initiallyBackgrounded;
  const listeners = new Set();
  return {
    isBackgrounded: () => backgrounded,
    subscribe(cb) {
      listeners.add(cb);
      return () => listeners.delete(cb);
    },
    setBackgrounded(next) {
      backgrounded = next;
      for (const cb of listeners) cb();
    },
  };
}

function engineWith(fetchResource, overrides = {}) {
  const visibilitySource = overrides.visibilitySource ?? fakeVisibilitySource();
  return createPollingEngine(DEFAULT_CONFIG, {
    fetchResource,
    visibilitySource,
    random: () => 0.5,
    ...overrides,
  });
}

describe('createPollingEngine', () => {
  beforeEach(() => {
    vi.useFakeTimers();
  });

  afterEach(() => {
    vi.useRealTimers();
  });

  it('keeps data and marker on a 304 response', async () => {
    const fetchResource = vi.fn().mockResolvedValue({ status: 304, marker: null, body: null });
    const engine = engineWith(fetchResource);

    engine.start();
    await flush();

    expect(fetchResource).toHaveBeenCalledTimes(1);
    expect(engine.getSnapshot()).toEqual({ data: null, marker: null, connectionLost: false });
    engine.dispose();
  });

  it('replaces data and marker on a 200 response', async () => {
    const fetchResource = vi
      .fn()
      .mockResolvedValue({ status: 200, marker: 3, body: { items: [] } });
    const engine = engineWith(fetchResource);

    engine.start();
    await flush();

    expect(engine.getSnapshot()).toEqual({
      data: { items: [] },
      marker: 3,
      connectionLost: false,
    });
    engine.dispose();
  });

  it('never shares state between two engine instances', async () => {
    const fetchA = vi.fn().mockResolvedValue({ status: 200, marker: 1, body: 'a' });
    const fetchB = vi.fn().mockResolvedValue({ status: 200, marker: 9, body: 'b' });
    const engineA = engineWith(fetchA);
    const engineB = engineWith(fetchB);

    engineA.start();
    engineB.start();
    await flush();

    expect(engineA.getSnapshot().marker).toBe(1);
    expect(engineB.getSnapshot().marker).toBe(9);
    engineA.dispose();
    engineB.dispose();
  });

  it('polls immediately when the tab regains foreground (R18)', async () => {
    const visibilitySource = fakeVisibilitySource(true);
    const fetchResource = vi.fn().mockResolvedValue({ status: 304, marker: null, body: null });
    const engine = engineWith(fetchResource, { visibilitySource });

    engine.start();
    await flush();
    expect(fetchResource).toHaveBeenCalledTimes(1);

    visibilitySource.setBackgrounded(false);
    await flush();
    expect(fetchResource).toHaveBeenCalledTimes(2);
    engine.dispose();
  });

  it('flags connection loss after the failure threshold, clears it on success', async () => {
    let shouldFail = true;
    const fetchResource = vi.fn(() =>
      shouldFail
        ? Promise.reject(new Error('network down'))
        : Promise.resolve({ status: 304, marker: null, body: null }),
    );
    const engine = engineWith(fetchResource);

    engine.start();
    await flush();
    for (let i = 1; i < DEFAULT_CONFIG.connectionLostThreshold; i += 1) {
      // Fires exactly the one pending timer, unlike advanceTimersByTimeAsync,
      // which can cascade through several once-scheduled backoff timers.
      await vi.advanceTimersToNextTimerAsync();
    }

    expect(fetchResource).toHaveBeenCalledTimes(DEFAULT_CONFIG.connectionLostThreshold);
    expect(engine.getSnapshot().connectionLost).toBe(true); // R23

    shouldFail = false;
    await vi.advanceTimersToNextTimerAsync();
    expect(engine.getSnapshot().connectionLost).toBe(false); // R24
    engine.dispose();
  });

  it('applyMutationMarker stores held+1 without an extra fetch', async () => {
    const fetchResource = vi.fn().mockResolvedValue({ status: 200, marker: 5, body: {} });
    const engine = engineWith(fetchResource);
    engine.start();
    await flush();

    engine.applyMutationMarker(6); // 6 === 5 + 1
    await flush();

    expect(engine.getSnapshot().marker).toBe(6); // R25
    expect(fetchResource).toHaveBeenCalledTimes(1); // no refetch
    engine.dispose();
  });

  it('applyMutationMarker discards a mismatched marker and triggers a refetch', async () => {
    const fetchResource = vi.fn().mockResolvedValue({ status: 200, marker: 5, body: {} });
    const engine = engineWith(fetchResource);
    engine.start();
    await flush();

    engine.applyMutationMarker(9); // 9 !== 5 + 1
    await flush();

    expect(fetchResource).toHaveBeenCalledTimes(2); // R26
    expect(engine.getSnapshot().marker).toBe(5); // the refetch's own response wins
    engine.dispose();
  });
});
