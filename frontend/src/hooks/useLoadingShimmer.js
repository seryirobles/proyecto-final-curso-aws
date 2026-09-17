// Drives LoadingState's shimmer sweep with a boolean tick - no CSS
// `@keyframes` under the no-stylesheet rule (design.md section 10).

import { useEffect, useState } from 'react';

const TICK_MS = 600;

export function useLoadingShimmer() {
  const [pulse, setPulse] = useState(false);

  useEffect(() => {
    const id = globalThis.setInterval(() => setPulse((value) => !value), TICK_MS);
    return () => globalThis.clearInterval(id);
  }, []);

  return pulse;
}
