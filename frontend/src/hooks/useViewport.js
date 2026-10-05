// One viewport tier from the breakpoint tokens (frontend_ux_phase2 R1-R7);
// called once, in App, and passed down as a `viewport` prop.

import { tokens } from '../tokens/index.js';
import { useBreakpoint } from './useBreakpoint.js';

export const VIEWPORT = {
  COMPACT: 'compact',
  NARROW: 'narrow',
  MEDIUM: 'medium',
  WIDE: 'wide',
};

export function useViewport() {
  const tablet = useBreakpoint(`(min-width: ${tokens.breakpoint.tablet}px)`);
  const medium = useBreakpoint(`(min-width: ${tokens.breakpoint.medium}px)`);
  const desktop = useBreakpoint(`(min-width: ${tokens.breakpoint.desktop}px)`);
  if (desktop) return VIEWPORT.WIDE;
  if (medium) return VIEWPORT.MEDIUM;
  return tablet ? VIEWPORT.NARROW : VIEWPORT.COMPACT;
}
