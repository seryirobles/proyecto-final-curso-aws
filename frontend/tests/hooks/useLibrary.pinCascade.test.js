// @vitest-environment jsdom
//
// Feature 30 (R1-R4, R6, R7): the pin-cascade delete warning + retry.
// Real usePolling + real engine; only the fetch boundary is faked, following
// useLibrary.mutationVisibility.test.js's pattern (design.md section 6).
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

// DELETE answers per `rejections[id]` on the plain attempt; a
// `?confirmCascade=true` retry succeeds unless `cascadeRejections[id]` names
// its own rejection - the two-step cascade rest_api_contract.md section 3.4
// defines, plus the retry's own failure mode (T3).
function fakeLibraryServer({ recipes, rejections = {}, cascadeRejections = {} }) {
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
      const [path, query] = url.split('?');
      const id = path.replace('/v1/library/recipes/', '');
      const confirmCascade = query === 'confirmCascade=true';
      const rejection = confirmCascade ? cascadeRejections[id] : rejections[id];
      if (rejection) {
        return {
          status: rejection.status,
          ok: false,
          headers: new Headers(),
          json: async () => ({
            code: rejection.code,
            detail: rejection.detail,
            details: rejection.details,
          }),
        };
      }
      rows = rows.filter((row) => row.id !== id);
      marker += 1;
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

function deleteCalls(fetchMock) {
  return fetchMock.mock.calls.filter(([, options]) => options?.method === 'DELETE');
}

describe('useLibrary pin-cascade delete', () => {
  beforeEach(() => {
    vi.useFakeTimers();
  });

  afterEach(() => {
    vi.useRealTimers();
    vi.restoreAllMocks();
  });

  it('a 409 opens a second confirmation naming the pin, and confirming retries with confirmCascade=true until the recipe is gone (R1, R2, R3, R6)', async () => {
    globalThis.fetch = fakeLibraryServer({
      recipes: [recipe('r-1')],
      rejections: {
        'r-1': {
          status: 409,
          code: 'PIN_RULES_AFFECTED',
          detail: 'No se puede eliminar.',
          details: { pins: [{ day: 7, slot: 1 }] },
        },
      },
    });
    const { result } = renderHook(() => useLibrary());
    await settle();

    act(() => result.current.remove('r-1'));
    await act(async () => result.current.confirm.confirm()); // first dialog -> 409

    expect(result.current.confirm.pending).not.toBeNull();
    expect(result.current.confirm.pending.message).toContain('domingo');
    expect(result.current.confirm.pending.message).toContain('Comida');
    // R5: the first attempt never sends confirmCascade.
    expect(deleteCalls(globalThis.fetch)[0][0]).toBe('/v1/library/recipes/r-1');

    await act(async () => result.current.confirm.confirm()); // second dialog -> cascade retry
    await settle();

    expect(result.current.recipes.map((row) => row.id)).toEqual([]);
    expect(deleteCalls(globalThis.fetch)).toHaveLength(2);
    expect(deleteCalls(globalThis.fetch)[1][0]).toBe('/v1/library/recipes/r-1?confirmCascade=true');
  });

  it("the cascade retry's own rejection sets error to detail verbatim, recipe untouched (T3)", async () => {
    globalThis.fetch = fakeLibraryServer({
      recipes: [recipe('r-4')],
      rejections: {
        'r-4': {
          status: 409,
          code: 'PIN_RULES_AFFECTED',
          detail: 'No se puede eliminar.',
          details: { pins: [{ day: 3, slot: 2 }] },
        },
      },
      cascadeRejections: {
        'r-4': { status: 404, code: 'NOT_FOUND', detail: 'X' },
      },
    });
    const { result } = renderHook(() => useLibrary());
    await settle();

    act(() => result.current.remove('r-4'));
    await act(async () => result.current.confirm.confirm()); // first dialog -> 409
    expect(result.current.confirm.pending).not.toBeNull();

    await act(async () => result.current.confirm.confirm()); // second dialog -> cascade retry rejected
    await settle();

    expect(result.current.error).toBe('X');
    expect(result.current.recipes.map((row) => row.id)).toEqual(['r-4']);
  });

  it('cancelling the second confirmation issues no retry and leaves the recipe (R4)', async () => {
    globalThis.fetch = fakeLibraryServer({
      recipes: [recipe('r-2')],
      rejections: {
        'r-2': {
          status: 409,
          code: 'PIN_RULES_AFFECTED',
          detail: 'No se puede eliminar.',
          details: { pins: [{ day: 1, slot: 2 }] },
        },
      },
    });
    const { result } = renderHook(() => useLibrary());
    await settle();

    act(() => result.current.remove('r-2'));
    await act(async () => result.current.confirm.confirm()); // first dialog -> 409
    expect(result.current.confirm.pending).not.toBeNull();

    act(() => result.current.confirm.cancel());
    await settle();

    expect(deleteCalls(globalThis.fetch)).toHaveLength(1);
    expect(result.current.recipes.map((row) => row.id)).toEqual(['r-2']);
  });

  it('a non-cascade rejection sets error to detail verbatim, no second dialog (R7)', async () => {
    globalThis.fetch = fakeLibraryServer({
      recipes: [recipe('r-3')],
      rejections: {
        'r-3': { status: 409, code: 'DUPLICATE', detail: 'Ya existe.' },
      },
    });
    const { result } = renderHook(() => useLibrary());
    await settle();

    act(() => result.current.remove('r-3'));
    await act(async () => result.current.confirm.confirm());

    expect(result.current.error).toBe('Ya existe.');
    expect(result.current.confirm.pending).toBeNull();
    expect(result.current.recipes.map((row) => row.id)).toEqual(['r-3']);
  });
});
