// The only genuinely React piece of feature 26's transport (design.md
// section 5): wires one `createPollingEngine` instance to
// `useSyncExternalStore`. No decision logic of its own - every R12-R26 branch
// is proven at the engine/module level; this hook only proves the wiring.

import { useEffect, useMemo, useSyncExternalStore } from 'react';
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
  { createEngine = createPollingEngine } = {},
) {
  const engine = useMemo(
    () =>
      createEngine(config, {
        fetchResource: conditionalGet(url),
        visibilitySource: domVisibilitySource(),
      }),
    [url, config, createEngine],
  );

  useEffect(() => {
    engine.start();
    return () => engine.dispose();
  }, [engine]);

  const snapshot = useSyncExternalStore(engine.subscribe, engine.getSnapshot);
  return { ...snapshot, applyMutationMarker: engine.applyMutationMarker };
}
