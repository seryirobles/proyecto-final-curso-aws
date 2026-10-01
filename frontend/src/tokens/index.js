import { COLORS } from './colors.js';
import { SPACE } from './spacing.js';
import { FONT_SIZE } from './typography.js';
import { BREAKPOINT } from './breakpoints.js';
import { FONT_FAMILY } from './fontFamily.js';
import { RADIUS } from './borderRadius.js';
import { SHADOW } from './shadow.js';
import { LAYOUT } from './layout.js';
import { OPACITY } from './opacity.js';

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
  fontFamily: FONT_FAMILY,
  radius: RADIUS,
  shadow: SHADOW,
  layout: LAYOUT,
  opacity: OPACITY,
};
