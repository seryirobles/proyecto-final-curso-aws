// @vitest-environment jsdom
// T37 (R18, R19, R20, R21): usePolling wiring, add/edit/check/remove/resync,
// no auto-retry on a 409 SHOPPING_LIST_LOCK_HELD.
import { act, renderHook, waitFor } from '@testing-library/react';
import { afterEach, describe, expect, it, vi } from 'vitest';

vi.mock('../../src/api/client.js', async (importOriginal) => {
  const actual = await importOriginal();
  return { ...actual, apiFetch: vi.fn() };
});
vi.mock('../../src/hooks/usePolling.js', () => ({ usePolling: vi.fn() }));

import { apiFetch, ApiError } from '../../src/api/client.js';
import { usePolling } from '../../src/hooks/usePolling.js';
import { useShoppingList } from '../../src/hooks/useShoppingList.js';

const LIVE_WEEKS = {
  today: '2026-08-17',
  current: { weekId: '2026-W34', monday: '2026-08-17', sunday: '2026-08-23' },
  next: { weekId: '2026-W35', monday: '2026-08-24', sunday: '2026-08-30' },
};

function item(id, overrides = {}) {
  return { id, name: 'arroz', quantity: 500, unit: 'g', checked: false, ...overrides };
}

function pollSnapshot(items) {
  return {
    data: { items },
    connectionLost: false,
    applyMutationMarker: vi.fn(),
    refetchNow: vi.fn(), // issue ui-not-reflecting-mutations
  };
}

