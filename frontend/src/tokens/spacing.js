/**
 * Spacing scale, authored deliberately for this project (not lifted from the
 * prototype, which has 91 distinct padding values — drift, not a system; see
 * docs/frontend_prototype.md section 2.4).
 *
 * Six steps on a 4px/8px grid, the smallest scale that still separates
 * "tight" (inline gaps, badge padding) from "loose" (section spacing) without
 * inventing a value per component — plus an explicit `none` for zero, so that
 * every spacing value in a component is a named token with no literal `0`
 * (the acceptance criterion is unconditional).
 */

export const SPACE = {
  none: '0',
  xs: '4px',
  sm: '8px',
  md: '16px',
  lg: '24px',
  xl: '32px',
  xxl: '48px',
};
