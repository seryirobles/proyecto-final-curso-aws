/**
 * Breakpoint tokens for `window.matchMedia` (inline styles cannot express
 * `@media`; docs/conventions.md section "The responsive constraint"). Only
 * two thresholds: this project needs one place the week grid collapses to a
 * day-by-day view (tablet) and one place it gets a wider desktop layout
 * (desktop). A third step would not correspond to any known layout change.
 */

export const BREAKPOINT = {
  tablet: 600,
  desktop: 1024,
};