describe('useShoppingList', () => {
  afterEach(() => {
    vi.restoreAllMocks();
    vi.clearAllMocks();
    vi.useRealTimers();
  });

  it('splits items into unchecked and checked sections (FR-SHOP-08)', () => {
    usePolling.mockReturnValue(pollSnapshot([item('s-1'), item('s-2', { checked: true })]));
    apiFetch.mockResolvedValue(LIVE_WEEKS);
    const { result } = renderHook(() => useShoppingList());

    expect(result.current.uncheckedItems.map((i) => i.id)).toEqual(['s-1']);
    expect(result.current.checkedItems.map((i) => i.id)).toEqual(['s-2']);
  });

  it('zero items sets the empty-state flag (R19)', () => {
    usePolling.mockReturnValue(pollSnapshot([]));
    apiFetch.mockResolvedValue(LIVE_WEEKS);
    const { result } = renderHook(() => useShoppingList());

    expect(result.current.uncheckedItems).toHaveLength(0);
    expect(result.current.checkedItems).toHaveLength(0);
  });

  it('polls before the first data arrives (R20)', () => {
    usePolling.mockReturnValue({
      data: null,
      connectionLost: false,
      applyMutationMarker: vi.fn(),
      refetchNow: vi.fn(), // issue ui-not-reflecting-mutations
    });
    apiFetch.mockResolvedValue(LIVE_WEEKS);
    const { result } = renderHook(() => useShoppingList());

    expect(result.current.isLoading).toBe(true);
  });

  it('fetches live-weeks once, for the resync button scope label (R21)', async () => {
    usePolling.mockReturnValue(pollSnapshot([]));
    apiFetch.mockResolvedValue(LIVE_WEEKS);

    const { result } = renderHook(() => useShoppingList());

    await waitFor(() => expect(result.current.liveWeeks).toEqual(LIVE_WEEKS));
  });

  it('a failed live-weeks fetch only hides the scope label, never the hook error (design decision 3)', async () => {
    usePolling.mockReturnValue(pollSnapshot([item('s-1')]));
    apiFetch.mockImplementation((url) =>
      url === '/v1/live-weeks' ? Promise.reject(new Error('network down')) : Promise.resolve(null),
    );
    const { result } = renderHook(() => useShoppingList());

    // Flush the rejected promise's microtask queue via a real macrotask tick.
    await act(async () => new Promise((resolve) => globalThis.setTimeout(resolve, 0)));

    expect(result.current.liveWeeks).toBeNull();
    expect(result.current.error).toBeNull();
    // The list itself still functions - unaffected by the decorative label's failure.
    expect(result.current.uncheckedItems.map((i) => i.id)).toEqual(['s-1']);
    await act(async () => result.current.resync());
    expect(apiFetch).toHaveBeenCalledWith(
      '/v1/shopping-list/resync',
      expect.objectContaining({ method: 'POST' }),
    );
  });

  it('openEdit pre-fills the draft from the item being edited (F4 lesson)', () => {
    usePolling.mockReturnValue(pollSnapshot([item('s-1', { name: 'lentejas', quantity: 300 })]));
    apiFetch.mockResolvedValue(LIVE_WEEKS);
    const { result } = renderHook(() => useShoppingList());

    act(() => result.current.openEdit(item('s-1', { name: 'lentejas', quantity: 300 })));

    expect(result.current.draft).toEqual({ name: 'lentejas', quantity: '300', unit: 'g' });
    expect(result.current.isEditing).toBe(true);
  });

  it('openAdd starts from an empty draft', () => {
    usePolling.mockReturnValue(pollSnapshot([]));
    apiFetch.mockResolvedValue(LIVE_WEEKS);
    const { result } = renderHook(() => useShoppingList());

    act(() => result.current.openAdd());

    expect(result.current.draft).toEqual({ name: '', quantity: '', unit: '' });
    expect(result.current.isEditing).toBe(false);
  });

  it('saveItem posts to the items collection on add', async () => {
    usePolling.mockReturnValue(pollSnapshot([]));
    apiFetch.mockImplementation((url) =>
      url === '/v1/live-weeks' ? Promise.resolve(LIVE_WEEKS) : Promise.resolve(null),
    );
    const { result } = renderHook(() => useShoppingList());
    act(() => result.current.openAdd());
    act(() => result.current.updateDraftField('name', 'arroz'));
    act(() => result.current.updateDraftField('quantity', '500'));
    act(() => result.current.updateDraftField('unit', 'g'));

    await act(async () => result.current.saveItem());

    expect(apiFetch).toHaveBeenCalledWith(
      '/v1/shopping-list/items',
      expect.objectContaining({
        method: 'POST',
        body: { name: 'arroz', quantity: 500, unit: 'g' },
      }),
    );
  });

  it('saveItem puts to the item id on edit', async () => {
    const fixture = item('s-1', { name: 'arroz', quantity: 500, unit: 'g' });
    usePolling.mockReturnValue(pollSnapshot([fixture]));
    apiFetch.mockImplementation((url) =>
      url === '/v1/live-weeks' ? Promise.resolve(LIVE_WEEKS) : Promise.resolve(null),
    );
    const { result } = renderHook(() => useShoppingList());
    act(() => result.current.openEdit(fixture));

    await act(async () => result.current.saveItem());

    // Body must carry the real edited values, not a hardcoded stand-in (M1).
    expect(apiFetch).toHaveBeenCalledWith(
      '/v1/shopping-list/items/s-1',
      expect.objectContaining({
        method: 'PUT',
        body: { name: 'arroz', quantity: 500, unit: 'g' },
      }),
    );
  });

  it('setChecked patches the checked field', async () => {
    usePolling.mockReturnValue(pollSnapshot([item('s-1')]));
    apiFetch.mockImplementation((url) =>
      url === '/v1/live-weeks' ? Promise.resolve(LIVE_WEEKS) : Promise.resolve(null),
    );
    const { result } = renderHook(() => useShoppingList());

    await act(async () => result.current.setChecked(item('s-1'), true));

    expect(apiFetch).toHaveBeenCalledWith(
      '/v1/shopping-list/items/s-1',
      expect.objectContaining({ method: 'PATCH', body: { checked: true } }),
    );
  });

  it('remove routes through useConfirm before calling apiFetch (R18)', async () => {
    usePolling.mockReturnValue(pollSnapshot([item('s-1')]));
    apiFetch.mockImplementation((url) =>
      url === '/v1/live-weeks' ? Promise.resolve(LIVE_WEEKS) : Promise.resolve(null),
    );
    const { result } = renderHook(() => useShoppingList());
    await waitFor(() => expect(result.current.liveWeeks).not.toBeNull());
    apiFetch.mockClear();

    act(() => result.current.remove('s-1'));

    expect(result.current.confirm.pending).not.toBeNull();
    expect(apiFetch).not.toHaveBeenCalled();

    await act(async () => result.current.confirm.confirm());

    expect(apiFetch).toHaveBeenCalledWith(
      '/v1/shopping-list/items/s-1',
      expect.objectContaining({ method: 'DELETE' }),
    );
  });

  it('resync sets isResyncing while in flight (R20)', async () => {
    usePolling.mockReturnValue(pollSnapshot([]));
    let resolveResync;
    apiFetch.mockImplementation((url) => {
      if (url === '/v1/live-weeks') return Promise.resolve(LIVE_WEEKS);
      return new Promise((resolve) => (resolveResync = resolve));
    });
    const { result } = renderHook(() => useShoppingList());

    let resyncPromise;
    act(() => {
      resyncPromise = result.current.resync();
    });

    expect(result.current.isResyncing).toBe(true);

    await act(async () => {
      resolveResync(null);
      await resyncPromise;
    });

    expect(result.current.isResyncing).toBe(false);
  });

  it('active: false reaches usePolling as enabled: false (App shell finding 1)', () => {
    usePolling.mockReturnValue(pollSnapshot([]));
    apiFetch.mockResolvedValue(LIVE_WEEKS);

    renderHook(() => useShoppingList({ active: false }));

    expect(usePolling).toHaveBeenCalledWith('/v1/shopping-list', undefined, { enabled: false });
  });

  it('a 409 SHOPPING_LIST_LOCK_HELD sets error, resets isResyncing, and does not auto-retry over time (M3, M4)', async () => {
    vi.useFakeTimers();
    usePolling.mockReturnValue(pollSnapshot([]));
    apiFetch.mockImplementation((url) => {
      if (url === '/v1/live-weeks') return Promise.resolve(LIVE_WEEKS);
      return Promise.reject(
        new ApiError({
          status: 409,
          code: 'SHOPPING_LIST_LOCK_HELD',
          detail: 'Otra persona está resincronizando la lista. Inténtalo de nuevo.',
        }),
      );
    });
    const { result } = renderHook(() => useShoppingList());

    await act(async () => result.current.resync());

    expect(result.current.error).toBe(
      'Otra persona está resincronizando la lista. Inténtalo de nuevo.',
    );
    // The retry button must become clickable again after a lock-held error (M4).
    expect(result.current.isResyncing).toBe(false);

    // No deferred retry either (M3) - advance real time, not just the sync tick.
    await act(async () => vi.advanceTimersByTimeAsync(60_000));

    expect(
      apiFetch.mock.calls.filter((call) => call[0] === '/v1/shopping-list/resync'),
    ).toHaveLength(1);
  });
});
