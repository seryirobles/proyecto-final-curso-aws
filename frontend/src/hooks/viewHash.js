// View <-> URL hash mapping (frontend_ux_phase2 R45). Slugs are identifiers, not copy.

export const VIEW_SLUGS = {
  week: 'semana',
  library: 'biblioteca',
  rules: 'reglas',
  shoppingList: 'compra',
  summary: 'resumen',
};

export function viewToHash(view) {
  return `#/${VIEW_SLUGS[view]}`;
}

export function hashToView(hash) {
  return Object.keys(VIEW_SLUGS).find((view) => viewToHash(view) === hash) ?? null;
}
