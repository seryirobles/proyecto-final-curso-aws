// jsdom has no matchMedia: evaluates `(min-width: Npx)` against `width`.

import { vi } from 'vitest';

export function mockViewport(width = 1440) {
  const state = { width, listeners: new Set() };
  window.matchMedia = vi.fn((query) => {
    const min = Number(/min-width:\s*(\d+)px/.exec(query)[1]);
    return {
      get matches() {
        return state.width >= min;
      },
      addEventListener: (_t, l) => state.listeners.add(l),
      removeEventListener: (_t, l) => state.listeners.delete(l),
    };
  });
  state.resize = (next) => {
    state.width = next;
    state.listeners.forEach((l) => l());
  };
  return state;
}
