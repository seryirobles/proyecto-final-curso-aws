/**
 * Font-size scale, authored deliberately for this project (not lifted from
 * the prototype, which has 24 distinct font-size values including half-pixel
 * steps like 10.5px/11.5px — drift, not a system; see
 * docs/frontend_prototype.md section 2.4).
 *
 * Six steps on an approximate 1.25 (major third) ratio from a 16px body size,
 * rounded to whole pixels: enough range for a label through a page title
 * without a size per component.
 */

export const FONT_SIZE = {
  xs: '12px',
  sm: '14px',
  md: '16px',
  lg: '20px',
  xl: '25px',
  xxl: '31px',
};
