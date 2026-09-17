// es-ES display labels for the already-decided wire codes (design.md section
// 4.5/6). Maps code -> label only, never the reverse - the wire never
// receives a label (rest_api_contract.md section 3.0 rule 1).

import { LOCALE } from '../locale.js';

export const UNIT_LABELS = {
  g: 'g',
  ml: 'ml',
  unit: 'ud',
};

// design.md section 5a - admin account list role text (R33).
export const ROLE_LABELS = {
  Admin: 'Administrador',
  User: 'Usuario',
};

export const CATEGORY_LABELS = {
  meat: 'Carne',
  fish: 'Pescado',
  carbohydrate: 'Carbohidratos',
  legume: 'Legumbres',
  vegetable: 'Vegetal',
  eggs: 'Huevos',
};

// Decorative-only category dot (T85, design.md 10.6) - arbitrary assignment
// across 6 categories (5 accent tokens + `eggs`'s neutral `ink2`), no domain
// meaning; a category is domain vocabulary, not a design token.
export const CATEGORY_COLORS = {
  meat: 'terra',
  fish: 'aub',
  carbohydrate: 'honey',
  legume: 'olive',
  vegetable: 'terraDeep',
  eggs: 'ink2',
};

// Intl has no concept of "lunch/dinner" (design.md section 3) - the one pair
// of literal labels the fixed slot wire codes need.
export const SLOT_LABELS = {
  1: 'Comida',
  2: 'Cena',
};

// day 1-7, Monday = 1 (rest_api_contract.md section 2, isocalendar order).
// 2024-01-01 (UTC) was an ISO Monday - a fixed anchor, not "this week".
const WEEKDAY_FORMATTER = new Intl.DateTimeFormat(LOCALE, { weekday: 'long' });
const ISO_MONDAY_UTC = Date.UTC(2024, 0, 1);
const DAY_MS = 24 * 60 * 60 * 1000;

export const DAY_LABELS = Object.fromEntries(
  [1, 2, 3, 4, 5, 6, 7].map((day) => [
    day,
    WEEKDAY_FORMATTER.format(new Date(ISO_MONDAY_UTC + (day - 1) * DAY_MS)),
  ]),
);
