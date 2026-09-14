import { describe, expect, it } from 'vitest';
import {
  CATEGORY_LABELS,
  DAY_LABELS,
  ROLE_LABELS,
  SLOT_LABELS,
  UNIT_LABELS,
} from '../../src/domain/labels.js';
import { INGREDIENT_CATEGORIES, UNITS } from '../../src/domain/wireCodes.js';

describe('labels', () => {
  it('maps every Unit wire code to its exact es-ES label (design.md section 6)', () => {
    expect(UNIT_LABELS).toEqual({
      g: 'g',
      ml: 'ml',
      unit: 'ud',
    });
    for (const unit of UNITS) {
      expect(typeof UNIT_LABELS[unit]).toBe('string');
      expect(UNIT_LABELS[unit].length).toBeGreaterThan(0);
    }
  });

  it('maps every IngredientCategory wire code to its exact es-ES label (design.md section 6)', () => {
    expect(CATEGORY_LABELS).toEqual({
      meat: 'Carne',
      fish: 'Pescado',
      carbohydrate: 'Carbohidratos',
      legume: 'Legumbres',
      vegetable: 'Vegetal',
      eggs: 'Huevos',
    });
    for (const category of INGREDIENT_CATEGORIES) {
      expect(typeof CATEGORY_LABELS[category]).toBe('string');
      expect(CATEGORY_LABELS[category].length).toBeGreaterThan(0);
    }
  });

  it('maps both Role wire codes to their exact es-ES label (R33, design.md section 5a)', () => {
    expect(ROLE_LABELS).toEqual({ Admin: 'Administrador', User: 'Usuario' });
  });

  it('maps both slot wire codes', () => {
    expect(SLOT_LABELS[1]).toBe('Comida');
    expect(SLOT_LABELS[2]).toBe('Cena');
  });

  it('maps all 7 day codes to distinct, non-empty weekday names', () => {
    const labels = [1, 2, 3, 4, 5, 6, 7].map((day) => DAY_LABELS[day]);

    labels.forEach((label) => {
      expect(typeof label).toBe('string');
      expect(label.length).toBeGreaterThan(0);
    });
    expect(new Set(labels).size).toBe(7);
  });

  it('orders day 1 as Monday, day 7 as Sunday, per Intl', () => {
    const formatter = new Intl.DateTimeFormat('es-ES', { weekday: 'long' });
    expect(DAY_LABELS[1]).toBe(formatter.format(new Date(Date.UTC(2024, 0, 1))));
    expect(DAY_LABELS[7]).toBe(formatter.format(new Date(Date.UTC(2024, 0, 7))));
  });
});
