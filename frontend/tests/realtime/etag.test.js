import { describe, expect, it } from 'vitest';
import { parseMarker, quoteMarker } from '../../src/realtime/etag.js';

describe('etag', () => {
  it('round-trips a marker through quote and parse', () => {
    expect(parseMarker(quoteMarker(41))).toBe(41);
    expect(quoteMarker(0)).toBe('"0"');
  });

  it.each([[null], [undefined], ['*'], ['41'], ['"41", "42"'], ['"nope"'], ['']])(
    'treats %s as no marker, never throws',
    (value) => {
      expect(parseMarker(value)).toBeNull();
    },
  );
});
