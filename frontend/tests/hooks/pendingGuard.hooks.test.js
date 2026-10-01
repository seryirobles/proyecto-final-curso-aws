// @vitest-environment jsdom
// R31, R32: two rapid calls to a guarded action issue one request, and the
// owning hook exposes `pending` for it.
import { act, renderHook, waitFor } from '@testing-library/react';
import { afterEach, describe, expect, it, vi } from 'vitest';

vi.mock('../../src/api/client.js', async (importOriginal) => {
  const actual = await importOriginal();
  return { ...actual, apiFetch: vi.fn() };
});
vi.mock('../../src/hooks/usePolling.js', () => ({ usePolling: vi.fn() }));

import { apiFetch } from '../../src/api/client.js';
import { usePolling } from '../../src/hooks/usePolling.js';
import { useWeekPlanner } from '../../src/hooks/useWeekPlanner.js';
import { useLibrary } from '../../src/hooks/useLibrary.js';
import { useShoppingList } from '../../src/hooks/useShoppingList.js';
import { useRules } from '../../src/hooks/useRules.js';
import { useAdminAccounts } from '../../src/hooks/useAdminAccounts.js';
import { useRecipeAuthoring } from '../../src/hooks/useRecipeAuthoring.js';

const LIVE_WEEKS = {
  today: '2026-08-17',
  current: { weekId: '2026-W34', monday: '2026-08-17', sunday: '2026-08-23' },
  next: { weekId: '2026-W35', monday: '2026-08-24', sunday: '2026-08-30' },
};

function poll(data) {
  return {
    data,
    marker: 1,
    connectionLost: false,
    applyMutationMarker: vi.fn(),
    refetchNow: vi.fn(),
  };
}

// Reads resolve; mutations (calls with a method) hang so the second tap sees
// the first still in flight.
function mockApi() {
  apiFetch.mockImplementation((url, options) => {
    if (options?.method) return new Promise(() => {});
    if (url === '/v1/live-weeks') return Promise.resolve(LIVE_WEEKS);
    if (url === '/v1/users') return Promise.resolve({ users: [] });
    return Promise.resolve({});
  });
}

function mutationCalls() {
  return apiFetch.mock.calls.filter(([, options]) => options?.method);
}

afterEach(() => {
  vi.restoreAllMocks();
  vi.clearAllMocks();
});

describe('guarded mutations send one request on a double tap', () => {
  it('useWeekPlanner.submitCandidate (R32)', async () => {
    mockApi();
    usePolling.mockReturnValue(poll({ weekId: '2026-W34', slots: [] }));
    const { result } = renderHook(() => useWeekPlanner());
    await waitFor(() => expect(result.current.liveWeeks).not.toBeNull());
    act(() => result.current.openCandidateAuthoring(1, 1));

    await act(async () => {
      result.current.submitCandidate({ source: 'library', recipeId: 'r-1' });
      result.current.submitCandidate({ source: 'library', recipeId: 'r-1' });
    });

    expect(mutationCalls()).toHaveLength(1);
    expect(result.current.pending.has('submitCandidate')).toBe(true);
  });

  it('useLibrary: a library-method authoring submit (R32)', async () => {
    mockApi();
    usePolling.mockReturnValue(poll({ recipes: [] }));
    const { result } = renderHook(() => useLibrary());
    act(() => result.current.openAdd());
    act(() => result.current.authoring.selectLibraryRecipe('r-1'));
    act(() => result.current.authoring.setMethod('library'));

    await act(async () => {
      result.current.authoring.submit();
      result.current.authoring.submit();
    });

    expect(mutationCalls()).toHaveLength(1);
    expect(result.current.pending).toBeInstanceOf(Set);
  });

  it('useShoppingList.saveItem and resync (R32)', async () => {
    mockApi();
    usePolling.mockReturnValue(poll({ items: [] }));
    const { result } = renderHook(() => useShoppingList());
    act(() => result.current.openAdd());
    act(() => result.current.updateDraftField('name', 'arroz'));
    act(() => result.current.updateDraftField('quantity', '2'));
    act(() => result.current.updateDraftField('unit', 'g'));

    await act(async () => {
      result.current.saveItem();
      result.current.saveItem();
      result.current.resync();
      result.current.resync();
    });

    expect(mutationCalls()).toHaveLength(2);
    expect(result.current.pending.has('saveItem')).toBe(true);
    expect(result.current.pending.has('resync')).toBe(true);
  });

  it('useRules.saveCategoryCount (R32)', async () => {
    mockApi();
    usePolling.mockReturnValue(
      poll({
        rules: [],
        availableOptions: {
          maxCountByCategory: { meat: 3 },
          daysAvailableForPin: [],
          daysAvailableToDisable: [],
        },
      }),
    );
    const { result } = renderHook(() => useRules());
    act(() => result.current.setCategoryCountCategory('meat'));
    act(() => result.current.setCategoryCountCount('2'));

    await act(async () => {
      result.current.saveCategoryCount();
      result.current.saveCategoryCount();
    });

    expect(mutationCalls()).toHaveLength(1);
    expect(result.current.pending.has('saveCategoryCount')).toBe(true);
  });

  it('useAdminAccounts.create (R32)', async () => {
    mockApi();
    const { result } = renderHook(() => useAdminAccounts());
    await waitFor(() => expect(result.current.isLoading).toBe(false));
    act(() => result.current.setNewUsername('nuevo'));
    act(() => result.current.setNewTemporaryPassword('temporal123'));

    await act(async () => {
      result.current.create();
      result.current.create();
    });

    expect(mutationCalls()).toHaveLength(1);
    expect(result.current.pending.has('create')).toBe(true);
  });

  it('useRecipeAuthoring.submit (R32)', async () => {
    const onSubmit = vi.fn(() => new Promise(() => {}));
    usePolling.mockReturnValue(poll({ recipes: [] }));
    const { result } = renderHook(() => useRecipeAuthoring({ mode: 'library', onSubmit }));
    act(() => result.current.selectLibraryRecipe('r-1'));
    act(() => result.current.setMethod('library'));

    await act(async () => {
      result.current.submit();
      result.current.submit();
    });

    expect(onSubmit).toHaveBeenCalledTimes(1);
    expect(result.current.pending.has('submit')).toBe(true);
  });
});
