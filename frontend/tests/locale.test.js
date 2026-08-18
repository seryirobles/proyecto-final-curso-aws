import { describe, expect, it } from 'vitest';
import { LOCALE, formatDate, formatNumber } from '../src/locale.js';

describe('locale', () => {
  it('exports the fixed es-ES locale as a constant', () => {
    expect(LOCALE).toBe('es-ES');
  });

  it('formats numbers with the es-ES decimal comma, never a decimal point', () => {
    const formatted = formatNumber(1.5);

    expect(formatted).toContain(',');
    expect(formatted).not.toContain('.');
  });

  it('formats dates through Intl.DateTimeFormat pinned to es-ES', () => {
    // Local (not UTC) components: formatDate() has no `timeZone` option, so
    // Intl.DateTimeFormat renders in the runner's local zone too. Building
    // the fixture from local components (instead of Date.UTC, which needs a
    // UTC->local conversion) keeps the assertion deterministic no matter the
    // runner's TZ — a UTC instant near midnight can roll onto a different
    // local day at extreme offsets (e.g. UTC+13/+14).
    const date = new Date(2026, 0, 15, 12);
    const formatted = formatDate(date);

    expect(formatted).toContain('2026');
    expect(formatted).toContain('15');
  });
});
