/**
 * Font-family tokens (design.md section 10.1): three distinct type roles
 * mined from the prototype's intent, not its literal CSS - Baloo 2 for
 * headings, Nunito for body text, DM Mono for labels/metadata. Each keeps a
 * real system-font fallback so text renders before, or if, the self-hosted
 * face (fonts.js) finishes loading.
 */

export const FONT_FAMILY = {
  heading: '"Baloo 2", ui-rounded, "Segoe UI", sans-serif',
  body: '"Nunito", "Segoe UI", ui-sans-serif, sans-serif',
  label: '"DM Mono", ui-monospace, "Cascadia Mono", monospace',
};
