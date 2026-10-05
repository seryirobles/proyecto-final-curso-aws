// Shared native-control styles for the rule/shopping-list/account views.
// Prototype line refs and the card/heading dedup rationale live in
// progress/impl_frontend_spa.md's "Fix round" entries.

import { tokens } from './index.js';

// Prototype line 257-259: text/number inputs and `<select>` share one
// visual treatment, so both use this object.
export const selectStyle = {
  border: `1px solid ${tokens.color.line2}`,
  backgroundColor: tokens.color.surface2,
  borderRadius: tokens.radius.sm,
  padding: `${tokens.space.xs} ${tokens.space.sm}`,
  fontWeight: 600,
  boxSizing: 'border-box',
  fontSize: tokens.fontSize.input,
  color: tokens.color.ink,
};

export const inputStyle = selectStyle;

// Disabled look for submit buttons whose inline colours would hide it (R30).
export const disabledStyle = { opacity: tokens.opacity.disabled, cursor: 'not-allowed' };

export function primaryButtonStyle(disabled) {
  return {
    ...(disabled ? disabledStyle : null),
    border: 'none',
    backgroundColor: disabled ? tokens.color.line2 : tokens.color.terra,
    color: disabled ? tokens.color.ink3 : tokens.color.surface,
    borderRadius: tokens.radius.sm,
    padding: `${tokens.space.sm} ${tokens.space.md}`,
    fontWeight: 700,
  };
}

export const secondaryButtonStyle = {
  border: `1px solid ${tokens.color.line2}`,
  backgroundColor: tokens.color.surface,
  color: tokens.color.ink2,
  borderRadius: tokens.radius.sm,
  padding: `${tokens.space.xs} ${tokens.space.sm}`,
  fontWeight: 600,
};

export const ghostButtonStyle = {
  border: 'none',
  backgroundColor: 'transparent',
  color: tokens.color.ink3,
  padding: `${tokens.space.xs} ${tokens.space.sm}`,
  fontWeight: 600,
};

export const listResetStyle = {
  listStyle: 'none',
  margin: tokens.space.none,
  padding: tokens.space.none,
};

export const listRowStyle = {
  display: 'flex',
  alignItems: 'center',
  justifyContent: 'space-between',
  gap: tokens.space.sm,
  padding: `${tokens.space.sm} ${tokens.space.md}`,
  borderTop: `1px solid ${tokens.color.line}`,
};

// Rule-group heading accent dot (line 310/323/347's `<span>`), one fixed
// colour per RulesView group - not a per-item map like CATEGORY_COLORS.
export const accentDotStyle = (color) => ({
  width: '8px',
  height: '8px',
  borderRadius: tokens.radius.pill,
  backgroundColor: color,
  flex: 'none',
});

// Card wrapper shared by RulesView/ShoppingListView/AccountRow/
// AdminAccountsView (fix round finding 5) - background/border/radius/
// shadow/padding only; callers add their own layout/margin on top.
export const cardStyle = {
  backgroundColor: tokens.color.surface,
  border: `1px solid ${tokens.color.line}`,
  borderRadius: tokens.radius.md,
  boxShadow: tokens.shadow.sm,
  padding: tokens.space.sm,
};

// Week day-card grid columns per viewport tier (frontend_ux_phase2 R26-R28).
export function weekGridColumns(viewport) {
  if (viewport === 'wide') return 'repeat(7, minmax(0, 1fr))';
  if (viewport === 'medium') return 'repeat(4, minmax(0, 1fr))';
  return 'minmax(0, 1fr)';
}

// Minimum touch target: 44 px below 768 px, 24 px from 768 px (frontend_ux_phase2 R41-R43).
export function targetStyle(viewport) {
  const size =
    viewport === 'compact' || viewport === 'narrow'
      ? tokens.layout.targetMobile
      : tokens.layout.targetDesktop;
  return { minHeight: size, minWidth: size };
}

export const headingStyle = {
  margin: tokens.space.none,
  fontFamily: tokens.fontFamily.heading,
};
