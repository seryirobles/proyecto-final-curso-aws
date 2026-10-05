// Scrolls the window to the top when the active view changes, not on mount
// (frontend_ux_phase2 R17).

import { useEffect, useRef } from 'react';

export function useScrollToTop(view) {
  const previous = useRef(view);
  useEffect(() => {
    if (previous.current === view) return;
    previous.current = view;
    window.scrollTo(0, 0);
  }, [view]);
}
