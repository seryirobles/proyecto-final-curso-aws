/**
 * Breakpoint tokens for `window.matchMedia` (inline styles cannot express
 * `@media`; docs/conventions.md "The responsive constraint"). Thresholds feed
 * `useViewport` (frontend_ux_phase2 R7): 600 narrow, 768 medium, 1280 wide.
 */

export const BREAKPOINT = {
  tablet: 600,
  medium: 768,
  desktop: 1280,
};
