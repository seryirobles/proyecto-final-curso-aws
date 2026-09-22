// @vitest-environment jsdom
//
// Issue 10 (E1, E11): a library delete must leave the view without the row.
// Real usePolling + real engine; only the fetch boundary is faked, because
// the defect lives in the marker/refetch interaction, not in useLibrary.
import { act, renderHook } from '@testing-library/react';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { useLibrary } from '../../src/hooks/useLibrary.js';

function recipe(id) {
  return {
    id,
    author: 'Marta',
    name: `Receta ${id}`,
    category: 'legume',
    servings: 4,
    estimatedTime: '30 min',
    ingredients: [],
    tools: [],
    procedure: [],
  };
}

// Minimal library server: one marker, bumped `markerStep` per mutation,
// honouring `If-None-Match` exactly as rest_api_contract.md section 6 does.
function fakeLibraryServer({ recipes, markerStep = 1 }) {
  let marker = 41;
  let rows = [...recipes];
  return vi.fn(async (url, options = {}) => {
    const method = options.method ?? 'GET';
    if (url === '/v1/library/recipes' && method === 'GET') {
      const held = options.headers?.['If-None-Match'];
      if (held === `"${marker}"`) {
        return { status: 304, ok: false, headers: new Headers({ ETag: held }) };
      }
      return {
        status: 200,
        ok: true,
        headers: new Headers({ ETag: `"${marker}"` }),
        json: async () => ({ recipes: rows }),
      };
    }
    if (method === 'DELETE') {
      rows = rows.filter((row) => url !== `/v1/library/recipes/${row.id}`);
      marker += markerStep;
      return { status: 204, ok: true, headers: new Headers({ ETag: `"${marker}"` }) };
    }
    throw new Error(`unexpected ${method} ${url}`);
  });
}

async function settle() {
  await act(async () => {
    await vi.advanceTimersByTimeAsync(10); // well below one poll interval
  });
}

describe('useLibrary reflects its own mutations without a reload', () => {
  beforeEach(() => {
    vi.useFakeTimers();
  });

  afterEach(() => {
    vi.useRealTimers();
    vi.restoreAllMocks();
  });

  it('a confirmed delete removes the recipe from the rendered list (E1)', async () => {
    globalThis.fetch = fakeLibraryServer({ recipes: [recipe('r-1'), recipe('r-2')] });
    const { result } = renderHook(() => useLibrary());
    await settle();
    expect(result.current.recipes.map((row) => row.id)).toEqual(['r-1', 'r-2']);

    act(() => result.current.remove('r-1'));
    await act(async () => result.current.confirm.confirm());
    await settle();

    expect(result.current.recipes.map((row) => row.id)).toEqual(['r-2']);
    expect(result.current.error).toBeNull();
  });

  it('a delete whose marker jumps by more than one still refreshes the list (E11)', async () => {
    // The R26 branch - already correct today; guards against a fix that
    // repairs E1 by dropping the discard-and-refetch path.
    globalThis.fetch = fakeLibraryServer({
      recipes: [recipe('r-1'), recipe('r-2')],
      markerStep: 3,
    });
    const { result } = renderHook(() => useLibrary());
    await settle();

    act(() => result.current.remove('r-1'));
    await act(async () => result.current.confirm.confirm());
    await settle();

    expect(result.current.recipes.map((row) => row.id)).toEqual(['r-2']);
  });
});
