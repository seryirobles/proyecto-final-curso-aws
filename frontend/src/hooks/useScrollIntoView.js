// Scrolls an opened form into view once per target key (frontend_ux_phase1
// R10, R14). The key is the target's identity, not the object a poll rebuilds.

import { useEffect } from 'react';

export function useScrollIntoView(ref, key) {
  useEffect(() => {
    if (key == null) return;
    ref.current?.scrollIntoView?.({ block: 'start', behavior: 'smooth' });
  }, [ref, key]);
}
