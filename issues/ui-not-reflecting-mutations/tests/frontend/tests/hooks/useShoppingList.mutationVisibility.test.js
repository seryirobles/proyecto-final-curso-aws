// @vitest-environment jsdom
//
// Issue 10 (E4-E8): every shopping-list mutation must reach the view. Real
// usePolling + real engine; only the fetch boundary is faked, because the
// defect lives in the marker/refetch interaction, not in useShoppingList.
import { act, renderHook } from '@testing-library/react';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { useShoppingList } from '../../src/hooks/useShoppingList.js';

const LIVE_WEEKS = {
  today: '2026-08-17',
  current: { weekId: '2026-W34', monday: '2026-08-17', sunday: '2026-08-23' },
  next: { weekId: '2026-W35', monday: '2026-08-24', sunday: '2026-08-30' },
};

function item(id, overrides = {}) {
  return { id, name: `Item ${id}`, quantity: 2, unit: 'g', checked: false, ...overrides };
}

// Minimal shopping-list server, honouring `If-None-Match` exactly as
// rest_api_contract.md section 6 does; every mutation bumps the marker once.
function fakeShoppingServer(initialItems) {
  let marker = 41;
  let rows = [...initialItems];
  let nextId = 900;
  return vi.fn(async (url, options = {}) => {
    const method = options.method ?? 'GET';
    if (url === '/v1/live-weeks') {
      return { status: 200, ok: true, headers: new Headers(), json: async () => LIVE_WEEKS };
    }
    if (url === '/v1/shopping-list' && method === 'GET') {
      const held = options.headers?.['If-None-Match'];
      if (held === `"${marker}"`) {
        return { status: 304, ok: false, headers: new Headers({ ETag: held }) };
      }
      return {
        status: 200,
        ok: true,
        headers: new Headers({ ETag: `"${marker}"` }),
        json: async () => ({ items: rows }),
      };
    }
    if (url === '/v1/shopping-list/resync' && method === 'POST') {
      rows = [...rows, item('auto-1', { name: 'lentejas', quantity: 300 })];
      marker += 1;
      return {
        status: 200,
        ok: true,
        headers: new Headers({ ETag: `"${marker}"` }),
        json: async () => ({ items: rows }),
      };
    }
    if (url === '/v1/shopping-list/items' && method === 'POST') {
      const body = JSON.parse(options.body);
      const created = { id: `i-${(nextId += 1)}`, checked: false, ...body };
      rows = [...rows, created];
      marker += 1;
      return {
        status: 201,
        ok: true,
        headers: new Headers({ ETag: `"${marker}"` }),
        json: async () => created,
      };
    }
    const itemId = url.replace('/v1/shopping-list/items/', '');
    if (method === 'PUT') {
      const body = JSON.parse(options.body);
      rows = rows.map((row) => (row.id === itemId ? { ...row, ...body } : row));
      marker += 1;
      return {
        status: 200,
        ok: true,
        headers: new Headers({ ETag: `"${marker}"` }),
        json: async () => ({ id: itemId, ...body }),
      };
    }
    if (method === 'DELETE') {
      rows = rows.filter((row) => row.id !== itemId);
      marker += 1;
      return { status: 204, ok: true, headers: new Headers({ ETag: `"${marker}"` }) };
    }
    if (method === 'PATCH') {
      const body = JSON.parse(options.body);
      rows = rows.map((row) => (row.id === itemId ? { ...row, checked: body.checked } : row));
      marker += 1;
      return {
        status: 200,
        ok: true,
        headers: new Headers({ ETag: `"${marker}"` }),
        json: async () => ({ id: itemId, checked: body.checked }),
      };
    }
    throw new Error(`unexpected ${method} ${url}`);
  });
}

async function settle() {
  await act(async () => {
    await vi.advanceTimersByTimeAsync(10); // well below one poll interval
  });
}

describe('useShoppingList reflects its own mutations without a reload', () => {
  beforeEach(() => {
    vi.useFakeTimers();
  });

  afterEach(() => {
    vi.useRealTimers();
    vi.restoreAllMocks();
  });

  it('an added item appears in the rendered list (E4)', async () => {
    globalThis.fetch = fakeShoppingServer([item('i-1')]);
    const { result } = renderHook(() => useShoppingList());
    await settle();

    act(() => result.current.openAdd());
    act(() => result.current.updateDraftField('name', 'lentejas'));
    act(() => result.current.updateDraftField('quantity', '300'));
    act(() => result.current.updateDraftField('unit', 'g'));
    await act(async () => result.current.saveItem());
    await settle();

    expect(result.current.uncheckedItems.map((row) => row.name)).toEqual(['Item i-1', 'lentejas']);
    expect(result.current.error).toBeNull();
  });

  it('an edited quantity is shown on the item (E5)', async () => {
    globalThis.fetch = fakeShoppingServer([item('i-1')]);
    const { result } = renderHook(() => useShoppingList());
    await settle();

    act(() => result.current.openEdit(item('i-1')));
    act(() => result.current.updateDraftField('quantity', '500'));
    await act(async () => result.current.saveItem());
    await settle();

    expect(result.current.uncheckedItems.map((row) => row.quantity)).toEqual([500]);
  });

  it('checking an item moves it to the checked section (E6)', async () => {
    globalThis.fetch = fakeShoppingServer([item('i-1')]);
    const { result } = renderHook(() => useShoppingList());
    await settle();

    await act(async () => result.current.setChecked(item('i-1'), true));
    await settle();

    expect(result.current.uncheckedItems).toEqual([]);
    expect(result.current.checkedItems.map((row) => row.id)).toEqual(['i-1']);
  });

  it('a confirmed remove drops the item from the rendered list (E7)', async () => {
    globalThis.fetch = fakeShoppingServer([item('i-1'), item('i-2')]);
    const { result } = renderHook(() => useShoppingList());
    await settle();
    expect(result.current.uncheckedItems.map((row) => row.id)).toEqual(['i-1', 'i-2']);

    act(() => result.current.remove('i-1'));
    await act(async () => result.current.confirm.confirm());
    await settle();

    expect(result.current.uncheckedItems.map((row) => row.id)).toEqual(['i-2']);
    expect(result.current.error).toBeNull();
  });

  it('a re-sync shows the ingredients it added (E8)', async () => {
    globalThis.fetch = fakeShoppingServer([item('i-1')]);
    const { result } = renderHook(() => useShoppingList());
    await settle();

    await act(async () => result.current.resync());
    await settle();

    expect(result.current.uncheckedItems.map((row) => row.id)).toEqual(['i-1', 'auto-1']);
  });
});
