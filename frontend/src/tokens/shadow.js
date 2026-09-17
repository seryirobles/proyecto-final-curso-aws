/**
 * Shadow/elevation tokens (design.md section 10.3): three "how raised" steps
 * mined from the prototype's own layering, colour derived from `ink`
 * (colors.js) at low alpha rather than a generic black, so it reads warm
 * and consistent with the rest of the palette.
 */

export const SHADOW = {
  none: 'none',
  sm: '0 1px 3px rgba(40, 51, 31, 0.12)', // cards, day cells, rows
  md: '0 6px 16px rgba(40, 51, 31, 0.16)', // dropdowns, popovers, dialogs
  lg: '0 16px 40px rgba(40, 51, 31, 0.22)', // bottom sheets, toasts
};
