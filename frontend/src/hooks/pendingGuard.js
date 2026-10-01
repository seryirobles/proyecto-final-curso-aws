// In-flight guard for hook mutations (frontend_ux_phase1 R31, R32). A ref
// decides, because two taps in one tick both see stale state.

import { useCallback, useRef, useState } from 'react';

export function usePendingGuard() {
  const inFlight = useRef(new Set());
  const [pending, setPending] = useState(() => new Set());

  const release = useCallback((key) => {
    inFlight.current.delete(key);
    setPending(new Set(inFlight.current));
  }, []);

  const run = useCallback(
    (key, fn) => {
      if (inFlight.current.has(key)) return undefined;
      inFlight.current.add(key);
      setPending(new Set(inFlight.current));
      let result;
      try {
        result = fn();
      } catch (err) {
        release(key);
        throw err;
      }
      return Promise.resolve(result).finally(() => release(key));
    },
    [release],
  );

  const isPending = useCallback((key) => pending.has(key), [pending]);

  return { run, isPending, pending };
}
