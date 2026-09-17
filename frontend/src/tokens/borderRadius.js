/**
 * Border-radius tokens (design.md section 10.2): the prototype's 19 distinct
 * values read for intent, not copied - four visual roles cover all of them
 * without reintroducing the "drift, not a system" problem (docs/
 * frontend_prototype.md section 2.4).
 */

export const RADIUS = {
  none: '0',
  sm: '8px', // inputs, small buttons, chip-shaped controls
  md: '16px', // cards, day cells, dialogs, sheets
  lg: '24px', // large surfaces: bottom sheets, modal panels
  pill: '999px', // badges, circular icon buttons
};
