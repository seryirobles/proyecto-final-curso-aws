// R45, R50: view <-> URL hash mapping.
import { describe, expect, it } from 'vitest';
import { hashToView, viewToHash } from '../../src/hooks/viewHash.js';

const PAIRS = [
  ['week', '#/semana'],
  ['library', '#/biblioteca'],
  ['rules', '#/reglas'],
  ['shoppingList', '#/compra'],
  ['summary', '#/resumen'],
];

describe('viewHash', () => {
  it.each(PAIRS)('maps %s to %s and back', (view, hash) => {
    expect(viewToHash(view)).toBe(hash);
    expect(hashToView(hash)).toBe(view);
  });

  it.each(['', '#', '#/', '#/nope', '#semana', '#/semana/x', undefined])(
    'returns null for %j',
    (hash) => {
      expect(hashToView(hash)).toBeNull();
    },
  );
});
