// @vitest-environment jsdom
//
// Issue 6 (new-recipe-not-shown-in-library), E1-E3. Real hooks and a real
// polling engine; only the network boundary is faked, because the defect is
// the interaction between the mutation's ETag and the next conditional GET
// (docs/rest_api_contract.md section 6).
import { act, renderHook } from '@testing-library/react';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';

import { useLibrary } from '../../src/hooks/useLibrary.js';

const INITIAL_MARKER = 41;

function entry(id, name) {
  return {
    id,
    author: 'Marta',
    name,
    category: 'legume',
    servings: 4,
    estimatedTime: '30 min',
    ingredients: [],
    tools: [],
    procedure: [],
  };
}

function response(status, body, marker) {
  return {
    status,
    ok: status >= 200 && status < 300,
    headers: new Headers({ ETag: `"${marker}"` }),
    json: async () => body,
  };
}

// Marker semantics of the real API: every write bumps it by exactly one and
// the mutation response carries the new value (docs/data_model.md 1.1).
function createFakeApi(initialRecipes) {
  let marker = INITIAL_MARKER;
  let recipes = initialRecipes;
  const requests = [];

  return {
    get requests() {
      return requests;
    },
    fetch: vi.fn(async (url, options = {}) => {
      const method = options.method ?? 'GET';
      const ifNoneMatch = new Headers(options.headers ?? {}).get('If-None-Match');
      requests.push({ url, method, ifNoneMatch });

      if (method === 'GET') {
        if (ifNoneMatch === `"${marker}"`) return response(304, null, marker);
        return response(200, { recipes }, marker);
      }
      if (method === 'POST') {
        const created = { ...entry('r-2', ''), ...JSON.parse(options.body).recipe, id: 'r-2' };
        recipes = [...recipes, created];
        marker += 1;
        return response(201, { ...created, duplicateWarning: false }, marker);
      }
      if (method === 'PUT') {
        const id = url.split('/').pop();
        const updated = { ...entry(id, ''), ...JSON.parse(options.body).recipe, id };
        recipes = recipes.map((r) => (r.id === id ? updated : r));
        marker += 1;
        return response(200, { ...updated, duplicateWarning: false }, marker);
      }
      throw new Error(`unexpected ${method} ${url}`);
    }),
  };
}

async function settle(ms = 60_000) {
  await act(async () => {
    await vi.advanceTimersByTimeAsync(ms);
  });
}

describe('library view after its own mutation', () => {
  let api;

  beforeEach(() => {
    vi.useFakeTimers();
    api = createFakeApi([entry('r-1', 'Lentejas')]);
    globalThis.fetch = api.fetch;
  });

  afterEach(() => {
    vi.useRealTimers();
    vi.restoreAllMocks();
  });

  async function renderLibrary() {
    const rendered = renderHook(() => useLibrary());
    await settle(0);
    expect(rendered.result.current.recipes.map((r) => r.name)).toEqual(['Lentejas']);
    return rendered;
  }

  // Non-empty sections (issue recipe-saved-without-required-sections, G-89,
  // landed after this test was staged): fixture-only addition, no assertion
  // touched - collateral, same pattern as useLibrary.test.js's own fix.
  function fillRequiredSections(result) {
    act(() => result.current.authoring.addIngredient());
    act(() => result.current.authoring.updateIngredient(0, 'name', 'lentejas'));
    act(() => result.current.authoring.updateIngredient(0, 'quantity', '300'));
    act(() => result.current.authoring.updateIngredient(0, 'unit', 'g'));
    act(() => result.current.authoring.addTool());
    act(() => result.current.authoring.updateTool(0, 'olla'));
    act(() => result.current.authoring.addProcedureStep());
    act(() => result.current.authoring.updateProcedureStep(0, 'Cocer las lentejas.'));
  }

  it('E1: a recipe created from the library view appears in it without a reload', async () => {
    const { result } = await renderLibrary();

    act(() => result.current.openAdd());
    act(() => result.current.authoring.updateField('name', 'Tortilla'));
    act(() => result.current.authoring.updateField('category', 'eggs'));
    fillRequiredSections(result);
    await act(async () => result.current.authoring.submit());
    await settle();

    expect(result.current.recipes.map((r) => r.name)).toEqual(['Lentejas', 'Tortilla']);
  });

  it('E2: an edit made from the library view appears in it without a reload', async () => {
    const { result } = await renderLibrary();

    act(() => result.current.openEdit(entry('r-1', 'Lentejas')));
    act(() => result.current.authoring.updateField('name', 'Lentejas estofadas'));
    fillRequiredSections(result);
    await act(async () => result.current.authoring.submit());
    await settle();

    expect(result.current.recipes.map((r) => r.name)).toEqual(['Lentejas estofadas']);
  });

  it('E3: polling stays conditional on the post-mutation marker', async () => {
    const { result } = await renderLibrary();

    act(() => result.current.openAdd());
    act(() => result.current.authoring.updateField('name', 'Tortilla'));
    act(() => result.current.authoring.updateField('category', 'eggs'));
    fillRequiredSections(result);
    await act(async () => result.current.authoring.submit());
    await settle();

    const lastGet = api.requests.filter((r) => r.method === 'GET').at(-1);
    expect(lastGet.ifNoneMatch).toBe(`"${INITIAL_MARKER + 1}"`);
  });
});
