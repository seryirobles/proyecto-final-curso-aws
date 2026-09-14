// Wraps `window.matchMedia` so a breakpoint becomes a state value, never a
// literal in a component (design.md section 4.3; R17,
// docs/conventions.md "The responsive constraint").

import { useEffect, useState } from 'react';

export function useBreakpoint(query) {
  const [matches, setMatches] = useState(() => window.matchMedia(query).matches);

  useEffect(() => {
    const mql = window.matchMedia(query);
    const onChange = () => setMatches(mql.matches);
    mql.addEventListener('change', onChange);
    return () => mql.removeEventListener('change', onChange);
  }, [query]);

  return matches;
}
