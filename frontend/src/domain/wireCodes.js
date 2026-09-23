/**
 * Frontend-side mirror of the backend's closed wire vocabularies (design.md
 * section 0, T4a). Source of truth stays
 * `backend/core/src/planner_core/domain/units.py` and
 * `ingredient_category.py` - the frontend toolchain cannot import Python, so
 * this file lists the same string values by hand. Adds no new value.
 */

export const UNITS = ['g', 'ml', 'unit'];

export const INGREDIENT_CATEGORIES = [
  'meat',
  'fish',
  'carbohydrate',
  'legume',
  'vegetable',
  'eggs',
];

// Mirrors planner_core/domain/role.py's Role StrEnum values.
export const ROLE_FROM_WIRE = { admin: 'Admin', user: 'User' };

export function roleFromWire(wireRole) {
  return ROLE_FROM_WIRE[wireRole] ?? null;
}
