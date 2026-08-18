import { COLORS } from './colors.js';
import { SPACE } from './spacing.js';
import { FONT_SIZE } from './typography.js';
import { BREAKPOINT } from './breakpoints.js';

/**
 * Single design-tokens module (docs/conventions.md section "Styling: inline
 * CSS"): every colour, spacing, font size and breakpoint referenced by name,
 * never as a literal in a component's `style` object.
 */
export const tokens = {
  color: COLORS,
  space: SPACE,
  fontSize: FONT_SIZE,
  breakpoint: BREAKPOINT,
};
