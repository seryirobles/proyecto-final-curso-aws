// The only genuinely React piece of feature 26's transport (design.md
// section 5): wires one `createPollingEngine` instance to
// `useSyncExternalStore`. No decision logic of its own - every R12-R26 branch
// is proven at the engine/module level; this hook only proves the wiring.

import { useEffect, useMemo, useState, useSyncExternalStore } from 'react';
import { conditionalGet } from '../realtime/conditionalGet.js';
import { DEFAULT_CONFIG, createPollingEngine } from '../realtime/pollingEngine.js';

function domVisibilitySource() {
  return {
    isBackgrounded: () => document.hidden || !document.hasFocus(),
    subscribe(callback) {
      document.addEventListener('visibilitychange', callback);
      window.addEventListener('blur', callback);
      window.addEventListener('focus', callback);
      return () => {
        document.removeEventListener('visibilitychange', callback);
        window.removeEventListener('blur', callback);
        window.removeEventListener('focus', callback);
      };
    },
  };
}

export function usePolling(
  url,
  config = DEFAULT_CONFIG,
  { createEngine = createPollingEngine, enabled = true } = {},
) {
  // A disposed engine never re-arms, so a re-enable needs a fresh instance.
  // See progress/impl_frontend_spa.md > "Library slice — Fix round 3".
  const [generation, setGeneration] = useState(0);
  const [wasEnabled, setWasEnabled] = useState(enabled);
  if (enabled !== wasEnabled) {
    setWasEnabled(enabled);
    if (enabled) setGeneration((g) => g + 1);
  }

  const engine = useMemo(
    () =>
      createEngine(config, {
        fetchResource: conditionalGet(url),
        visibilitySource: domVisibilitySource(),
      }),
    // `generation` intentionally forces a fresh engine on re-enable; it is a
    // cache-busting key, not a value the factory reads.
    // eslint-disable-next-line react-hooks/exhaustive-deps
    [url, config, createEngine, generation],
  );

  // `enabled` gates start()/dispose() only - the engine itself is created on
  // every generation bump (cheap, no network) whether or not it starts.
  useEffect(() => {
    if (!enabled) return undefined;
    engine.start();
    return () => engine.dispose();
  }, [engine, enabled]);

  const snapshot = useSyncExternalStore(engine.subscribe, engine.getSnapshot);
  return {
    ...snapshot,
    applyMutationMarker: engine.applyMutationMarker,
    refetchNow: engine.refetchNow, // issue ui-not-reflecting-mutations
  };
}
