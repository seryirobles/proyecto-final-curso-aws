// @vitest-environment jsdom
//
// Issue 10 (E2, E3): rule mutations must reach the view. Real usePolling + real
// engine; only the fetch boundary is faked.
import { act, renderHook } from '@testing-library/react';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { useRules } from '../../src/hooks/useRules.js';

// Minimal rules server, honouring `If-None-Match` exactly as
// rest_api_contract.md section 6 does; every mutation bumps the marker once.
function fakeRulesServer(initialRules) {
  let marker = 41;
  let rows = [...initialRules];
  return vi.fn(async (url, options = {}) => {
    const method = options.method ?? 'GET';
    if (url === '/v1/library/recipes') {
      return {
        status: 200,
        ok: true,
        headers: new Headers({ ETag: '"1"' }),
        json: async () => ({ recipes: [] }),
      };
    }
    if (url === '/v1/rules' && method === 'GET') {
      const held = options.headers?.['If-None-Match'];
      if (held === `"${marker}"`) {
        return { status: 304, ok: false, headers: new Headers({ ETag: held }) };
      }
      return {
        status: 200,
        ok: true,
        headers: new Headers({ ETag: `"${marker}"` }),
        json: async () => ({ rules: rows }),
      };
    }
    if (method === 'DELETE') {
      const ruleId = url.replace('/v1/rules/', '');
      rows = rows.filter((row) => `cat#${row.category}` !== ruleId);
      marker += 1;
      return { status: 204, ok: true, headers: new Headers({ ETag: `"${marker}"` }) };
    }
    if (method === 'PUT') {
      const rule = JSON.parse(options.body);
      rows = [...rows, rule];
      marker += 1;
      return {
        status: 200,
        ok: true,
        headers: new Headers({ ETag: `"${marker}"` }),
        json: async () => rule,
      };
    }
    throw new Error(`unexpected ${method} ${url}`);
  });
}

function categoryCount(category, count) {
  return { type: 'categoryCount', category, count };
}

async function settle() {
  await act(async () => {
    await vi.advanceTimersByTimeAsync(10); // well below one poll interval
  });
}

describe('useRules reflects its own mutations without a reload', () => {
  beforeEach(() => {
    vi.useFakeTimers();
  });

  afterEach(() => {
    vi.useRealTimers();
    vi.restoreAllMocks();
  });

  it('a confirmed rule delete drops it from the rendered list (E3)', async () => {
    globalThis.fetch = fakeRulesServer([categoryCount('meat', 2), categoryCount('fish', 1)]);
    const { result } = renderHook(() => useRules());
    await settle();
    expect(result.current.categoryCounts.map((r) => r.category)).toEqual(['meat', 'fish']);

    act(() => result.current.remove(categoryCount('meat', 2)));
    await act(async () => result.current.confirm.confirm());
    await settle();

    expect(result.current.categoryCounts.map((r) => r.category)).toEqual(['fish']);
    expect(result.current.error).toBeNull();
  });

  it('a saved category-count rule appears in the rendered list (E2)', async () => {
    globalThis.fetch = fakeRulesServer([]);
    const { result } = renderHook(() => useRules());
    await settle();

    act(() => result.current.setCategoryCountCategory('meat'));
    act(() => result.current.setCategoryCountCount('2'));
    await act(async () => result.current.saveCategoryCount());
    await settle();

    expect(result.current.categoryCounts.map((r) => r.category)).toEqual(['meat']);
  });
});
