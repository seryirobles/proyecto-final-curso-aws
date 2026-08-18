/**
 * The app has exactly one locale. It is a constant, not a runtime setting,
 * and no i18n framework is added (docs/conventions.md section "Castilian
 * Spanish"; FR-UX-03).
 */
export const LOCALE = 'es-ES';

export function formatDate(date) {
  return new Intl.DateTimeFormat(LOCALE).format(date);
}

export function formatNumber(value) {
  return new Intl.NumberFormat(LOCALE).format(value);
}
