// The adaptive-polling decision logic (docs/architecture.md section 1.2.4,
// FR-RT-01/-02/-03). Framework-free — no React import, no DOM read of its own;
// `visibilitySource`/`fetchResource`/`random`/timers are all injected deps, the
// same "port, not a global" shape the backend gives `Clock` (design.md section 5).

// Tuning constants fixed at the spec gate (design.md section 6) - no FR/G pins
// a number, so these are the implementation detail, named rather than literal.
export const ACTIVE_INTERVAL_MS = 5000;
export const BACKGROUND_INTERVAL_MS = 30000;
export const BACKOFF_CAP_MS = 60000;
export const BACKOFF_JITTER_RATIO = 0.2;
export const CONNECTION_LOST_THRESHOLD = 3;

export const DEFAULT_CONFIG = {
  activeIntervalMs: ACTIVE_INTERVAL_MS,
  backgroundIntervalMs: BACKGROUND_INTERVAL_MS,
  backoffCapMs: BACKOFF_CAP_MS,
  jitterRatio: BACKOFF_JITTER_RATIO,
  connectionLostThreshold: CONNECTION_LOST_THRESHOLD,
};

export function computeDelay(
  { isBackgrounded, consecutiveFailures, config },
  random = Math.random,
) {
  const base = isBackgrounded ? config.backgroundIntervalMs : config.activeIntervalMs;
  if (consecutiveFailures <= 0) return base; // R16, R17 - no failures, no backoff
  const doubled = base * 2 ** consecutiveFailures; // R21 - doubled once per failure
  const capped = Math.min(doubled, config.backoffCapMs);
  const jitterFactor = 1 + (random() * 2 - 1) * config.jitterRatio; // R22
  return capped * jitterFactor;
}

export function resolveMutationMarker(heldMarker, returnedMarker) {
  if (returnedMarker === heldMarker + 1) {
    return { marker: returnedMarker, refetch: false }; // R25
  }
  return { marker: heldMarker, refetch: true }; // R26
}

const DEFAULT_DEPS = {
  setTimeoutFn: (...args) => globalThis.setTimeout(...args),
  clearTimeoutFn: (...args) => globalThis.clearTimeout(...args),
  random: Math.random,
};

export function createPollingEngine(config, deps) {
  const { fetchResource, visibilitySource, setTimeoutFn, clearTimeoutFn, random } = {
    ...DEFAULT_DEPS,
    ...deps,
  };

  // A single cached object, replaced (never mutated) only when a value
  // actually changes - `useSyncExternalStore` requires a stable reference
  // between real changes, or every render looks like a fresh store update.
  let snapshot = { data: null, marker: null, connectionLost: false };
  let consecutiveFailures = 0;
  let timerId = null;
  let inFlight = false;
  let disposed = false;
  let unsubscribeVisibility = null;
  let wasBackgrounded = false;
  const listeners = new Set();

  function notify() {
    for (const listener of listeners) listener();
  }

  function updateSnapshot(patch) {
    const next = { ...snapshot, ...patch };
    const changed =
      next.data !== snapshot.data ||
      next.marker !== snapshot.marker ||
      next.connectionLost !== snapshot.connectionLost;
    if (changed) {
      snapshot = next;
      notify();
    }
  }

  function scheduleNext() {
    if (disposed) return; // finding 2, fix round 2 - a disposed engine never re-arms
    const delay = computeDelay(
      { isBackgrounded: visibilitySource.isBackgrounded(), consecutiveFailures, config },
      random,
    );
    timerId = setTimeoutFn(poll, delay);
  }

  async function poll() {
    if (inFlight) return;
    inFlight = true;
    try {
      const result = await fetchResource(snapshot.marker);
      if (result.status === 200) {
        updateSnapshot({ data: result.body, marker: result.marker }); // R14
      } // 304 leaves data/marker unchanged (R13)
      consecutiveFailures = 0; // R20
      if (snapshot.connectionLost) updateSnapshot({ connectionLost: false }); // R24
    } catch {
      consecutiveFailures += 1; // R19
      if (consecutiveFailures >= config.connectionLostThreshold && !snapshot.connectionLost) {
        updateSnapshot({ connectionLost: true }); // R23
      }
    } finally {
      inFlight = false;
      scheduleNext();
    }
  }

  function pollNow() {
    if (disposed) return; // fix round 3 - a stale applyMutationMarker/visibility callback
    if (timerId !== null) clearTimeoutFn(timerId);
    poll();
  }

  function handleVisibilityNotification() {
    const isBackgroundedNow = visibilitySource.isBackgrounded();
    if (wasBackgrounded && !isBackgroundedNow) {
      pollNow(); // R18 - resume immediately, do not wait for a scheduled delay
    }
    wasBackgrounded = isBackgroundedNow;
  }

  return {
    subscribe(listener) {
      listeners.add(listener);
      return () => listeners.delete(listener);
    },
    getSnapshot() {
      return snapshot;
    },
    applyMutationMarker(returnedMarker) {
      const resolved = resolveMutationMarker(snapshot.marker, returnedMarker);
      updateSnapshot({ marker: resolved.marker });
      if (resolved.refetch) pollNow(); // R26
    },
    start() {
      wasBackgrounded = visibilitySource.isBackgrounded();
      unsubscribeVisibility = visibilitySource.subscribe(handleVisibilityNotification);
      poll();
    },
    dispose() {
      disposed = true;
      if (timerId !== null) clearTimeoutFn(timerId);
      if (unsubscribeVisibility) unsubscribeVisibility();
    },
  };
}
